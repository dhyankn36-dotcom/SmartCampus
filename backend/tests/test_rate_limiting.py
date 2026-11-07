
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
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["id"]


def test_registration_rate_limit(client):
    for number in range(3):
        response = client.post(
            "/api/auth/register",
            json={
                "name": "Test Student",
                "email": f"student{number}@example.com",
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 201

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Extra Student",
            "email": "extra@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_login_rate_limit(client):
    register_user(client, "login@example.com")

    for _ in range(5):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 200

    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "TestPassword123",
        },
    )

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_complaint_creation_rate_limit(client):
    register_user(client, "complaints@example.com")
    token = login_user(client, "complaints@example.com")

    for _ in range(10):
        create_complaint(client, token)

    response = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Extra complaint",
            "description": "This should exceed the limit.",
            "category": "Infrastructure",
        },
    )

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_image_upload_rate_limit(client):
    register_user(client, "images@example.com")
    token = login_user(client, "images@example.com")
    complaint_id = create_complaint(client, token)

    image_content = (
        bytes.fromhex("89504E470D0A1A0A") + b"test-image-content"
    )

    for _ in range(5):
        response = client.post(
            f"/api/complaints/{complaint_id}/image",
            headers={"Authorization": f"Bearer {token}"},
            files={
                "file": (
                    "test.png",
                    image_content,
                    "image/png",
                )
            },
        )
        assert response.status_code == 200, response.json()

    response = client.post(
        f"/api/complaints/{complaint_id}/image",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "test.png",
                image_content,
                "image/png",
            )
        },
    )

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_feedback_rate_limit(client):
    register_user(client, "feedback@example.com")
    token = login_user(client, "feedback@example.com")

    complaint_id = create_complaint(client, token)

    promote_to_admin("feedback@example.com")
    admin_token = login_user(client, "feedback@example.com")

    status_response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "Resolved"},
    )
    assert status_response.status_code == 200

    feedback_payload = {
        "feedback": "The complaint was resolved successfully.",
        "rating": 5,
    }

    for _ in range(3):
        response = client.post(
            f"/api/complaints/{complaint_id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json=feedback_payload,
        )

        assert response.status_code in (200, 409)

    response = client.post(
        f"/api/complaints/{complaint_id}/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json=feedback_payload,
    )

    assert response.status_code == 429
    assert "Retry-After" in response.headers
