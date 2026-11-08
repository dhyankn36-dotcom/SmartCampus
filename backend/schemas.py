
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --------------------------------------------------
# USER SCHEMAS
# --------------------------------------------------

class UserRegister(BaseModel):
    """Request body for registering a new student."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Student's full name. Maximum 100 characters.",
        examples=["Dhyan Kumar"],
    )
    email: EmailStr = Field(
        description="A valid email address.",
        examples=["student@example.com"],
    )
    password: str = Field(
        min_length=6,
        max_length=128,
        description="Account password. Must contain 6 to 128 characters.",
        examples=["SecurePass123"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Dhyan Kumar",
                    "email": "student@example.com",
                    "password": "SecurePass123",
                }
            ]
        }
    )


class UserLogin(BaseModel):
    """Request body for user authentication."""

    email: EmailStr = Field(
        description="Registered email address.",
        examples=["student@example.com"],
    )
    password: str = Field(
        description="Account password.",
        examples=["SecurePass123"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "student@example.com",
                    "password": "SecurePass123",
                }
            ]
        }
    )


class UserResponse(BaseModel):
    """Public user profile returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str


class TokenResponse(BaseModel):
    """Authentication response containing a bearer access token."""

    access_token: str = Field(
        description="JWT access token used to authenticate protected endpoints."
    )
    token_type: str = Field(
        default="bearer",
        description="Token type.",
    )
    user: UserResponse


# --------------------------------------------------
# COMPLAINT SCHEMAS
# --------------------------------------------------

class ComplaintCreate(BaseModel):
    """Request body for creating a campus complaint."""

    title: str = Field(
        min_length=1,
        max_length=200,
        description="Short complaint title. Maximum 200 characters.",
        examples=["Broken classroom fan"],
    )
    description: str = Field(
        min_length=1,
        description="Detailed explanation of the campus issue.",
        examples=["The ceiling fan in classroom 204 is not working."],
    )
    category: str = Field(
        description=(
            "Complaint category: Infrastructure, Wi-Fi, "
            "Cleanliness, or Transport."
        ),
        examples=["Infrastructure"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Broken classroom fan",
                    "description": "The ceiling fan in classroom 204 is not working.",
                    "category": "Infrastructure",
                }
            ]
        }
    )


class ComplaintStatusUpdate(BaseModel):
    """Request body for changing a complaint's status."""

    status: str = Field(
        description=(
            "New status: Submitted, In Progress, Resolved, or Rejected."
        ),
        examples=["In Progress"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "In Progress"
                }
            ]
        }
    )


class ComplaintResponse(BaseModel):
    """Complaint details returned by the API."""

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
# STATUS HISTORY SCHEMAS
# --------------------------------------------------

class StatusHistoryResponse(BaseModel):
    """A single complaint status-history entry."""

    id: int
    complaint_id: int
    old_status: str | None = None
    new_status: str
    changed_by_user_id: int | None = None
    changed_by_name: str
    changed_at: datetime


# --------------------------------------------------
# FEEDBACK SCHEMAS
# --------------------------------------------------

class FeedbackCreate(BaseModel):
    """Request body for submitting feedback after resolution."""

    feedback: str = Field(
        min_length=1,
        max_length=1000,
        description="Written feedback. Maximum 1000 characters.",
        examples=["The issue was resolved quickly. Thank you."],
    )
    rating: int = Field(
        ge=1,
        le=5,
        description="Rating from 1 (lowest) to 5 (highest).",
        examples=[5],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "feedback": "The issue was resolved quickly. Thank you.",
                    "rating": 5,
                }
            ]
        }
    )


class FeedbackResponse(BaseModel):
    """Student feedback details returned to administrators."""

    complaint_id: int
    ticket_id: str
    title: str
    feedback: str
    rating: int
    feedback_submitted_at: datetime
    student_name: str


class FeedbackAnalytics(BaseModel):
    """Aggregated student feedback statistics."""

    total_feedback: int
    average_rating: float
    rating_distribution: dict[int, int]
