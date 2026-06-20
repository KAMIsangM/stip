"""DeepSeek LLM provider — MVP primary (config llm.provider=deepseek)."""

import logging

import httpx

from app.core.config import get_settings
from app.provider.llm.base_llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    async def chat_completion(
        self, prompt: str, response_format: str = "text", messages: list[dict] | None = None
    ) -> str:
        cfg = get_settings()["llm"]["deepseek"]
        base_url = cfg["base_url"]
        model = cfg["model"]
        api_key = cfg.get("api_key", "")
        logger.info(
            "DeepSeek API call: url=%s, model=%s, api_key_prefix=%s...",
            base_url, model, api_key[:12] if api_key else "(EMPTY)",
        )

        if messages is None:
            messages = [{"role": "user", "content": prompt}]

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": messages,
                },
            )
            logger.info("DeepSeek API response status: %d", resp.status_code)
            resp.raise_for_status()
            body = resp.json()
            return body["choices"][0]["message"]["content"]
