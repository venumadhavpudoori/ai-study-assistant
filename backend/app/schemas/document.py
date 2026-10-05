from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.base import DocumentStatus

class DocumentRead(BaseModel):
    id: int
    workspace_id: int
    filename: str
    status: DocumentStatus
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
