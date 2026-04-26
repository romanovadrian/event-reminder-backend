def test_auth_register_login_logout_and_protected_routes(client):
    unauthorized_users = client.get("/users")
    assert unauthorized_users.status_code == 401

    register = client.post(
        "/auth/register",
        json={
            "full_name": "Alex Popescu",
            "email": "alex@example.com",
            "phone_number": "+37369111222",
            "password": "StrongPass123",
            "timezone": "Europe/Chisinau",
            "is_active": True,
        },
    )
    assert register.status_code == 201
    user = register.json()
    user_id = user["id"]

    login = client.post(
        "/auth/login",
        data={"username": "alex@example.com", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    list_response = client.get("/users", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/users/{user_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["phone_number"] == "+37369111222"

    logout = client.post("/auth/logout", headers=headers)
    assert logout.status_code == 200


def test_auth_validation_failures(client):
    bad_phone = client.post(
        "/auth/register",
        json={
            "full_name": "Bad Phone",
            "email": "bad-phone@example.com",
            "phone_number": "069111222",
            "password": "StrongPass123",
            "timezone": "Europe/Chisinau",
        },
    )
    assert bad_phone.status_code == 422

    bad_timezone = client.post(
        "/auth/register",
        json={
            "full_name": "Bad TZ",
            "email": "bad-tz@example.com",
            "phone_number": "+37369111223",
            "password": "StrongPass123",
            "timezone": "Moon/Base",
        },
    )
    assert bad_timezone.status_code == 422

    login_fail = client.post(
        "/auth/login",
        data={"username": "bad-tz@example.com", "password": "WrongPass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_fail.status_code == 401


def test_reminder_crud_and_assignments(client):
    owner_register = client.post(
        "/auth/register",
        json={
            "full_name": "Owner User",
            "email": "owner@example.com",
            "phone_number": "+37369111220",
            "password": "StrongPass123",
            "timezone": "UTC",
        },
    )
    assert owner_register.status_code == 201

    owner_login = client.post(
        "/auth/login",
        data={"username": "owner@example.com", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert owner_login.status_code == 200
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}

    user_1 = client.post(
        "/users",
        headers=owner_headers,
        json={
            "full_name": "User One",
            "email": "user1@example.com",
            "phone_number": "+37369111224",
            "timezone": "UTC",
        },
    )
    assert user_1.status_code == 201
    user_1_id = user_1.json()["id"]

    user_2 = client.post(
        "/users",
        headers=owner_headers,
        json={
            "full_name": "User Two",
            "email": "user2@example.com",
            "phone_number": "+37369111225",
            "timezone": "Europe/Chisinau",
        },
    )
    assert user_2.status_code == 201
    user_2_id = user_2.json()["id"]

    reminder_response = client.post(
        "/reminders",
        headers=owner_headers,
        json={
            "title": "Wedding Anniversary",
            "event_type": "anniversary",
            "event_date": "2015-06-10",
            "remind_days_before": 3,
            "notes": "Buy flowers",
            "is_active": True,
        },
    )
    assert reminder_response.status_code == 201
    reminder_id = reminder_response.json()["id"]

    list_response = client.get("/reminders", headers=owner_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/reminders/{reminder_id}", headers=owner_headers)
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Wedding Anniversary"

    patch_response = client.patch(
        f"/reminders/{reminder_id}",
        headers=owner_headers,
        json={
            "title": "Wedding Anniversary Updated",
            "is_active": False,
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Wedding Anniversary Updated"

    assign_1 = client.post(
        f"/reminders/{reminder_id}/users",
        headers=owner_headers,
        json={"user_id": user_1_id, "notify_time": "09:30:00"},
    )
    assert assign_1.status_code == 201

    assign_2 = client.post(
        f"/reminders/{reminder_id}/users",
        headers=owner_headers,
        json={"user_id": user_2_id, "notify_time": "08:45:00"},
    )
    assert assign_2.status_code == 201

    duplicate_assign = client.post(
        f"/reminders/{reminder_id}/users",
        headers=owner_headers,
        json={"user_id": user_1_id, "notify_time": "09:30:00"},
    )
    assert duplicate_assign.status_code == 201

    assignments = client.get(f"/reminders/{reminder_id}/users", headers=owner_headers)
    assert assignments.status_code == 200
    assert len(assignments.json()) == 2

    unassign = client.delete(f"/reminders/{reminder_id}/users/{user_1_id}", headers=owner_headers)
    assert unassign.status_code == 204

    assignments_after = client.get(f"/reminders/{reminder_id}/users", headers=owner_headers)
    assert assignments_after.status_code == 200
    assert len(assignments_after.json()) == 1

    missing_unassign = client.delete(f"/reminders/{reminder_id}/users/{user_1_id}", headers=owner_headers)
    assert missing_unassign.status_code == 404

    delete_response = client.delete(f"/reminders/{reminder_id}", headers=owner_headers)
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/reminders/{reminder_id}", headers=owner_headers)
    assert get_deleted.status_code == 404
