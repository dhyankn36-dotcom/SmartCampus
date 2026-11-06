
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --------------------------------------------------
# USER SCHEMAS
# --------------------------------------------------

class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --------------------------------------------------
# COMPLAINT SCHEMAS
# --------------------------------------------------

class ComplaintCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: str


class ComplaintStatusUpdate(BaseModel):
    status: str


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
    feedback_rating: int | None = None
    feedback_submitted_at: datetime | None = None
    image_url: str | None = None


# --------------------------------------------------
# FEEDBACK SCHEMAS
# --------------------------------------------------

class FeedbackCreate(BaseModel):
    feedback: str = Field(min_length=1, max_length=1000)
    rating: int = Field(ge=1, le=5)


class FeedbackResponse(BaseModel):
    complaint_id: int
    ticket_id: str
    title: str
    feedback: str
    rating: int
    feedback_submitted_at: datetime
    student_name: str


class FeedbackAnalytics(BaseModel):
    total_feedback: int
    average_rating: float
    rating_distribution: dict[int, int]
