from .anthropic_provider import AnthropicProvider
from .groq_provider import GroqProvider
from .deepseek_provider import DeepSeekProvider

PROVIDER_REGISTRY = {
    "anthropic": AnthropicProvider,
    "groq": GroqProvider,
    "deepseek": DeepSeekProvider,
    # Add more providers here
}
