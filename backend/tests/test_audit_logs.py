
import database

from models import AuditLog, User


def register_student(client, email="student@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test Student",
            "email": email,
            "password": "TestPassword123",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()


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
    db = database.SessionLocal()

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
            "description": "The classroom fan is not working.",
            "category": "Infrastructure",
        },
    )

    assert response.status_code == 201, response.json()
    return response.json()["id"]


def test_admin_status_update_creates_audit_log(client):
    register_student(client)
    student_token = login_user(client, "student@example.com")

    complaint_id = create_complaint(client, student_token)

    promote_to_admin("student@example.com")
    admin_token = login_user(client, "student@example.com")

    response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "In Progress"},
    )

    assert response.status_code == 200, response.json()

    audit_response = client.get(
        "/api/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert audit_response.status_code == 200
    logs = audit_response.json()

    assert len(logs) == 1
    assert logs[0]["actor_name"] == "Test Student"
    assert logs[0]["complaint_id"] == complaint_id
    assert logs[0]["action"] == "complaint_status_updated"
    assert logs[0]["old_value"] == "Submitted"
    assert logs[0]["new_value"] == "In Progress"
    assert logs[0]["actor_user_id"] is not None
    assert logs[0]["created_at"] is not None


def test_student_cannot_view_audit_logs(client):
    register_student(client)

    token = login_user(client, "student@example.com")

    response = client.get(
        "/api/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_audit_logs(client):
    response = client.get("/api/admin/audit-logs")

    assert response.status_code == 401


def test_audit_logs_can_be_filtered_by_complaint_and_action(client):
    register_student(client)
    student_token = login_user(client, "student@example.com")

    complaint_id = create_complaint(client, student_token)

    promote_to_admin("student@example.com")
    admin_token = login_user(client, "student@example.com")

    client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "In Progress"},
    )

    headers = {"Authorization": f"Bearer {admin_token}"}

    filtered_response = client.get(
        "/api/admin/audit-logs",
        headers=headers,
        params={
            "complaint_id": complaint_id,
            "action": "complaint_status_updated",
            "page": 1,
            "page_size": 10,
        },
    )

    assert filtered_response.status_code == 200
    logs = filtered_response.json()

    assert len(logs) == 1
    assert logs[0]["complaint_id"] == complaint_id
    assert logs[0]["action"] == "complaint_status_updated"


def test_repeating_same_status_does_not_create_audit_log(client):
    register_student(client)
    student_token = login_user(client, "student@example.com")

    complaint_id = create_complaint(client, student_token)

    promote_to_admin("student@example.com")
    admin_token = login_user(client, "student@example.com")

    response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Submitted"},
    )

    assert response.status_code == 200

    audit_response = client.get(
        "/api/admin/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert audit_response.status_code == 200
    assert audit_response.json() == []
