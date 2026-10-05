from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.base import User, Document, Workspace
from app.services.document.storage import storage

router = APIRouter()

@router.get("/{id}/view")
async def view_document(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Ownership check
    stmt = select(Document).join(Workspace).where(
        Document.id == id,
        Workspace.owner_id == current_user.id
    )
    result = await db.execute(stmt)
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Serve file
    file_path = storage.get_path(document.filename)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.filename
    )
