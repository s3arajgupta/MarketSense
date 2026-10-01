"""
MarketSense — Abstract LLM Client Interface & Factory

Provides a clean abstraction over LLM providers (Gemini API, Ollama).
All downstream code (mentor, RAG, prompts) depends only on this interface,
never on a specific provider.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    text: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMClient(ABC):
    """
    Abstract LLM provider interface.

    Implementations must provide:
    - generate(): Send a prompt, get a response
    - is_available(): Check if the provider is ready
    """

    @abstractmethod
    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """
        Generate a response given a user prompt and optional system context.

        Args:
            user_prompt: The main prompt/question.
            system_prompt: System-level instructions (persona, rules, context).
            temperature: Creativity control (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum tokens in the response.

        Returns:
            LLMResponse with generated text and metadata.
        """
        ...

    @abstractmethod
    def generate_stream(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Stream text chunks from the LLM.

        Yields:
            str: Successive text chunks as they arrive.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is ready (API key set, service running, etc.)."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name for UI display."""
        ...


def create_llm_client(provider: str | None = None) -> LLMClient:
    """
    Factory function — creates the appropriate LLM client based on config.

    Args:
        provider: Override provider name. If None, reads from config.

    Returns:
        Configured LLMClient instance.

    Raises:
        ValueError: If the provider is unknown.
        ConnectionError: If the provider is not available.
    """
    if provider is None:
        from config import LLM_PROVIDER
        provider = LLM_PROVIDER

    provider = provider.lower().strip()

    if provider == "gemini":
        from intelligence.gemini_provider import GeminiClient
        client = GeminiClient()
    elif provider == "ollama":
        from intelligence.ollama_provider import OllamaClient
        client = OllamaClient()
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Supported providers: 'gemini', 'ollama'"
        )

    if not client.is_available():
        raise ConnectionError(
            f"LLM provider '{provider}' is not available. "
            f"Check your configuration in .env"
        )

    return client
