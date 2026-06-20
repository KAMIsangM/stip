"""Tencent ASR provider — fallback ASR via Tencent Cloud ASR API.

Uses Tencent Cloud ASR (一句话识别) RESTful API for non-streaming
audio file recognition.

Config keys (from config.yaml → asr.tencent):
    secret_id, secret_key, app_id
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone

import aiohttp

from app.core.config import get_settings
from app.provider.asr.base_asr_provider import BaseASRProvider

logger = logging.getLogger(__name__)

_TENCENT_ASR_URL = "https://asr.tencentcloudapi.com"


class TencentASRProvider(BaseASRProvider):
    """File-based ASR via Tencent Cloud ASR (一句话识别)."""

    def __init__(self) -> None:
        cfg = get_settings()["asr"]["tencent"]
        self._secret_id = cfg.get("secret_id", "")
        self._secret_key = cfg.get("secret_key", "")
        self._app_id = cfg.get("app_id", "")

    async def stream_recognize(
        self, audio_stream: Generator[bytes, None, None], config: dict
    ) -> AsyncGenerator[str, None]:
        if not self._secret_id or not self._secret_key:
            logger.warning("[tencent-asr] Credentials not configured, skipping")
            return

        chunks: list[bytes] = []
        for chunk in audio_stream:
            if chunk:
                chunks.append(chunk)
        if not chunks:
            return

        audio_data = b"".join(chunks)
        language = config.get("language", "zh-CN")

        try:
            result = await self._recognize(audio_data, language)
            if result:
                yield result
        except Exception as exc:
            logger.exception("[tencent-asr] Recognition failed")
            raise

    async def _recognize(self, audio_data: bytes, language: str) -> str | None:
        import base64

        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        payload = json.dumps({
            "EngineModelType": "16k_zh" if language.startswith("zh") else "16k_en",
            "VoiceFormat": "mp3",
            "Data": audio_b64,
            "DataLen": len(audio_data),
        })

        timestamp = int(time.time())
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

        # TC3-HMAC-SHA256 signing
        service = "asr"
        host = "asr.tencentcloudapi.com"
        action = "SentenceRecognition"
        version = "2019-06-14"
        algorithm = "TC3-HMAC-SHA256"
        content_type = "application/json; charset=utf-8"

        # Step 1: canonical request
        canonical_headers = f"content-type:{content_type}\nhost:{host}\n"
        signed_headers = "content-type;host"
        hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            f"POST\n/\n\n{canonical_headers}\n{signed_headers}\n{hashed_payload}"
        )

        # Step 2: string to sign
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical}"

        # Step 3: signature
        def _sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _sign(f"TC3{self._secret_key}".encode("utf-8"), date)
        secret_service = _sign(secret_date, service)
        secret_signing = _sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # Step 4: authorization header
        authorization = (
            f"{algorithm} "
            f"Credential={self._secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": content_type,
            "Host": host,
            "X-TC-Action": action,
            "X-TC-Version": version,
            "X-TC-Timestamp": str(timestamp),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    _TENCENT_ASR_URL, headers=headers, data=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error("[tencent-asr] API error %d: %s", resp.status, text)
                        return None
                    result = await resp.json()
                    return self._parse_result(result)
        except aiohttp.ClientError as exc:
            logger.error("[tencent-asr] HTTP request failed: %s", exc)
            return None

    def _parse_result(self, result: dict) -> str | None:
        """Extract text from Tencent ASR response."""
        resp_data = result.get("Response", {})
        error = resp_data.get("Error")
        if error:
            logger.warning("[tencent-asr] API error: %s", error.get("Message", ""))
            return None
        text = resp_data.get("Result", "")
        return text.strip() if text else None
