# PlanShift

A shift-scheduling web application for hourly-employment teams — coffee shops, restaurants, retail. Managers build a schedule on an interactive calendar, the server enforces the scheduling rules, and employees see only what has been published to them.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Building a rota by hand is mostly conflict-checking: does this person hold the right position, are they already booked, did they ask for the day off, is the shift now over capacity? PlanShift moves those checks into the application layer so an invalid schedule cannot be saved in the first place.

## Features

### Manager

- **Two calendar views** — a weekly hour grid that lays out overlapping shifts side by side, and a monthly overview.
- **Draft and publish workflow** — shifts are created as drafts, visible only to managers. Publishing pushes a date range to employee calendars in one action.
- **Validated assignment** — employees are assigned to shifts inline; the server rejects any combination that breaks a scheduling rule and explains why.
- **Team and position management** — create employees, define the positions they are qualified for, and generate account credentials. The generated password is displayed exactly once and stored only as a hash.
- **Workload sidebar** — lists active employees with their scheduled hours for the current period, and highlights a person's shifts on click.

### Employee

- **Personal calendar** — a monthly view containing only published shifts the employee is assigned to.
- **Unavailability** — mark or clear a future day as unavailable with a single click; the change is saved asynchronously and immediately blocks assignment on that day.

## Scheduling rules

Every assignment passes through four checks in `backend/apps/scheduling/services.py`, inside the same transaction that saves the shift:

| Rule | Behaviour |
|---|---|
| `_check_position_match` | An employee may only be assigned to a shift for the position they hold — a barista cannot fill a head-chef shift. |
| `_check_capacity` | The number of assignees may not exceed the shift's capacity. |
| `_check_availability` | An employee marked unavailable for that date cannot be assigned. |
| `_check_no_overlap` | An employee cannot hold two shifts whose time ranges overlap; back-to-back shifts are allowed. |

If any check fails, `ValidationError` propagates out of the `transaction.atomic()` block in `use_cases.py` and the whole write is rolled back, so a shift is never left half-assigned.

## Architecture

Server-rendered Django with a vanilla-JavaScript front end — no build step, no bundler, no framework runtime.

```
├── backend/
│   ├── config/                 # settings, root URLconf, WSGI/ASGI
│   └── apps/
│       ├── accounts/           # custom User model, roles, auth, role decorators
│       └── scheduling/
│           ├── models.py       # Position, Shift, Assignment, EmployeeUnavailability
│           ├── services.py     # scheduling rules + query helpers
│           ├── use_cases.py    # transactional save/publish orchestration
│           ├── tests.py        # rule and visibility tests
│           ├── management/     # seed_demo command
│           └── views/          # employee, manager_shifts, manager_resources
├── frontend/
│   ├── templates/              # Django templates and partials
│   └── static/
│       ├── css/styles.css      # design tokens + components
│       └── js/manager-shifts/  # calendar rendering, layout, modals
├── docker/entrypoint.sh        # migrate + seed, then start the server
├── Dockerfile
├── docker-compose.yml
└── manage.py                   # wrapper so commands run from the project root
```

Views stay thin: they parse the request and render. Business rules live in `services.py`, transaction boundaries in `use_cases.py`.

### Notable implementation details

- **State injection instead of a load-time API round trip.** Django serialises the initial shift and employee data into `<script type="application/json">` blocks and `data-*` attributes. The client reads them synchronously on boot, so the calendar paints without a fetch.
- **Greedy lane placement for overlapping shifts.** `manager-shifts/core.js` sorts a day's shifts by start time and drops each into the first lane whose previous shift has ended, allocating a new lane only when none is free. Lane index and count become absolute CSS coordinates on the chip.
- **Deterministic position colours.** Chip colours are derived from the position ID (`hue = (id * 47) % 360`) rather than stored in the database, so a new position is immediately distinguishable without a migration or a colour picker. The calendar legend lists only the positions present in the visible period.
- **Async unavailability toggle.** Employee day toggles go through the Fetch API and return a `JsonResponse`; only the affected cell re-renders, and the server re-validates the date on every call.

