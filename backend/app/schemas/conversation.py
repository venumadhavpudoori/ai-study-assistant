from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ConversationCreate(BaseModel):
    workspace_id: int
    title: str

class ConversationRead(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
