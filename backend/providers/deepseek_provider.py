from .base import BaseLLMProvider
import httpx

class DeepSeekProvider(BaseLLMProvider):
    def get_name(self):
        return "deepseek"

    async def generate(self, messages, tools=None, **kwargs):
        # Example DeepSeek API call (replace with real endpoint/params)
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools or [],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
