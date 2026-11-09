
def register_user(client, email="student@example.com"):
    return client.post(
        "/api/auth/register",
        json={
            "name": "Test Student",
            "email": email,
            "password": "password123",
        },
    )


def login_user(client, email="student@example.com"):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )
    return response.json()["access_token"]


def test_health_endpoint(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_user_registration(client):
    response = register_user(client)

    assert response.status_code == 201
    assert response.json()["email"] == "student@example.com"
    assert response.json()["role"] == "student"


def test_registration_rejects_whitespace_only_name(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "   ",
            "email": "blank-name@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_duplicate_registration(client):
    register_user(client)

    response = register_user(client)

    assert response.status_code == 409


def test_user_login(client):
    register_user(client)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "student@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_invalid_login(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


def test_current_user_authentication(client):
    register_user(client)
    token = login_user(client)

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Test Student"


def test_complaint_requires_login(client):
    response = client.post(
        "/api/complaints",
        json={
            "title": "WiFi issue",
            "description": "Campus WiFi is unavailable.",
            "category": "Wi-Fi",
        },
    )

    assert response.status_code == 401


def test_complaint_creation_rejects_whitespace_only_text(client):
    register_user(client)
    token = login_user(client)
    headers = {"Authorization": f"Bearer {token}"}
    complaint_data = {
        "title": "WiFi issue",
        "description": "Campus WiFi is unavailable.",
        "category": "Wi-Fi",
    }

    for field in ("title", "description"):
        response = client.post(
            "/api/complaints",
            headers=headers,
            json={**complaint_data, field: "   "},
        )
        assert response.status_code == 422


def test_complaint_creation(client):
    register_user(client)
    token = login_user(client)

    response = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "WiFi issue",
            "description": "Campus WiFi is unavailable.",
            "category": "Wi-Fi",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "Submitted"
    assert response.json()["department"] == "IT Department"


def test_invalid_complaint_category(client):
    register_user(client)
    token = login_user(client)

    response = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Unknown issue",
            "description": "Testing invalid category.",
            "category": "Unknown",
        },
    )

    assert response.status_code == 400


def test_student_cannot_update_complaint_status(client):
    register_user(client)
    token = login_user(client)

    complaint = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "WiFi issue",
            "description": "Testing permissions.",
            "category": "Wi-Fi",
        },
    )

    complaint_id = complaint.json()["id"]

    response = client.patch(
        f"/api/complaints/{complaint_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "Resolved"},
    )

    assert response.status_code == 403


def test_student_cannot_access_another_students_complaint(client):
    register_user(client, "first@example.com")
    first_token = login_user(client, "first@example.com")

    complaint = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {first_token}"},
        json={
            "title": "Private complaint",
            "description": "This belongs to the first student.",
            "category": "Infrastructure",
        },
    )

    complaint_id = complaint.json()["id"]

    register_user(client, "second@example.com")
    second_token = login_user(client, "second@example.com")

    response = client.get(
        f"/api/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert response.status_code == 404
