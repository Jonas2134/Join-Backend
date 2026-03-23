# Join Backend

**Join Backend** is the Backend service for Join, a Kanban board application. It is built using Django and Django REST Framework, providing a robust API for managing boards, lists, cards, and user authentication.

---

## Features

- User authentication and authorization with JWT and http-only cookies
- CRUD operations for boards, lists, and cards
- User management and profile handling
- RESTful API design

---

## Tech Stack

- **Framework:** Django 5.2 & Django REST Framework 3.16
- **Authentication:** SimpleJWT with HTTP-only cookies
- **Database:** PostgreSQL (production) / SQLite (development)
- **WSGI Server:** Gunicorn
- **Containerization:** Docker & Docker Compose

---

## Project Structure

```
$PROJECT_ROOT/
├── core/                        # Django project configuration
│   ├── settings.py              # Main settings
│   ├── urls.py                  # Root URL routing
│   ├── api_urls.py              # API URL aggregation
│   ├── authentication.py        # Custom cookie-based JWT auth
│   └── permissions.py           # Shared permission classes
├── auth_app/                    # Authentication & user model
│   ├── models.py                # CustomUserProfile (extends AbstractUser)
│   ├── api/
│   │   ├── views.py             # Register, Login, Logout, Guest login, etc.
│   │   ├── serializers.py
│   │   └── urls.py
│   └── management/commands/
│       └── cleanup_guests.py    # Remove stale guest accounts
├── board_app/                   # Board management
│   ├── models.py                # Board model
│   └── api/
│       ├── views.py             # Board CRUD + leave endpoint
│       ├── serializers.py
│       └── urls.py
├── column_app/                  # Column / list management
│   ├── models.py                # Column model (with WIP limits)
│   └── api/
│       ├── views.py             # Column CRUD
│       ├── serializers.py
│       └── urls.py
├── task_app/                    # Task / card management
│   ├── models.py                # Task model
│   └── api/
│       ├── views.py             # Task CRUD
│       ├── serializers.py
│       └── urls.py
├── contact_and_profile_app/     # Profiles & contacts
│   └── api/
│       ├── views.py             # Profile, user list, contacts
│       ├── serializers.py
│       └── urls.py
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
└── manage.py
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- pip

### Local Development

```bash
# Clone the repository
git clone https://github.com/<your-username>/join-backend.git
cd join-backend

# Create a virtual environment
python -m venv .venv
```

Activate the virtual environment:

| OS | Command |
|---|---|
| Linux / macOS | `source .venv/bin/activate` |
| Windows (CMD) | `.venv\Scripts\activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |

```bash
# Install dependencies
pip install -r requirements.txt

# Create a .env file (see Environment Variables below)
cp .env.example .env          # Linux / macOS
copy .env.example .env        # Windows (CMD)

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

### Docker

```bash
# Build and start with Docker Compose
docker-compose up --build
```

This starts a PostgreSQL database and the Django application on port `8000`.

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `SECRET_KEY` | Django secret key | `django-insecure-change-me` |
| `DEBUG` | Enable debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed CORS origins | `http://localhost:5173` |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials in CORS | `True` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted CSRF origins | `http://localhost:5173` |
| `DB_ENGINE` | Database engine (`postgresql` or omit for SQLite) | `postgresql` |
| `DB_NAME` | Database name | `join_db` |
| `DB_USER` | Database user | `join_user` |
| `DB_PASSWORD` | Database password | `join_password` |
| `DB_HOST` | Database host | `db` |
| `DB_PORT` | Database port | `5432` |

---

## API Endpoints

All endpoints are prefixed with `/api/`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Register a new user |
| POST | `/api/login/` | Log in and receive JWT cookies |
| POST | `/api/logout/` | Log out and blacklist the refresh token |
| POST | `/api/token/refresh/` | Refresh the access token |
| POST | `/api/guest-login/` | Log in as a temporary guest user |
| GET | `/api/auth/status/` | Check current authentication status |
| POST | `/api/password/change/` | Change the current user's password |

### Boards

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/boards/` | List all boards the user is a member of |
| POST | `/api/boards/` | Create a new board |
| GET | `/api/boards/<id>/` | Get board details with columns and tasks |
| PATCH | `/api/boards/<id>/` | Update board (owner only) |
| DELETE | `/api/boards/<id>/` | Delete board (owner only) |
| POST | `/api/boards/<id>/leave/` | Leave a board as a member |

### Columns

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/boards/<board_id>/columns/` | List all columns of a board |
| POST | `/api/boards/<board_id>/columns/` | Create a new column |
| GET | `/api/columns/<id>/` | Get column details |
| PATCH | `/api/columns/<id>/` | Update column (name, position, WIP limit) |
| DELETE | `/api/columns/<id>/` | Delete a column |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/columns/<column_id>/tasks/` | List all tasks in a column |
| POST | `/api/columns/<column_id>/tasks/` | Create a new task |
| GET | `/api/tasks/<id>/` | Get task details |
| PATCH | `/api/tasks/<id>/` | Update task (move, assign, edit) |
| DELETE | `/api/tasks/<id>/` | Delete a task |

### Profiles & Contacts

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/profile/` | Get the current user's profile |
| PATCH | `/api/profile/` | Update the current user's profile |
| GET | `/api/users/` | List users (searchable, excludes own contacts) |
| GET | `/api/users/<id>/` | Get a user's profile |
| POST | `/api/users/<id>/add-contact/` | Add a user to contacts |
| GET | `/api/contacts/` | List all contacts |
| DELETE | `/api/contacts/<id>/` | Remove a contact |

---

## Authentication

Authentication is handled via **JWT tokens stored in HTTP-only cookies**, making them inaccessible to JavaScript and protecting against XSS attacks.

- **Login** sets `access_token` and `refresh_token` as HTTP-only cookies
- **Token refresh** rotates the refresh token and blacklists the old one
- **Remember me** extends the cookie lifetime to 30 days
- **Guest login** creates a temporary user account that is automatically cleaned up after inactivity

---

## Management Commands

### cleanup_guests

Removes guest user accounts that have been inactive beyond a specified threshold.

```bash
# Delete guests inactive for 24 hours (default)
python manage.py cleanup_guests

# Delete guests inactive for 48 hours
python manage.py cleanup_guests --hours 48

# Preview deletions without executing
python manage.py cleanup_guests --dry-run
```
