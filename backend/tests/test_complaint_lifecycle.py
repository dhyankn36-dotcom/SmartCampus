
from database import SessionLocal
from models import User


def register_user(client, email):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test Student",
            "email": email,
            "password": "TestPassword123",
        },
    )
    assert response.status_code == 201, response.json()


def login_user(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "TestPassword123",
        },
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


def test_complete_complaint_lifecycle(client):
    register_user(client, "lifecycle_student@example.com")
    student_token = login_user(client, "lifecycle_student@example.com")

    register_user(client, "lifecycle_admin@example.com")
    promote_to_admin("lifecycle_admin@example.com")
    admin_token = login_user(client, "lifecycle_admin@example.com")

    complaint_response = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Broken classroom fan",
            "description": "The classroom fan is not working.",
            "category": "Infrastructure",
            "location": "Block A",
        },
    )

    assert complaint_response.status_code == 201, complaint_response.json()
    complaint_id = complaint_response.json()["id"]

    for new_status in ["In Progress", "Resolved"]:
        response = client.patch(
            f"/api/complaints/{complaint_id}/status",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": new_status},
        )

        assert response.status_code == 200, response.json()

    history_response = client.get(
        f"/api/complaints/{complaint_id}/history",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 3

    assert history[0]["old_status"] is None
    assert history[0]["new_status"] == "Submitted"

    assert history[1]["old_status"] == "Submitted"
    assert history[1]["new_status"] == "In Progress"

    assert history[2]["old_status"] == "In Progress"
    assert history[2]["new_status"] == "Resolved"
