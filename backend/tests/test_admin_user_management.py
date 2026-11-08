
import database

from models import User, AuditLog


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
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )
        assert user is not None
        user.role = "admin"
        db.commit()
    finally:
        db.close()


def get_user(email):
    db = database.SessionLocal()
    try:
        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )
    finally:
        db.close()


def get_audit_logs(action):
    db = database.SessionLocal()
    try:
        return (
            db.query(AuditLog)
            .filter(AuditLog.action == action)
            .all()
        )
    finally:
        db.close()


def test_admin_can_list_users(client):
    register_user(client, "student1@example.com")
    register_user(client, "student2@example.com")

    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    token = login_user(client, "admin@example.com")

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 3

    for user in response.json():
        assert "hashed_password" not in user


def test_student_cannot_list_users(client):
    register_user(client, "student@example.com")
    token = login_user(client, "student@example.com")

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_users(client):
    response = client.get("/api/admin/users")

    assert response.status_code == 401


def test_admin_can_filter_users_by_role(client):
    register_user(client, "student@example.com")
    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    token = login_user(client, "admin@example.com")

    response = client.get(
        "/api/admin/users?role=student",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert all(user["role"] == "student" for user in response.json())


def test_admin_can_search_users(client):
    register_user(client, "searchstudent@example.com")
    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    token = login_user(client, "admin@example.com")

    response = client.get(
        "/api/admin/users?search=searchstudent",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["email"] == "searchstudent@example.com"


def test_admin_can_promote_student(client):
    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    student = register_user(client, "student@example.com")

    token = login_user(client, "admin@example.com")

    response = client.patch(
        f"/api/admin/users/{student['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"

    updated_user = get_user("student@example.com")
    assert updated_user.role == "admin"

    logs = get_audit_logs("user_role_updated")
    assert len(logs) == 1
    assert logs[0].old_value == "student"
    assert logs[0].new_value == "admin"


def test_admin_can_demote_another_admin(client):
    register_user(client, "admin1@example.com")
    promote_to_admin("admin1@example.com")

    second_admin = register_user(client, "admin2@example.com")
    promote_to_admin("admin2@example.com")

    token = login_user(client, "admin1@example.com")

    response = client.patch(
        f"/api/admin/users/{second_admin['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "student"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "student"

    updated_user = get_user("admin2@example.com")
    assert updated_user.role == "student"

    logs = get_audit_logs("user_role_updated")
    assert len(logs) == 1
    assert logs[0].old_value == "admin"
    assert logs[0].new_value == "student"


def test_admin_cannot_demote_themselves(client):
    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    admin = get_user("admin@example.com")
    token = login_user(client, "admin@example.com")

    response = client.patch(
        f"/api/admin/users/{admin.id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "student"},
    )

    assert response.status_code == 409
    assert get_user("admin@example.com").role == "admin"


def test_invalid_role_is_rejected(client):
    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    student = register_user(client, "student@example.com")
    token = login_user(client, "admin@example.com")

    response = client.patch(
        f"/api/admin/users/{student['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "superadmin"},
    )

    assert response.status_code == 422
    assert get_user("student@example.com").role == "student"


def test_unknown_user_returns_404(client):
    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    token = login_user(client, "admin@example.com")

    response = client.patch(
        "/api/admin/users/99999/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )

    assert response.status_code == 404


def test_unchanged_role_does_not_create_audit_log(client):
    register_user(client, "admin@example.com")
    promote_to_admin("admin@example.com")

    student = register_user(client, "student@example.com")
    token = login_user(client, "admin@example.com")

    response = client.patch(
        f"/api/admin/users/{student['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "student"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User already has this role."

    logs = get_audit_logs("user_role_updated")
    assert len(logs) == 0


def test_student_cannot_change_user_role(client):
    register_user(client, "student1@example.com")
    student2 = register_user(client, "student2@example.com")

    token = login_user(client, "student1@example.com")

    response = client.patch(
        f"/api/admin/users/{student2['id']}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "admin"},
    )

    assert response.status_code == 403
    assert get_user("student2@example.com").role == "student"
