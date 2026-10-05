import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.core.config import settings
from app.services.retrieval.retrieval_service import retrieve_relevant_chunks, RetrievedChunk
from app.services.llm import llm_service
from app.services.rag.prompt_service import prompt_service
from app.services.rag.validation import validate_citations
from app.services.rag.rewrite_service import rewrite_query
from app.models.base import Message, MessageSource

logger = logging.getLogger(__name__)

async def generate_rag_answer(
    db: AsyncSession,
    conversation_id: int,
    user_id: int,
    workspace_id: int,
    query_text: str
) -> Tuple[str, List[int]]:
    """
    Orchestrates the RAG flow: Rewrite -> Retrieval -> Prompting -> Generation -> Validation.
    Returns the final answer and the list of chunk IDs used.
    """
    try:
        # 1. Rewrite query for conversational context
        standalone_query = await rewrite_query(db, conversation_id, query_text)

        # 2. Retrieval using standalone query
        chunks = await retrieve_relevant_chunks(
            db=db,
            query_text=standalone_query,
            workspace_id=workspace_id
        )

        # 3. Threshold Check
        if not chunks:
            return "I couldn't find enough information in your uploaded materials", []

        # 4. Build Prompt
        system_prompt = prompt_service.get_prompt("rag_v1.txt")

        # Format context: [1] (doc_id, p.N): content
        context_blocks = []
        for i, chunk in enumerate(chunks, start=1):
            block = f"[{i}] (Doc {chunk.document_id}, p.{chunk.page_number}): {chunk.content}"
            context_blocks.append(block)

        user_prompt = "Context:\n" + "\n".join(context_blocks) + f"\n\nQuestion: {query_text}"

        # 5. Generate Answer
        raw_answer = await llm_service.generate(system_prompt, user_prompt)

        # 6. Validate Citations
        final_answer = validate_citations(raw_answer, len(chunks))

        # Identify which chunks were actually cited
        cited_chunk_ids = []
        for i, chunk in enumerate(chunks, start=1):
            if f"[{i}]" in final_answer:
                cited_chunk_ids.append(chunk.chunk_id)

        return final_answer, cited_chunk_ids
    except Exception as e:
        logger.exception("Failed during RAG pipeline execution")
        err_msg = str(e)
        if "API key" in err_msg or "api_key" in err_msg or "401" in err_msg:
            return "I couldn't generate an answer because the OpenAI API key is missing or invalid. Please configure a valid OPENAI_API_KEY in your backend .env file.", []
        return f"Unable to generate answer due to an internal error: {err_msg}", []
