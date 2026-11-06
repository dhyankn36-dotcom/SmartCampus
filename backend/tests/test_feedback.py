
from database import SessionLocal
from models import User


def register_user(client, email):
    return client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "password123",
        },
    )


def login_user(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )
    assert response.status_code == 200
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


def create_complaint(client, token):
    response = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "WiFi issue",
            "description": "Campus WiFi is not working.",
            "category": "Wi-Fi",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def resolve_complaint(client, complaint_id, admin_token):
    return client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Resolved"},
    )


def submit_feedback(client, complaint_id, token, feedback):
    return client.post(
        f"/api/complaints/{complaint_id}/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "feedback": feedback,
            "rating": 5,
        },
    )


def test_student_can_submit_feedback(client):
    register_user(client, "student@example.com")
    student_token = login_user(client, "student@example.com")

    complaint_id = create_complaint(client, student_token)

    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")
    admin_token = login_user(client, "admin@example.com")

    resolved = resolve_complaint(
        client, complaint_id, admin_token
    )
    assert resolved.status_code == 200

    response = submit_feedback(
        client,
        complaint_id,
        student_token,
        "The WiFi issue was resolved successfully.",
    )

    assert response.status_code == 200
    assert response.json()["feedback"] == (
        "The WiFi issue was resolved successfully."
    )


def test_feedback_rejected_for_unresolved_complaint(client):
    register_user(client, "student@example.com")
    token = login_user(client, "student@example.com")

    complaint_id = create_complaint(client, token)

    response = submit_feedback(
        client,
        complaint_id,
        token,
        "Thank you for the support.",
    )

    assert response.status_code == 400


def test_empty_feedback_rejected(client):
    register_user(client, "student@example.com")
    token = login_user(client, "student@example.com")

    complaint_id = create_complaint(client, token)

    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")
    admin_token = login_user(client, "admin@example.com")

    resolve_complaint(client, complaint_id, admin_token)

    response = submit_feedback(
        client, complaint_id, token, ""
    )

    assert response.status_code == 422


def test_feedback_rejected_for_another_students_complaint(client):
    register_user(client, "first@example.com")
    first_token = login_user(client, "first@example.com")

    complaint_id = create_complaint(client, first_token)

    register_user(client, "second@example.com")
    second_token = login_user(client, "second@example.com")

    response = submit_feedback(
        client,
        complaint_id,
        second_token,
        "Trying to access another complaint.",
    )

    assert response.status_code == 403
    


def test_feedback_over_2000_characters_rejected(client):
    register_user(client, "student@example.com")
    token = login_user(client, "student@example.com")

    complaint_id = create_complaint(client, token)

    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")
    admin_token = login_user(client, "admin@example.com")

    resolve_complaint(client, complaint_id, admin_token)

    response = submit_feedback(
        client, complaint_id, token, "A" * 2001
    )

    assert response.status_code == 422
