# Event Reminder (Python + PostgreSQL)

Simple reminder API for birthdays, anniversaries, and custom events.

## Features
- FastAPI CRUD API for users, reminders, and reminder assignments
- PostgreSQL persistence with SQLAlchemy
- Background polling scheduler that triggers reminders on schedule
- Timezone-aware reminder evaluation per user

## Stack
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL 16

## Quick Start

1. Start PostgreSQL:

```bash
docker compose up -d db
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. Configure environment:

```bash
cp .env.example .env
```

5. Run the app:

```bash
uvicorn app.main:app --reload
```

6. Open API docs:
- http://127.0.0.1:8000/docs

## Example User Payload

```json
{
  "full_name": "Alex Popescu",
  "email": "alex@example.com",
  "phone_number": "+37369111222",
  "timezone": "Europe/Chisinau",
  "is_active": true
}
```

## Example Reminder Payload

```json
{
  "title": "Alex Birthday",
  "event_type": "birthday",
  "event_date": "1995-10-10",
  "remind_days_before": 2,
  "notes": "Buy a gift",
  "is_active": true
}
```

## Example Assignment Payload

```json
{
  "user_id": "b5af0139-90e8-4fd0-bf2d-17eac54b237e",
  "notify_time": "09:00:00"
}
```

## Notes
- By default reminder triggers are logged to app output.

## JWT Authentication

1. Configure JWT settings in `.env`:

```env
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

2. Register a user:
- `POST /auth/register`

3. Login and obtain bearer token:
- `POST /auth/login`
- Use `application/x-www-form-urlencoded` payload with:
  - `username` (email)
  - `password`

4. Use token for protected routes (`/users`, `/reminders`):

```http
Authorization: Bearer <access_token>
```

5. Logout:
- `POST /auth/logout`
- Current implementation is stateless logout (client discards token).

## SMS Reminders (Twilio)

1. Create a Twilio account and get:
- `Account SID`
- `Auth Token`
- A Twilio phone number capable of SMS

2. Update your `.env`:

```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+12025550123
```

3. Reinstall dependencies if needed:

```bash
pip install -e .
```

4. Start the app and keep it running:

```bash
uvicorn app.main:app --reload
```

5. Create users, create a reminder, then assign users to the reminder.

Core endpoint flow:
- `POST /users`
- `POST /reminders`
- `POST /reminders/{reminder_id}/users`
- `GET /reminders/{reminder_id}/users`

6. Create a reminder due now (or a few minutes from now) and keep the app running to test delivery.

Important:
- For Twilio trial accounts, the destination number must be verified in Twilio first.
- Use E.164 phone format (for example `+373XXXXXXXX`).
- If `SMS_PROVIDER=twilio` but credentials are missing, the app falls back to log output.

## Export API YAML For Frontend Agent

Generate OpenAPI YAML from the current backend routes:

```bash
export-openapi-yaml
```

Default output path:
- `docs/api/openapi.yaml`

Custom output path:

```bash
export-openapi-yaml --output docs/api/frontend-agent-spec.yaml
```

Suggested frontend-agent flow:
1. Run `export-openapi-yaml` after backend endpoint changes.
2. Point your frontend agent to the generated YAML file.
3. Regenerate frontend API client/types from this YAML to keep contracts in sync.
