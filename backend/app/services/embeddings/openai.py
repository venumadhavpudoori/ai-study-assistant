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
        self._key = None
        self._client = None

    def _get_client(self) -> AsyncOpenAI:
        current_key = settings.OPENAI_API_KEY or settings.GROK_API_KEY or "dummy-key-not-set"
        if self._client is None or self._key != current_key:
            self._key = current_key
            self._client = AsyncOpenAI(api_key=current_key)
        return self._client

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        client = self._get_client()
        try:
            response = await client.embeddings.create(
                input=texts,
                model=settings.EMBEDDING_MODEL_NAME
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.warning(f"Remote embedding endpoint failed ({e}); falling back to local deterministic embeddings.")
            dim = 1536
            stopwords = {
                'what', 'is', 'a', 'an', 'the', 'in', 'on', 'of', 'and', 'to', 'for', 'with', 
                'at', 'by', 'from', 'as', 'that', 'this', 'it', 'are', 'was', 'be', 'or', 'how'
            }
            import re
            results = []
            for text in texts:
                raw_words = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
                words = [w for w in raw_words if w not in stopwords] or raw_words
                vec = [0.0] * dim
                for w in words:
                    idx = int(hashlib.md5(w.encode('utf-8')).hexdigest()[:8], 16) % dim
                    vec[idx] += 1.0
                for i in range(len(words) - 1):
                    bigram = f"{words[i]}_{words[i+1]}"
                    idx = int(hashlib.md5(bigram.encode('utf-8')).hexdigest()[:8], 16) % dim
                    vec[idx] += 1.5
                norm = math.sqrt(sum(x * x for x in vec)) or 1.0
                results.append([x / norm for x in vec])
            return results

    @property
    def model_name(self) -> str:
        return settings.EMBEDDING_MODEL_NAME
