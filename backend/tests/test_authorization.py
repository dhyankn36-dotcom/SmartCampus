
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
    return client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "WiFi issue",
            "description": "Campus WiFi is not working.",
            "category": "Wi-Fi",
        },
    )


def test_admin_can_update_complaint_status(client):
    register_user(client, "admin@example.com")
    student_token = login_user(client, "admin@example.com")

    complaint = create_complaint(client, student_token)
    assert complaint.status_code == 201

    complaint_id = complaint.json()["id"]

    promote_to_admin("admin@example.com")
    admin_token = login_user(client, "admin@example.com")

    response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "In Progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_admin_can_view_all_complaints(client):
    register_user(client, "first@example.com")
    first_token = login_user(client, "first@example.com")
    assert create_complaint(client, first_token).status_code == 201

    register_user(client, "second@example.com")
    second_token = login_user(client, "second@example.com")
    assert create_complaint(client, second_token).status_code == 201

    promote_to_admin("first@example.com")
    admin_token = login_user(client, "first@example.com")

    response = client.get(
        "/api/complaints",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_student_cannot_update_complaint_status(client):
    register_user(client, "student@example.com")
    token = login_user(client, "student@example.com")

    complaint = create_complaint(client, token)
    complaint_id = complaint.json()["id"]

    response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "Resolved"},
    )

    assert response.status_code == 403
