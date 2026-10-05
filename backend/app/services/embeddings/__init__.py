from app.services.embeddings.openai import OpenAIEmbeddingProvider
from app.services.embeddings.provider import EmbeddingProvider

# Singleton provider
embedding_service: EmbeddingProvider = OpenAIEmbeddingProvider()
