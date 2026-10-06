from openai import AsyncOpenAI
from app.core.config import settings
from app.services.llm.provider import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self._key = None
        self._client = None
        self._model = None

    def _get_client_and_model(self):
        key = settings.OPENAI_API_KEY or settings.GROK_API_KEY or settings.GROQ_API_KEY or "dummy-key-not-set"
        if self._client is None or self._key != key:
            self._key = key
            if key.startswith("gsk_") or (settings.GROQ_API_KEY and not settings.OPENAI_API_KEY):
                # Groq API (console.groq.com)
                self._client = AsyncOpenAI(
                    api_key=key,
                    base_url=settings.GROQ_BASE_URL
                )
                self._model = settings.GROQ_MODEL
            elif key.startswith("xai-") or (settings.GROK_API_KEY and not settings.OPENAI_API_KEY and not key.startswith("gsk_")):
                # xAI Grok API (api.x.ai)
                self._client = AsyncOpenAI(
                    api_key=key,
                    base_url=settings.GROK_BASE_URL
                )
                self._model = settings.GROK_MODEL
            else:
                # OpenAI API
                self._client = AsyncOpenAI(
                    api_key=key
                )
                self._model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        return self._client, self._model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        client, model = self._get_client_and_model()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0, # Keep it deterministic for RAG
        )
        return response.choices[0].message.content
