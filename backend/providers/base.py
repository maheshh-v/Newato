# Base class for all LLM providers
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def generate(self, messages, tools=None, **kwargs):
        """Generate a response from the LLM."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the provider name (e.g., 'anthropic', 'groq', 'deepseek')."""
        pass
