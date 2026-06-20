"""Aliyun ASR provider — file-based recognition via REST API.

Uses Aliyun Intelligent Speech Interaction (NLS) RESTful API for
non-streaming audio file recognition. Supports PCM/WAV/MP3 formats.

Config keys (from config.yaml → asr.aliyun):
    access_key_id, access_key_secret, app_key, region

Token 获取方式：调用 CreateToken API 获取临时 token（有效期 1 天）。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator, Generator
from urllib.parse import quote, urlencode

import aiohttp

from app.core.config import get_settings
from app.provider.asr.base_asr_provider import BaseASRProvider

logger = logging.getLogger(__name__)

# Aliyun NLS REST endpoint for file recognition
_REST_URL = "https://nls-gateway.cn-shanghai.aliyuncs.com/asr/file/recognize"


class AliyunASRProvider(BaseASRProvider):
    """File-based ASR via Aliyun NLS REST API.

    NOTE: This provider implements the BaseASRProvider.stream_recognize
    interface, but because the Aliyun REST API is request-response (not
    streaming), it accumulates all audio chunks, sends one HTTP request,
    and yields a single result.
    """

    def __init__(self) -> None:
        cfg = get_settings()["asr"]["aliyun"]
        self._access_key_id = cfg.get("access_key_id", "")
        self._access_key_secret = cfg.get("access_key_secret", "")
        self._app_key = cfg.get("app_key", "")
        self._region = cfg.get("region", "cn-shanghai")
        self._token: str | None = None
        self._token_expire: float = 0.0

    # ------------------------------------------------------------------
    # BaseASRProvider interface
    # ------------------------------------------------------------------

    async def stream_recognize(
        self, audio_stream: Generator[bytes, None, None], config: dict
    ) -> AsyncGenerator[str, None]:
        """Accumulate audio chunks and send one REST request for recognition.

        Yields the final recognition text.
        """
        if not self._access_key_id or not self._access_key_secret:
            logger.warning("[aliyun-asr] Credentials not configured, skipping")
            return

        # Collect all audio data
        chunks: list[bytes] = []
        for chunk in audio_stream:
            if chunk:
                chunks.append(chunk)
        if not chunks:
            return

        audio_data = b"".join(chunks)
        language = config.get("language", "zh-CN")

        try:
            result = await self._recognize_rest(audio_data, language)
            if result:
                yield result
        except Exception as exc:
            logger.exception("[aliyun-asr] Recognition failed")
            raise

    # ------------------------------------------------------------------
    # Aliyun NLS REST API helpers
    # ------------------------------------------------------------------

    async def _ensure_token(self) -> str:
        """Get a valid token, refreshing if expired (TTL ≈ 1 day)."""
        now = time.time()
        if self._token and now < self._token_expire:
            return self._token

        # Build CreateToken request with proper signature
        base_url = "https://nls-meta.cn-shanghai.aliyuncs.com/token"
        params = {
            "AccessKeyId": self._access_key_id,
            "Action": "CreateToken",
            "Version": "2019-02-28",
            "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "Format": "JSON",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": uuid.uuid4().hex,
        }

        # Build canonical string for signing
        sorted_keys = sorted(params.keys())
        canonical_params = "&".join(
            f"{quote(k, safe='')}={quote(str(v), safe='')}" for k, v in sorted_keys
        )
        string_to_sign = (
            f"GET&{quote('/token', safe='')}&{quote(canonical_params, safe='')}"
        )
        signature = base64.b64encode(
            hmac.new(
                (self._access_key_secret + "&").encode("utf-8"),
                string_to_sign.encode("utf-8"),
                hashlib.sha1,
            ).digest()
        ).decode("utf-8")
        params["Signature"] = signature

        async with aiohttp.ClientSession() as session:
            async with session.get(
                base_url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"CreateToken failed {resp.status}: {text}")
                data = await resp.json()
                self._token = data["Token"]["Id"]
                # Token valid for ~24 hours; refresh 1 hour before expiry
                self._token_expire = now + 23 * 3600

        logger.info("[aliyun-asr] Token refreshed, expires in 23h")
        return self._token

    async def _recognize_rest(
        self, audio_data: bytes, language: str = "zh-CN"
    ) -> str | None:
        """Send audio to Aliyun NLS REST API and return recognized text."""
        token = await self._ensure_token()

        headers = {
            "X-NLS-Token": token,
            "Content-Type": "application/octet-stream",
            "Accept": "application/json",
        }
        params = {
            "appkey": self._app_key,
            "format": "mp3",
            "sample_rate": "16000",
            "enable_intermediate_result": "false",
            "enable_punctuation_prediction": "true",
            "enable_inverse_text_normalization": "true",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    _REST_URL,
                    headers=headers,
                    params=params,
                    data=audio_data,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.error(
                            "[aliyun-asr] API error %d: %s", resp.status, text
                        )
                        return None
                    result = await resp.json()
                    return self._parse_result(result)
        except aiohttp.ClientError as exc:
            logger.error("[aliyun-asr] HTTP request failed: %s", exc)
            return None

    def _parse_result(self, result: dict) -> str | None:
        """Extract recognized text from Aliyun NLS REST response.

        Expected response format:
        {"status": 20000000, "result": "识别文本"}
        """
        status = result.get("status", -1)
        if status != 20000000:
            logger.warning(
                "[aliyun-asr] Recognition returned status %s: %s",
                status,
                result.get("message", ""),
            )
            return None
        text = result.get("result", "")
        return text.strip() if text else None
