import fitz  # PyMuPDF
import tiktoken
from typing import List, NamedTuple
from app.core.config import settings
from app.services.embeddings import embedding_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, insert
from app.models.base import DocumentChunk

class Chunk(NamedTuple):
    text: str
    page_number: int

def extract_text(file_path: str) -> List[str]:
    """Extract text from PDF page by page."""
    pages_text = []
    with fitz.open(file_path) as doc:
        for page in doc:
            pages_text.append(page.get_text("text"))
    return pages_text

def chunk_text(pages_text: List[str]) -> List[Chunk]:
    """Split text into chunks following token and page constraints."""
    encoding = tiktoken.get_encoding("cl100k_base")
    chunks = []

    for page_num, text in enumerate(pages_text, start=1):
        paragraphs = text.split("\n\n")
        current_chunk_tokens = []
        current_chunk_text = []

        for para in paragraphs:
            para_tokens = encoding.encode(para)

            # If a single paragraph is too large, split it (simplistic)
            if len(para_tokens) > settings.CHUNK_SIZE:
                # Split into smaller parts
                for i in range(0, len(para_tokens), settings.CHUNK_SIZE):
                    part_tokens = para_tokens[i : i + settings.CHUNK_SIZE]
                    chunks.append(Chunk(
                        text=encoding.decode(part_tokens),
                        page_number=page_num
                    ))
                continue

            # Check if adding this paragraph exceeds chunk size
            if len(current_chunk_tokens) + len(para_tokens) > settings.CHUNK_SIZE:
                # Save current chunk
                chunks.append(Chunk(
                    text=" ".join(current_chunk_text),
                    page_number=page_num
                ))

                # Implement overlap: keep the end of previous chunk
                overlap_tokens = current_chunk_tokens[-settings.CHUNK_OVERLAP:] if len(current_chunk_tokens) > settings.CHUNK_OVERLAP else current_chunk_tokens
                current_chunk_tokens = overlap_tokens
                current_chunk_text = [encoding.decode(overlap_tokens)]

                # Now add the current paragraph
                current_chunk_tokens.extend(para_tokens)
                current_chunk_text.append(para)
            else:
                current_chunk_tokens.extend(para_tokens)
                current_chunk_text.append(para)

        # Add final chunk for the page
        if current_chunk_text:
            chunks.append(Chunk(
                text=" ".join(current_chunk_text),
                page_number=page_num
            ))

    return chunks

async def embed_and_store(db: AsyncSession, document_id: int, chunks: List[Chunk]):
    """Vectorize chunks and store them in the database."""
    # 1. Idempotency: Delete existing chunks
    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

    # 2. Batch process embeddings
    texts = [c.text for c in chunks]
    embeddings = await embedding_service.embed_texts(texts)

    # 3. Bulk insert
    chunk_records = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        chunk_records.append({
            "document_id": document_id,
            "chunk_index": i,
            "page_number": chunk.page_number,
            "content": chunk.text,
            "embedding": emb,
            "embedding_model": embedding_service.model_name
        })

    if chunk_records:
        await db.execute(insert(DocumentChunk), chunk_records)

    await db.commit()
