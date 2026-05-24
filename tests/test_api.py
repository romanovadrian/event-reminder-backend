from http import client
import uuid


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


def test_user_creation_and_retrieval(client):
    register = client.post(
        "/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "phone_number": "+37369111226",
            "password": "StrongPass123",
            "timezone": "UTC",
        },
    )
    assert register.status_code == 201
    user = register.json()
    user_id = user["id"]

    login = client.post(
        "/auth/login",
        data={"username": "admin@example.com", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    get_response = client.get(f"/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_response.status_code == 200
    assert get_response.json()["email"] == "admin@example.com"

def test_user_creation(client):
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
    owner_id = owner_register.json()["id"]

    owner_login = client.post(
        "/auth/login",
        data={"username": "owner@example.com", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert owner_login.status_code == 200
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}

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

    reminder_user_association = client.post(
        f"/reminders/{reminder_id}/users",
        headers=owner_headers,
        json={"user_id": owner_id, "notify_time": "09:30:00"},
    )
    assert reminder_user_association.status_code == 201

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

    assignments = client.get(f"/reminders/{reminder_id}/users", headers=owner_headers)
    assert assignments.status_code == 200
    assert len(assignments.json()) == 1

    unassign = client.delete(f"/reminders/{reminder_id}/users/{owner_id}", headers=owner_headers)
    assert unassign.status_code == 400

    assignments_after = client.get(f"/reminders/{reminder_id}/users", headers=owner_headers)
    assert assignments_after.status_code == 200
    assert len(assignments_after.json()) == 1

    missing_unassign = client.delete(f"/reminders/{reminder_id}/users/{uuid.uuid4()}", headers=owner_headers)
    assert missing_unassign.status_code == 404

    delete_response = client.delete(f"/reminders/{reminder_id}", headers=owner_headers)
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/reminders/{reminder_id}", headers=owner_headers)
    assert get_deleted.status_code == 404


def test_debug_trigger_notification_by_association_id(client, monkeypatch):
    sent_to = []

    def fake_send_event_reminder(reminder, user):
        sent_to.append((str(reminder.id), str(user.id), user.phone_number))

    import app.main as main_module

    monkeypatch.setattr(main_module, "send_event_reminder", fake_send_event_reminder)

    owner_register = client.post(
        "/auth/register",
        json={
            "full_name": "Owner Debug",
            "email": "owner-debug@example.com",
            "phone_number": "+37369111240",
            "password": "StrongPass123",
            "timezone": "UTC",
        },
    )
    assert owner_register.status_code == 201

    owner_login = client.post(
        "/auth/login",
        data={"username": "owner-debug@example.com", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert owner_login.status_code == 200
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}

    user_response = client.post(
        "/users",
        headers=owner_headers,
        json={
            "full_name": "Debug Receiver",
            "email": "debug-receiver@example.com",
            "phone_number": "+37369111241",
            "timezone": "Europe/Chisinau",
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    reminder_response = client.post(
        "/reminders",
        headers=owner_headers,
        json={
            "title": "Debug Reminder",
            "event_type": "custom",
            "event_date": "2030-12-25",
            "remind_days_before": 0,
            "is_active": True,
        },
    )
    assert reminder_response.status_code == 201
    reminder_id = reminder_response.json()["id"]

    assignment_response = client.post(
        f"/reminders/{reminder_id}/users",
        headers=owner_headers,
        json={"user_id": user_id, "notify_time": "14:15:00"},
    )
    assert assignment_response.status_code == 201
    association_id = assignment_response.json()["id"]

    trigger_response = client.post(
        f"/debug/reminder-associations/{association_id}/trigger",
        headers=owner_headers,
    )
    assert trigger_response.status_code == 200
    body = trigger_response.json()
    assert body["association_id"] == association_id
    assert body["reminder_id"] == reminder_id
    assert body["user_id"] == user_id
    assert body["notify_time"] == "14:15:00"
    assert body["user_timezone"] == "Europe/Chisinau"
    assert body["last_notified_on"] is not None
    assert body["sms_provider"] in {"log", "twilio"}
    assert isinstance(body["twilio_credentials_present"], bool)
    assert body["triggered_at_utc"]

    assert len(sent_to) == 1
    assert sent_to[0][0] == reminder_id
    assert sent_to[0][1] == user_id
    assert sent_to[0][2] == "+37369111241"

    assignments = client.get(f"/reminders/{reminder_id}/users", headers=owner_headers)
    assert assignments.status_code == 200
    assignment = assignments.json()[0]
    assert assignment["id"] == association_id
    assert assignment["last_notified_on"] is not None
