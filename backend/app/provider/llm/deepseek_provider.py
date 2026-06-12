"""DeepSeek LLM provider — MVP primary (config llm.provider=deepseek)."""

import httpx

from app.core.config import get_settings
from app.provider.llm.base_llm_provider import BaseLLMProvider


class DeepSeekProvider(BaseLLMProvider):
    async def chat_completion(
        self, prompt: str, response_format: str = "text"
    ) -> str:
        cfg = get_settings()["llm"]["deepseek"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{cfg['base_url']}/chat/completions",
                headers={"Authorization": f"Bearer {cfg['api_key']}"},
                json={
                    "model": cfg["model"],
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
