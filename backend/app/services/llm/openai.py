from openai import AsyncOpenAI
from app.core.config import settings
from app.services.llm.provider import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self):
        key = settings.GROK_API_KEY or settings.GROQ_API_KEY or settings.OPENAI_API_KEY or "dummy-key-not-set"

        if key.startswith("gsk_") or settings.GROQ_API_KEY:
            # Groq API (console.groq.com)
            self.client = AsyncOpenAI(
                api_key=key,
                base_url=settings.GROQ_BASE_URL
            )
            self.model = settings.GROQ_MODEL
        elif key.startswith("xai-") or (settings.GROK_API_KEY and not key.startswith("gsk_")):
            # xAI Grok API (api.x.ai)
            self.client = AsyncOpenAI(
                api_key=key,
                base_url=settings.GROK_BASE_URL
            )
            self.model = settings.GROK_MODEL
        else:
            # OpenAI API
            self.client = AsyncOpenAI(
                api_key=key
            )
            self.model = "gpt-4o"

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0, # Keep it deterministic for RAG
        )
        return response.choices[0].message.content
