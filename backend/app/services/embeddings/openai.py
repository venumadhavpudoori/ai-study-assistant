import logging
import hashlib
import math
from typing import List
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.embeddings.provider import EmbeddingProvider

logger = logging.getLogger(__name__)

class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self):
        self.api_key = settings.GROK_API_KEY or settings.OPENAI_API_KEY or "dummy-key-not-set"
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=settings.EMBEDDING_MODEL_NAME
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.warning(f"Remote embedding endpoint failed ({e}); falling back to local deterministic embeddings.")
            dim = 1536
            results = []
            for text in texts:
                h = hashlib.sha512(text.encode("utf-8")).digest()
                vec = []
                for i in range(dim):
                    byte_val = h[i % len(h)]
                    vec.append((byte_val / 127.5) - 1.0)
                norm = math.sqrt(sum(x * x for x in vec)) or 1.0
                results.append([x / norm for x in vec])
            return results

    @property
    def model_name(self) -> str:
        return settings.EMBEDDING_MODEL_NAME
