from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.base import User, Conversation, Message, MessageSource, Workspace, DocumentChunk
from app.schemas.conversation import ConversationCreate, ConversationRead
from app.services.rag.rag_service import generate_rag_answer

router = APIRouter()

class MessageRequest(BaseModel):
    text: str

class SourceResponse(BaseModel):
    document_id: int
    page_number: int

    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: Optional[datetime] = None
    sources: List[SourceResponse] = []

    model_config = ConfigDict(from_attributes=True)

@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Ownership check for workspace
    stmt = select(Workspace).where(
        Workspace.id == request.workspace_id,
        Workspace.owner_id == current_user.id
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # 2. Create conversation
    new_conv = Conversation(
        workspace_id=request.workspace_id,
        user_id=current_user.id,
        title=request.title
    )
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    return new_conv

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Ownership check for conversation
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Get all messages for conversation ordered chronologically
    stmt_msgs = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    res_msgs = await db.execute(stmt_msgs)
    messages = res_msgs.scalars().all()
    if not messages:
        return []

    # 3. Load sources for assistant messages
    assistant_msg_ids = [m.id for m in messages if m.role == "assistant"]
    sources_by_msg = {}
    if assistant_msg_ids:
        stmt_sources = (
            select(
                MessageSource.message_id,
                DocumentChunk.document_id,
                DocumentChunk.page_number
            )
            .join(DocumentChunk, MessageSource.chunk_id == DocumentChunk.id)
            .where(MessageSource.message_id.in_(assistant_msg_ids))
            .order_by(MessageSource.id.asc())
        )
        src_res = await db.execute(stmt_sources)
        for msg_id, doc_id, page_num in src_res.all():
            sources_by_msg.setdefault(msg_id, []).append(
                SourceResponse(document_id=doc_id, page_number=page_num)
            )

    return [
        MessageResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            sources=sources_by_msg.get(m.id, [])
        )
        for m in messages
    ]

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    request: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Ownership check for conversation
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Save user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.text
    )
    db.add(user_msg)
    await db.commit()

    # 3. Generate RAG answer
    answer_text, used_chunk_ids = await generate_rag_answer(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        workspace_id=conversation.workspace_id,
        query_text=request.text
    )

    # 4. Save assistant message
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=answer_text
    )
    db.add(assistant_msg)
    await db.flush()

    # 5. Save sources
    ret_sources = []
    if used_chunk_ids:
        sources = [
            MessageSource(message_id=assistant_msg.id, chunk_id=cid, score=0.0)
            for cid in used_chunk_ids
        ]
        db.add_all(sources)
        await db.commit()

        # Load citation doc_id and page numbers for the response
        stmt_src = (
            select(DocumentChunk.document_id, DocumentChunk.page_number)
            .where(DocumentChunk.id.in_(used_chunk_ids))
        )
        src_rows = await db.execute(stmt_src)
        ret_sources = [
            SourceResponse(document_id=row[0], page_number=row[1])
            for row in src_rows.all()
        ]
    else:
        await db.commit()

    return MessageResponse(
        id=assistant_msg.id,
        conversation_id=assistant_msg.conversation_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at,
        sources=ret_sources
    )
