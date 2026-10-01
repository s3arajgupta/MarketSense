"""
MarketSense — Ollama Local Provider

Uses the Ollama Python client for fully offline, privacy-preserving inference.
Secondary/fallback provider — requires Ollama installed and a model pulled.
"""
import httpx
from intelligence.llm_client import LLMClient, LLMResponse


class OllamaClient(LLMClient):
    """Ollama local inference provider."""

    def __init__(self):
        from config import OLLAMA_MODEL, OLLAMA_HOST
        self._model = OLLAMA_MODEL
        self._host = OLLAMA_HOST
        self._client = None

    def _get_client(self):
        """Lazy-initialize the Ollama client."""
        if self._client is None:
            import ollama
            self._client = ollama.Client(host=self._host)
        return self._client

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a response using local Ollama model."""
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = client.chat(
            model=self._model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )

        # Extract token counts
        input_tokens = response.get("prompt_eval_count", 0)
        output_tokens = response.get("eval_count", 0)

        return LLMResponse(
            text=response["message"]["content"],
            model=self._model,
            provider="ollama",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def generate_stream(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """Stream chunks of text from local Ollama model."""
        client = self._get_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = client.chat(
            model=self._model,
            messages=messages,
            stream=True,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )
        for chunk in response:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

    def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            response = httpx.get(f"{self._host}/api/tags", timeout=3.0)
            if response.status_code != 200:
                return False
            models = response.json().get("models", [])
            # Check if our configured model (base name) is available
            model_base = self._model.split(":")[0]
            return any(model_base in m.get("name", "") for m in models)
        except (httpx.ConnectError, httpx.TimeoutException, Exception):
            return False

    @property
    def provider_name(self) -> str:
        return f"Ollama ({self._model})"
