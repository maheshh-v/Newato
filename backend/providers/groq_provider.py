from .base import BaseLLMProvider
import groq

class GroqProvider(BaseLLMProvider):
    def get_name(self):
        return "groq"

    async def generate(self, messages, tools=None, **kwargs):
        client = groq.AsyncGroq(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools or [],
            tool_choice="auto",
        )
        return response
