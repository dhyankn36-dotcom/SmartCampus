from database import SessionLocal
from models import User


def register_user(client, email):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Feedback Filter User",
            "email": email,
            "password": "TestPassword123",
        },
    )
    assert response.status_code == 201, response.json()


def login_user(client, email):
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "TestPassword123"},
    )
    assert response.status_code == 200, response.json()
    return response.json()["access_token"]


def promote_to_admin(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        assert user is not None
        user.role = "admin"
        db.commit()
    finally:
        db.close()


def test_admin_can_filter_feedback_by_rating_and_search(client):
    register_user(client, "feedback_filter_student@example.com")
    student_token = login_user(client, "feedback_filter_student@example.com")

    created = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Library WiFi issue",
            "description": "The library network disconnects.",
            "category": "Wi-Fi",
        },
    )
    assert created.status_code == 201, created.json()
    complaint_id = created.json()["id"]

    register_user(client, "feedback_filter_admin@example.com")
    promote_to_admin("feedback_filter_admin@example.com")
    admin_token = login_user(client, "feedback_filter_admin@example.com")
    headers = {"Authorization": f"Bearer {admin_token}"}

    resolved = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers=headers,
        json={"status": "Resolved"},
    )
    assert resolved.status_code == 200, resolved.json()

    submitted = client.post(
        f"/api/complaints/{complaint_id}/feedback",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "feedback": "The library WiFi works properly now.",
            "rating": 5,
        },
    )
    assert submitted.status_code == 200, submitted.json()

    by_rating = client.get("/api/admin/feedback?rating=5", headers=headers)
    assert by_rating.status_code == 200, by_rating.json()
    assert len(by_rating.json()) == 1
    assert by_rating.json()[0]["rating"] == 5

    by_search = client.get(
        "/api/admin/feedback?search=library",
        headers=headers,
    )
    assert by_search.status_code == 200, by_search.json()
    assert len(by_search.json()) == 1
    assert by_search.json()[0]["title"] == "Library WiFi issue"


def test_admin_feedback_filter_rejects_out_of_range_rating(client):
    register_user(client, "feedback_rating_admin@example.com")
    promote_to_admin("feedback_rating_admin@example.com")
    admin_token = login_user(client, "feedback_rating_admin@example.com")

    response = client.get(
        "/api/admin/feedback?rating=6",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422
