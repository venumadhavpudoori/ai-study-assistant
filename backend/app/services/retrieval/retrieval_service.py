from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.config import settings
from app.services.embeddings import embedding_service
from app.models.base import DocumentChunk, Document

class RetrievedChunk(BaseModel):
    content: str
    score: float
    page_number: int
    document_id: int
    chunk_id: int

    model_config = {"from_attributes": True}

async def retrieve_relevant_chunks(
    db: AsyncSession,
    query_text: str,
    workspace_id: int,
    top_k: Optional[int] = None,
    threshold: Optional[float] = None
) -> List[RetrievedChunk]:
    """
    Retrieve the most relevant document chunks for a given query within a workspace.
    Uses pgvector cosine distance.
    """
    # 1. Embed the query
    embeddings = await embedding_service.embed_texts([query_text])
    query_vector = embeddings[0]

    # 2. Vector search with workspace filter
    # Distance operator <=> is cosine distance.
    k = top_k or settings.RETRIEVAL_TOP_K
    t = threshold or settings.RETRIEVAL_THRESHOLD

    # 2. Vector search with workspace filter
    rows = []
    try:
        # Distance operator <=> is cosine distance for pgvector
        stmt = (
            select(
                DocumentChunk,
                (DocumentChunk.embedding.op("<=>")(query_vector)).label("distance")
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.workspace_id == workspace_id)
            .order_by(text("distance ASC"))
            .limit(k)
        )
        result = await db.execute(stmt)
        rows = result.all()
    except Exception:
        # If pgvector extension is not installed in the database, rollback and calculate in Python
        await db.rollback()
        import math
        fallback_stmt = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(Document.workspace_id == workspace_id)
        )
        fallback_res = await db.execute(fallback_stmt)
        all_chunks = fallback_res.scalars().all()

        scored = []
        for c in all_chunks:
            if not c.embedding:
                continue
            dot = sum(a * b for a, b in zip(query_vector, c.embedding))
            norm_q = math.sqrt(sum(a * a for a in query_vector)) or 1.0
            norm_c = math.sqrt(sum(b * b for b in c.embedding)) or 1.0
            similarity = dot / (norm_q * norm_c)
            distance = 1.0 - similarity
            scored.append((c, distance))

        scored.sort(key=lambda x: x[1])
        rows = scored[:k]

    if not rows:
        return []

    # 3. Calculate similarity and filter by threshold
    results = []
    for chunk, distance in rows:
        similarity = 1.0 - float(distance)
        if similarity >= t:
            results.append(RetrievedChunk(
                content=chunk.content,
                score=similarity,
                page_number=chunk.page_number,
                document_id=chunk.document_id,
                chunk_id=chunk.id
            ))

    return results
