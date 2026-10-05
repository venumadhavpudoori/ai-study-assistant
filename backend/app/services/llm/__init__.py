from app.services.llm.openai import OpenAIProvider
from app.services.llm.provider import LLMProvider

# Singleton provider
llm_service: LLMProvider = OpenAIProvider()
