
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


def create_complaint(client, token, title, description, category):
    response = client.post(
        "/api/complaints",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "description": description,
            "category": category,
            "location": "Block A",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()


def test_search_complaints_by_title(client):
    register_user(client, "search_title@example.com")
    token = login_user(client, "search_title@example.com")

    create_complaint(
        client, token, "Broken classroom fan",
        "The fan is not working.", "Infrastructure"
    )
    create_complaint(
        client, token, "WiFi connection issue",
        "Internet is unavailable.", "Wi-Fi"
    )

    response = client.get(
        "/api/complaints?search=classroom",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Broken classroom fan"


def test_search_complaints_by_description(client):
    register_user(client, "search_description@example.com")
    token = login_user(client, "search_description@example.com")

    create_complaint(
        client, token, "Network issue",
        "Internet connection is unstable.", "Wi-Fi"
    )
    create_complaint(
        client, token, "Broken chair",
        "The classroom chair is damaged.", "Infrastructure"
    )

    response = client.get(
        "/api/complaints?search=unstable",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Network issue"


def test_search_complaints_by_ticket_id(client):
    register_user(client, "search_ticket@example.com")
    token = login_user(client, "search_ticket@example.com")

    complaint = create_complaint(
        client, token, "Broken projector",
        "Projector is not working.", "Infrastructure"
    )

    response = client.get(
        f"/api/complaints?search={complaint['ticket_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ticket_id"] == complaint["ticket_id"]


def test_filter_complaints_by_category(client):
    register_user(client, "filter_category@example.com")
    token = login_user(client, "filter_category@example.com")

    create_complaint(
        client, token, "Broken fan",
        "Fan not working.", "Infrastructure"
    )
    create_complaint(
        client, token, "Internet issue",
        "WiFi unavailable.", "Wi-Fi"
    )

    response = client.get(
        "/api/complaints?category=Infrastructure",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["category"] == "Infrastructure"


def test_filter_complaints_by_status(client):
    register_user(client, "filter_status@example.com")
    student_token = login_user(client, "filter_status@example.com")

    complaint = create_complaint(
        client, student_token, "Broken fan",
        "Fan not working.", "Infrastructure"
    )

    register_user(client, "filter_admin@example.com")
    promote_to_admin("filter_admin@example.com")
    admin_token = login_user(client, "filter_admin@example.com")

    update_response = client.patch(
        f"/api/complaints/{complaint['id']}/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"status": "In Progress"},
    )
    assert update_response.status_code == 200

    response = client.get(
        "/api/complaints?status=In%20Progress",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "In Progress"


def test_invalid_status_filter_is_rejected(client):
    register_user(client, "invalid_status@example.com")
    token = login_user(client, "invalid_status@example.com")

    response = client.get(
        "/api/complaints?status=InvalidStatus",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_invalid_category_filter_is_rejected(client):
    register_user(client, "invalid_category@example.com")
    token = login_user(client, "invalid_category@example.com")

    response = client.get(
        "/api/complaints?category=InvalidCategory",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


def test_complaint_pagination(client):
    register_user(client, "pagination@example.com")
    token = login_user(client, "pagination@example.com")

    for number in range(5):
        create_complaint(
            client,
            token,
            f"Complaint {number}",
            f"Description {number}",
            "Infrastructure",
        )

    headers = {"Authorization": f"Bearer {token}"}

    page_one = client.get(
        "/api/complaints?page=1&page_size=2",
        headers=headers,
    )
    page_two = client.get(
        "/api/complaints?page=2&page_size=2",
        headers=headers,
    )
    page_three = client.get(
        "/api/complaints?page=3&page_size=2",
        headers=headers,
    )

    assert page_one.status_code == 200
    assert page_two.status_code == 200
    assert page_three.status_code == 200

    assert len(page_one.json()) == 2
    assert len(page_two.json()) == 2
    assert len(page_three.json()) == 1

    ids = [
        item["id"]
        for page in (page_one, page_two, page_three)
        for item in page.json()
    ]

    assert len(ids) == len(set(ids))


def test_pagination_rejects_invalid_values(client):
    register_user(client, "invalid_page@example.com")
    token = login_user(client, "invalid_page@example.com")

    headers = {"Authorization": f"Bearer {token}"}

    invalid_page = client.get(
        "/api/complaints?page=0",
        headers=headers,
    )
    invalid_size = client.get(
        "/api/complaints?page_size=101",
        headers=headers,
    )

    assert invalid_page.status_code == 422
    assert invalid_size.status_code == 422


def test_student_only_sees_own_filtered_complaints(client):
    register_user(client, "owner_filter@example.com")
    owner_token = login_user(client, "owner_filter@example.com")

    register_user(client, "other_filter@example.com")
    other_token = login_user(client, "other_filter@example.com")

    create_complaint(
        client, owner_token, "Owner complaint",
        "Owner description.", "Infrastructure"
    )
    create_complaint(
        client, other_token, "Other complaint",
        "Other description.", "Infrastructure"
    )

    response = client.get(
        "/api/complaints?category=Infrastructure&page=1&page_size=100",
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Owner complaint"


def test_admin_can_see_all_filtered_complaints(client):
    register_user(client, "admin_filter_student@example.com")
    student_token = login_user(client, "admin_filter_student@example.com")

    create_complaint(
        client, student_token, "Student complaint",
        "Student description.", "Infrastructure"
    )

    register_user(client, "admin_filter@example.com")
    promote_to_admin("admin_filter@example.com")
    admin_token = login_user(client, "admin_filter@example.com")

    response = client.get(
        "/api/complaints?category=Infrastructure",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_rejects_empty_query(client):
    register_user(client, "empty_search@example.com")
    token = login_user(client, "empty_search@example.com")

    response = client.get(
        "/api/complaints?search=",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
