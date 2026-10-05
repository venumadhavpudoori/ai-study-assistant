from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.core.db import async_session_maker
from app.core.config import settings
from app.models.base import Document, DocumentStatus
from app.services.document.storage import storage
from app.services.rag.ingest import extract_text, chunk_text, embed_and_store
import logging

logger = logging.getLogger(__name__)

async def process_document_ingestion(document_id: int):
    """
    Orchestrates the ingestion pipeline:
    UPLOADED -> PROCESSING -> READY (or FAILED)
    """
    async with async_session_maker() as db:
        try:
            # 1. Update status to PROCESSING
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status=DocumentStatus.PROCESSING)
            )
            await db.commit()

            # 2. Locate file
            # We assume filename in DB is the safe unique filename
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                raise ValueError(f"Document {document_id} not found")

            file_path = storage.get_path(doc.filename)

            # 3. Pipeline
            pages_text = extract_text(file_path)
            chunks = chunk_text(pages_text)
            await embed_and_store(db, document_id, chunks)

            # 4. Set to READY
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status=DocumentStatus.READY, error=None)
            )
            await db.commit()

        except Exception as e:
            logger.exception(f"Ingestion failed for document {document_id}")
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status=DocumentStatus.FAILED, error=str(e))
            )
            await db.commit()

# Import select for the query
from sqlalchemy import select
