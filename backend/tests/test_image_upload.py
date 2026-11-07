from io import BytesIO

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


def upload_image(client, complaint_id, token, filename, content, content_type):
    return client.post(
        f"/api/complaints/{complaint_id}/image",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                filename,
                BytesIO(content),
                content_type,
            )
        },
    )


def test_student_can_upload_valid_png_image(client):
    register_user(client, "image1@example.com")
    token = login_user(client, "image1@example.com")
    complaint_id = create_complaint(client, token)

    png_content = bytes.fromhex("89504E470D0A1A0A") + b"test-image-content"

    response = upload_image(
        client, complaint_id, token,
        "complaint.png", png_content, "image/png"
    )

    assert response.status_code == 200, response.json()
    assert response.json()["message"] == "Image uploaded successfully."
    assert response.json()["image_url"]


def test_upload_rejects_unsupported_file_extension(client):
    register_user(client, "image2@example.com")
    token = login_user(client, "image2@example.com")
    complaint_id = create_complaint(client, token)

    response = upload_image(
        client, complaint_id, token,
        "document.pdf", b"sample-content", "application/pdf"
    )

    assert response.status_code == 415


def test_upload_rejects_invalid_image_signature(client):
    register_user(client, "image3@example.com")
    token = login_user(client, "image3@example.com")
    complaint_id = create_complaint(client, token)

    response = upload_image(
        client, complaint_id, token,
        "fake.png", b"not-a-real-png-image", "image/png"
    )

    assert response.status_code == 400


def test_upload_rejects_file_larger_than_5mb(client):
    register_user(client, "image4@example.com")
    token = login_user(client, "image4@example.com")
    complaint_id = create_complaint(client, token)

    large_content = (
        bytes.fromhex("89504E470D0A1A0A") + b"x" * (5 * 1024 * 1024)
    )

    response = upload_image(
        client, complaint_id, token,
        "large.png", large_content, "image/png"
    )

    assert response.status_code in (400, 413)


def test_unauthenticated_user_cannot_upload_image(client):
    register_user(client, "image5@example.com")
    token = login_user(client, "image5@example.com")
    complaint_id = create_complaint(client, token)

    png_content = bytes.fromhex("89504E470D0A1A0A") + b"test-image-content"

    response = client.post(
        f"/api/complaints/{complaint_id}/image",
        files={
            "file": (
                "complaint.png",
                BytesIO(png_content),
                "image/png",
            )
        },
    )

    assert response.status_code == 401


def test_student_cannot_upload_image_to_another_students_complaint(client):
    register_user(client, "image6@example.com")
    first_token = login_user(client, "image6@example.com")
    complaint_id = create_complaint(client, first_token)

    register_user(client, "image7@example.com")
    second_token = login_user(client, "image7@example.com")

    png_content = bytes.fromhex("89504E470D0A1A0A") + b"test-image-content"

    response = upload_image(
        client, complaint_id, second_token,
        "complaint.png", png_content, "image/png"
    )

    assert response.status_code == 403
