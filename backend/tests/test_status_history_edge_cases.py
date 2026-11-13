from database import SessionLocal
from models import User


def register_user(client, email):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "History Test Student",
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


def test_new_complaint_starts_with_submitted_history_entry(client):
    register_user(client, "initial_history@example.com")
    token = login_user(client, "initial_history@example.com")

    created = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Classroom projector issue",
            "description": "The projector is unavailable.",
            "category": "Infrastructure",
            "location": "Block B",
        },
    )
    assert created.status_code == 201, created.json()
    complaint_id = created.json()["id"]

    history = client.get(
        f"/api/complaints/{complaint_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert history.status_code == 200, history.json()
    assert len(history.json()) == 1
    assert history.json()[0]["old_status"] is None
    assert history.json()[0]["new_status"] == "Submitted"


def test_status_history_preserves_each_transition_in_order(client):
    register_user(client, "transition_student@example.com")
    student_token = login_user(client, "transition_student@example.com")

    created = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Campus network issue",
            "description": "The network is unavailable.",
            "category": "Wi-Fi",
            "location": "Library",
        },
    )
    assert created.status_code == 201, created.json()
    complaint_id = created.json()["id"]

    register_user(client, "transition_admin@example.com")
    promote_to_admin("transition_admin@example.com")
    admin_token = login_user(client, "transition_admin@example.com")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    for next_status in ("In Progress", "Resolved"):
        updated = client.patch(
            f"/api/complaints/{complaint_id}/status",
            headers=admin_headers,
            json={"status": next_status},
        )
        assert updated.status_code == 200, updated.json()

    history = client.get(
        f"/api/complaints/{complaint_id}/history",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert history.status_code == 200, history.json()
    transitions = [
        (entry["old_status"], entry["new_status"])
        for entry in history.json()
    ]
    assert transitions == [
        (None, "Submitted"),
        ("Submitted", "In Progress"),
        ("In Progress", "Resolved"),
    ]
