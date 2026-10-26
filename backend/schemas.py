
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)
    category: str


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: str
    title: str
    description: str
    category: str
    department: str
    status: str
    submitted_at: datetime
    feedback: str | None = None
