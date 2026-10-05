import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.retrieval.retrieval_service import retrieve_relevant_chunks, RetrievedChunk
from app.models.base import Document, DocumentChunk
from app.core.config import settings

@pytest.fixture
def mock_db():
    db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    db.execute.return_value = mock_result
    return db

@pytest.fixture
def mock_embedding_service():
    with patch("app.services.retrieval.retrieval_service.embedding_service") as mock:
        mock.embed_texts = AsyncMock()
        yield mock

@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_basic(mock_db, mock_embedding_service):
    # Mock embedding
    mock_embedding_service.embed_texts.return_value = [[0.1] * 1536]

    # Mock DB result
    # We mock the result of db.execute(stmt)
    mock_row = (
        DocumentChunk(id=1, content="Relevant text", page_number=1, document_id=10, embedding=[0.1]*1536),
        0.1 # distance
    )
    mock_db.execute.return_value.all.return_value = [mock_row]

    results = await retrieve_relevant_chunks(mock_db, "test query", 1)

    assert len(results) == 1
    assert results[0].content == "Relevant text"
    assert results[0].score == pytest.approx(0.9) # 1 - 0.1

@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_isolation(mock_db, mock_embedding_service):
    # Mock embedding
    mock_embedding_service.embed_texts.return_value = [[0.1] * 1536]

    # Mock DB result to return nothing (simulating ownership filter in SQL)
    mock_db.execute.return_value.all.return_value = []

    results = await retrieve_relevant_chunks(mock_db, "test query", 2)

    assert len(results) == 0

@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_threshold(mock_db, mock_embedding_service):
    # Mock embedding
    mock_embedding_service.embed_texts.return_value = [[0.1] * 1536]

    # Mock DB result with a high distance (low similarity)
    # distance 0.5 -> similarity 0.5 < threshold 0.7
    mock_row = (
        DocumentChunk(id=1, content="Irrelevant text", page_number=1, document_id=10, embedding=[0.5]*1536),
        0.5
    )
    mock_db.execute.return_value.all.return_value = [mock_row]

    results = await retrieve_relevant_chunks(mock_db, "test query", 1)

    assert len(results) == 0
