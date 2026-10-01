"""
MarketSense — Gemini API Provider

Uses the google-genai SDK to call Gemini models.
Default and recommended provider for portfolio project accessibility.
"""
from intelligence.llm_client import LLMClient, LLMResponse


class GeminiClient(LLMClient):
    """Gemini API provider via google-genai SDK."""

    def __init__(self):
        from config import GEMINI_API_KEY, GEMINI_MODEL
        self._api_key = GEMINI_API_KEY
        self._model = GEMINI_MODEL
        self._client = None

    def _get_client(self):
        """Lazy-initialize the Gemini client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def generate(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a response using Gemini API with retry and backoff on transient errors."""
        import time
        from google.genai import types

        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_prompt:
            config.system_instruction = system_prompt

        candidate_models = [self._model]
        # If the primary model encounters issues, define a fallback pool
        for fallback in ["gemini-3.5-flash-lite", "gemini-flash-latest"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_err = None
        for model_to_use in candidate_models:
            max_retries = 3
            backoff = 1.5
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model_to_use,
                        contents=user_prompt,
                        config=config,
                    )

                    # Extract token counts if available
                    input_tokens = 0
                    output_tokens = 0
                    if response.usage_metadata:
                        input_tokens = response.usage_metadata.prompt_token_count or 0
                        output_tokens = response.usage_metadata.candidates_token_count or 0

                    return LLMResponse(
                        text=response.text or "",
                        model=model_to_use,
                        provider="gemini",
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                    )
                except Exception as e:
                    last_err = e
                    err_str = str(e)
                    # Check for transient errors like 503 (UNAVAILABLE) or 429 (RESOURCE_EXHAUSTED)
                    if any(code in err_str for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]) and attempt < max_retries - 1:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    break  # If not retryable or max retries exceeded for this model, try next candidate model

        raise last_err

    def generate_stream(
        self,
        user_prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """Stream chunks of text from Gemini API with fallback support."""
        import time
        from google.genai import types

        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system_prompt:
            config.system_instruction = system_prompt

        candidate_models = [self._model]
        for fallback in ["gemini-3.5-flash-lite", "gemini-flash-latest"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_err = None
        for model_to_use in candidate_models:
            max_retries = 3
            backoff = 1.5
            for attempt in range(max_retries):
                try:
                    stream = client.models.generate_content_stream(
                        model=model_to_use,
                        contents=user_prompt,
                        config=config,
                    )
                    for chunk in stream:
                        if chunk.text:
                            yield chunk.text
                    return
                except Exception as e:
                    last_err = e
                    err_str = str(e)
                    if any(code in err_str for code in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]) and attempt < max_retries - 1:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    break

        raise last_err

    def is_available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self._api_key) and self._api_key != "your-api-key-here"

    @property
    def provider_name(self) -> str:
        return f"Gemini ({self._model})"