## Data model

```mermaid
erDiagram
    Position ||--o{ User : "qualifies (SET_NULL)"
    Position ||--o{ Shift : "required for (PROTECT)"
    User ||--o{ Shift : "created by (PROTECT)"
    User ||--o{ Assignment : "assigned (CASCADE)"
    Shift ||--o{ Assignment : "staffed by (CASCADE)"
    User ||--o{ EmployeeUnavailability : "declares (CASCADE)"

    Position {
        int id PK
        string name UK
        bool is_active
    }
    User {
        int id PK
        string username
        string role
        string employee_id UK
        int position_id FK
    }
    Shift {
        int id PK
        date date
        time start_time
        time end_time
        int capacity
        string status
        int position_id FK
        int created_by FK
    }
    Assignment {
        int id PK
        int shift_id FK
        int employee_id FK
    }
    EmployeeUnavailability {
        int id PK
        int employee_id FK
        date date
    }
```

Deletion behaviour is chosen per relationship: removing a position leaves employee accounts intact (`SET_NULL`) but is blocked while shifts still require it (`PROTECT`). Two unique constraints keep the schedule coherent at the database level — one employee per shift (`unique_employee_per_shift`) and one unavailability record per employee per day (`unique_employee_unavailability_day`).

## Security

- **Object-level authorisation on shifts.** Manager endpoints resolve a shift with `get_object_or_404(Shift.objects, pk=shift_id, created_by=request.user)`, so guessing another manager's shift ID returns 404 rather than granting access. Positions and employees are intentionally shared across managers as a single organisational directory.
- **Role-gated views.** `manager_required` / `employee_required` decorators guard every view; unauthenticated access redirects to the login page.
- **Credential handling.** Generated passwords are held in the session only long enough to be shown once, and persisted solely as a PBKDF2 hash.
- **Standard Django protections** are left in place — CSRF middleware, template auto-escaping, ORM-parameterised queries, clickjacking headers. Fetch calls read the CSRF token at runtime and send it as `X-CSRFToken`.

`SECRET_KEY`, `DEBUG` and `ALLOWED_HOSTS` are read from the environment; the built-in defaults are development-only.

## Getting started

### With Docker (recommended)

```bash
git clone https://github.com/DT-sudo/planshift.git
cd planshift
docker compose up
```

That is the whole setup. The container applies migrations and seeds a month of demo
data on first boot, so <http://127.0.0.1:8000/> opens on a populated schedule.

The image runs Django's development server with `DEBUG` enabled so the one-click demo
logins work — it is a demo environment, not a production image.

### With a local Python environment

Requires **Python 3.12+**.

```bash
git clone https://github.com/DT-sudo/planshift.git
cd planshift

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo         # optional: demo positions, staff and shifts
python manage.py runserver
```

The app is served at <http://127.0.0.1:8000/>.

### Demo accounts

While `DEBUG` is on, two demo accounts are available so the app can be explored without
any setup:

| Role | Username | Password |
|---|---|---|
| Manager | `manager_demo@example.com` | `demo12345!` |
| Employee | `employee_demo@example.com` | `demo12345!` |

For your own manager account, use `python manage.py createsuperuser`.

### Configuration

All settings fall back to development defaults; override through the environment as needed.

| Variable | Default |
|---|---|
| `DEBUG` | `1` |
| `SECRET_KEY` | development placeholder |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` |
| `TIME_ZONE` | `UTC` |
| `DB_ENGINE` | `django.db.backends.sqlite3` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | SQLite defaults |
| `SEED_DEMO_DATA` | `1` (Docker entrypoint only) |


## Tests

```bash
python manage.py test apps
```

The suite covers the four scheduling rules — including the boundary case that back-to-back shifts are permitted while overlapping ones are not — and the draft/published visibility split between the manager and employee views.

## License

MIT — see [LICENSE](LICENSE).
