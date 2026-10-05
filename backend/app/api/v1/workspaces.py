from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.db import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.base import User, Workspace, Document, Conversation, DocumentStatus
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead
from app.schemas.document import DocumentRead
from app.schemas.conversation import ConversationRead
from app.services.document.storage import storage
from app.services.document.utils import validate_pdf_mime, validate_file_size, generate_safe_filename
from app.workers.ingestion import process_document_ingestion

router = APIRouter()

@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_workspace = Workspace(
        name=workspace_in.name,
        owner_id=current_user.id
    )
    db.add(new_workspace)
    await db.commit()
    await db.refresh(new_workspace)
    return new_workspace

@router.get("/", response_model=List[WorkspaceRead])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Workspace).where(Workspace.owner_id == current_user.id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{id}", response_model=WorkspaceRead)
async def get_workspace(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Workspace).where(
        Workspace.id == id,
        Workspace.owner_id == current_user.id
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Workspace).where(
        Workspace.id == id,
        Workspace.owner_id == current_user.id
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    await db.delete(workspace)
    await db.commit()
    return None

@router.get("/{id}/documents", response_model=List[DocumentRead])
async def list_workspace_documents(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify workspace ownership
    stmt_ws = select(Workspace).where(Workspace.id == id, Workspace.owner_id == current_user.id)
    ws_result = await db.execute(stmt_ws)
    if not ws_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get documents
    stmt_docs = select(Document).where(Document.workspace_id == id)
    result = await db.execute(stmt_docs)
    return result.scalars().all()

@router.post("/{id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
@router.post("/{id}/documents/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def upload_workspace_document(
    id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Verify workspace ownership
    stmt_ws = select(Workspace).where(Workspace.id == id, Workspace.owner_id == current_user.id)
    ws_result = await db.execute(stmt_ws)
    workspace = ws_result.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # 2. Read file content
    content = await file.read()

    # 3. Validate size limit
    if not validate_file_size(len(content)):
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE // (1024 * 1024)}MB"
        )

    # 4. Validate PDF magic bytes
    if not validate_pdf_mime(content):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only valid PDF files are accepted."
        )

    # 5. Generate safe filename & save to storage
    safe_filename = generate_safe_filename(file.filename or "upload.pdf")
    storage.save_file(content, safe_filename)

    # 6. Insert Document record
    new_doc = Document(
        workspace_id=id,
        filename=safe_filename,
        status=DocumentStatus.UPLOADED
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    # 7. Enqueue background ingestion
    background_tasks.add_task(process_document_ingestion, new_doc.id)

    return new_doc

@router.get("/{id}/conversations", response_model=List[ConversationRead])
async def list_workspace_conversations(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify workspace ownership
    stmt_ws = select(Workspace).where(Workspace.id == id, Workspace.owner_id == current_user.id)
    ws_result = await db.execute(stmt_ws)
    if not ws_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Get conversations
    stmt_conv = select(Conversation).where(
        Conversation.workspace_id == id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt_conv)
    return result.scalars().all()
