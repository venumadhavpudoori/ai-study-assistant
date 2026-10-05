from pydantic import BaseModel, ConfigDict
from datetime import datetime

class WorkspaceBase(BaseModel):
    name: str

class WorkspaceCreate(WorkspaceBase):
    pass

class WorkspaceRead(WorkspaceBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
