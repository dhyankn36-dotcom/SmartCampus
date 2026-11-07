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


def create_complaint(client, token):
    response = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Broken classroom fan",
            "description": "The fan is not working.",
            "category": "Infrastructure",
            "location": "Block A",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["id"]


def update_status(client, complaint_id, token, new_status):
    return client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": new_status},
    )


def test_status_history_recorded_after_admin_update(client):
    register_user(client, "history1@example.com")
    student_token = login_user(client, "history1@example.com")

    register_user(client, "historyadmin1@example.com")
    promote_to_admin("historyadmin1@example.com")
    admin_token = login_user(client, "historyadmin1@example.com")

    complaint_id = create_complaint(client, student_token)

    update_response = update_status(
        client, complaint_id, admin_token, "In Progress"
    )
    assert update_response.status_code == 200, update_response.json()

    response = client.get(
        f"/api/complaints/{complaint_id}/history",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200, response.json()
    history = response.json()
    assert len(history) >= 1
    assert history[-1]["new_status"] == "In Progress"
    assert history[-1]["old_status"] == "Submitted"


def test_student_can_view_own_complaint_history(client):
    register_user(client, "history2@example.com")
    token = login_user(client, "history2@example.com")
    complaint_id = create_complaint(client, token)

    response = client.get(
        f"/api/complaints/{complaint_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.json()
    assert isinstance(response.json(), list)


def test_student_cannot_view_another_students_history(client):
    register_user(client, "history3@example.com")
    first_token = login_user(client, "history3@example.com")
    complaint_id = create_complaint(client, first_token)

    register_user(client, "history4@example.com")
    second_token = login_user(client, "history4@example.com")

    response = client.get(
        f"/api/complaints/{complaint_id}/history",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_history(client):
    register_user(client, "history5@example.com")
    token = login_user(client, "history5@example.com")
    complaint_id = create_complaint(client, token)

    response = client.get(
        f"/api/complaints/{complaint_id}/history"
    )

    assert response.status_code == 401
