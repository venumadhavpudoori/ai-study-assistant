from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.llm import llm_service
from app.services.rag.prompt_service import prompt_service
from app.models.base import Message

async def rewrite_query(db: AsyncSession, conversation_id: int, query_text: str) -> str:
    """
    Transforms a conversational query into a standalone search query using chat history.
    """
    # 1. Fetch last 5 messages for context
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(5)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    # Reverse them to chronological order
    messages = list(reversed(messages))

    if not messages:
        return query_text

    # 2. Format chat history
    history = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        history.append(f"{role}: {msg.content}")

    history_str = "\n".join(history)

    # 3. Generate rewrite
    system_prompt = prompt_service.get_prompt("rewrite_v1.txt")
    user_prompt = f"Chat History:\n{history_str}\n\nNew Question: {query_text}"

    try:
        rewritten_query = await llm_service.generate(system_prompt, user_prompt)
        return rewritten_query.strip()
    except Exception:
        # Fallback to original query on failure
        return query_text
