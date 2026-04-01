from .base import BaseLLMProvider
import anthropic

class AnthropicProvider(BaseLLMProvider):
    def get_name(self):
        return "anthropic"

    async def generate(self, messages, tools=None, **kwargs):
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        response = await client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=kwargs.get("system", ""),
            tools=tools or [],
            messages=messages,
        )
        return response
