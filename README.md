# KanMind Backend

REST API for **KanMind**, a kanban board app, built with **Django** and the
**Django REST Framework**. Users can register, create boards, invite members,
manage tasks (status, priority, assignee, reviewer, due date) and comment on
tasks.

The frontend is **not** part of this repository. It is provided by the
Developer Akademie: <https://github.com/Developer-Akademie-Backendkurs/project.KanMind>

## Tech stack

- Python 3.10+
- Django 5.2 LTS
- Django REST Framework (token authentication)
- django-cors-headers (the frontend runs on a different port)
- SQLite (local development)

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/RaphaelNeuberger/KanMind-Backend.git
cd KanMind-Backend

# 2. Create and activate a virtual environment
python -m venv env
# Windows
env\Scripts\activate
# macOS / Linux
source env/bin/activate

# 3. Install the dependencies
pip install -r requirements.txt

# 4. Create the database
python manage.py migrate

# 5. Optional: create the guest account used by the frontend guest login
python manage.py create_guest_user

# 6. Optional: create an admin account for the admin panel
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/api/`, the admin panel at
`http://127.0.0.1:8000/admin/`.

### Connecting the frontend

1. Clone the frontend repository (see link above).
2. Open it in VS Code and start `index.html` with the **Live Server**
   extension (default: `http://127.0.0.1:5500`).
3. The frontend already points to `http://127.0.0.1:8000/api/`
   (`shared/js/config.js`).

## Configuration

All settings have safe defaults for local development. For any other
environment set these environment variables:

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure development key | **Must** be set in production |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated host names |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://127.0.0.1:5500,http://localhost:5500` | Comma-separated frontend origins |

## Project structure

```
core/          Project settings and central URL routing
auth_app/      Registration, login, email check, guest user command
  api/         serializers.py, views.py, urls.py
kanban_app/    Boards, tasks and comments (models, admin)
  api/         serializers.py, views.py, urls.py, permissions.py
```

## Authentication

Token authentication is used. Registration and login return a token that
must be sent with every other request:

```
Authorization: Token <your-token>
```

Only `POST /api/registration/` and `POST /api/login/` are open endpoints.

## API endpoints

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| POST | `/api/registration/` | Create a user, returns token | open |
| POST | `/api/login/` | Log in with email + password, returns token | open |
| GET | `/api/email-check/?email=` | Find a user by email | authenticated |
| GET | `/api/boards/` | Boards the user owns or is member of | authenticated |
| POST | `/api/boards/` | Create a board | authenticated |
| GET | `/api/boards/{id}/` | Board with members and tasks | owner or member |
| PATCH | `/api/boards/{id}/` | Change title / replace member list | owner or member |
| DELETE | `/api/boards/{id}/` | Delete board incl. tasks and comments | owner |
| GET | `/api/tasks/assigned-to-me/` | Tasks where the user is assignee | authenticated |
| GET | `/api/tasks/reviewing/` | Tasks where the user is reviewer | authenticated |
| POST | `/api/tasks/` | Create a task | board member |
| PATCH | `/api/tasks/{id}/` | Update a task | board member |
| DELETE | `/api/tasks/{id}/` | Delete a task | task creator or board owner |
| GET | `/api/tasks/{id}/comments/` | Comments of a task (chronological) | board member |
| POST | `/api/tasks/{id}/comments/` | Add a comment | board member |
| DELETE | `/api/tasks/{id}/comments/{comment_id}/` | Delete a comment | comment author |

Status codes follow the specification: `201` created, `204` deleted,
`400` invalid data, `401` not authenticated, `403` no permission,
`404` not found.

## Special notes

- **Fullname vs. username:** the API works with a `fullname` and an email
  address. Internally the email is used as Django `username`; the fullname
  is split into `first_name` and `last_name` (at the first space).
- **Login by email:** users log in with email and password, the email is
  case-insensitive.
- **Board owner is always a member:** on creation and on every member update
  the owner is kept in the member list, so the owner can be assigned to tasks.
- **Task values:** `status` is one of `to-do`, `in-progress`, `review`,
  `done`; `priority` is one of `low`, `medium`, `high`.
- **Assignee and reviewer** are passed as `assignee_id` / `reviewer_id`,
  must be members of the board and may be `null`.
- **Moving tasks** to another board is not allowed (`400`); sending the
  current board id is accepted.
- **Trailing slash:** board and task detail URLs work with and without a
  trailing slash, because the frontend calls `boards/{id}` without one.
- **Guest login:** `python manage.py create_guest_user` creates the account
  `kevin@kovacsi.de` / `asdasdasd` that is hard-coded in the frontend.
- The SQLite database is excluded from Git (`.gitignore`).

## Tests

The project contains 65 API tests with 100 % coverage.

```bash
python manage.py test
coverage run manage.py test
coverage report
```

## License

Created as a training project at the Developer Akademie.
