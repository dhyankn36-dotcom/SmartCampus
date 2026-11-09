
import pytest
from pydantic import ValidationError

from schemas import (
    UserRegister,
    ComplaintCreate,
    FeedbackCreate,
)


def test_valid_user_registration():
    user = UserRegister(
        name="Test Student",
        email="student@example.com",
        password="password123",
    )
    assert user.name == "Test Student"


def test_user_registration_trims_name():
    user = UserRegister(
        name="  Test Student  ",
        email="student@example.com",
        password="sample-password",
    )
    assert user.name == "Test Student"


def test_whitespace_only_user_name_rejected():
    with pytest.raises(ValidationError):
        UserRegister(
            name="   ",
            email="student@example.com",
            password="sample-password",
        )


def test_invalid_user_email():
    with pytest.raises(ValidationError):
        UserRegister(
            name="Test Student",
            email="invalid-email",
            password="password123",
        )


def test_short_password_rejected():
    with pytest.raises(ValidationError):
        UserRegister(
            name="Test Student",
            email="student@example.com",
            password="123",
        )


def test_valid_complaint():
    complaint = ComplaintCreate(
        title="WiFi not working",
        description="Internet connection is unavailable.",
        category="Wi-Fi",
    )
    assert complaint.category == "Wi-Fi"


def test_empty_complaint_title_rejected():
    with pytest.raises(ValidationError):
        ComplaintCreate(
            title="",
            description="Internet connection is unavailable.",
            category="Wi-Fi",
        )


@pytest.mark.parametrize("field", ["title", "description"])
def test_whitespace_only_complaint_text_rejected(field):
    complaint_data = {
        "title": "WiFi not working",
        "description": "Internet connection is unavailable.",
        "category": "Wi-Fi",
        field: "   ",
    }

    with pytest.raises(ValidationError):
        ComplaintCreate(**complaint_data)


def test_complaint_text_is_trimmed():
    complaint = ComplaintCreate(
        title="  WiFi not working  ",
        description="  Internet connection is unavailable.  ",
        category="Wi-Fi",
    )

    assert complaint.title == "WiFi not working"
    assert complaint.description == "Internet connection is unavailable."


def test_valid_feedback():
    feedback = FeedbackCreate(
        feedback="Issue resolved successfully.",
        rating=5,
    )
    assert feedback.rating == 5


@pytest.mark.parametrize("rating", [0, 6, -1])
def test_invalid_feedback_rating(rating):
    with pytest.raises(ValidationError):
        FeedbackCreate(
            feedback="Test feedback",
            rating=rating,
        )


def test_empty_feedback_rejected():
    with pytest.raises(ValidationError):
        FeedbackCreate(
            feedback="",
            rating=4,
        )
