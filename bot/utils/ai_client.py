import aiohttp
import asyncio
from bot.config import DEEPSEEK_API_KEY

API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"
TIMEOUT = 30
MAX_RETRIES = 1

SYSTEM_PROMPT = (
    "You are Vexa AI, a helpful, friendly, and knowledgeable assistant. "
    "You never mention that you are DeepSeek or any other AI provider. "
    "You respond in Persian (فارسی) unless the user asks otherwise. "
    "Keep answers concise but helpful."
)


class AIClient:
    def __init__(self):
        self._api_key = DEEPSEEK_API_KEY

    async def chat(self, messages: list) -> str | None:
        if not self._api_key:
            return None

        system_msg = {"role": "system", "content": SYSTEM_PROMPT}
        payload = {
            "model": MODEL,
            "messages": [system_msg] + messages,
            "max_tokens": 1000,
            "temperature": 0.7,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(1 + MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        API_URL, json=payload, headers=headers, timeout=TIMEOUT
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data["choices"][0]["message"]["content"]
                        if resp.status == 429:
                            if attempt < MAX_RETRIES:
                                await asyncio.sleep(2)
                                continue
                            return None
                        if resp.status == 401:
                            return None
                        return None
            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1)
                    continue
                return None
            except Exception:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1)
                    continue
                return None
        return None
