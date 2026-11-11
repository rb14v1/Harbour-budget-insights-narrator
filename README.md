# Budget Insights Narrator

A personal budget tracker that turns a month's transactions into a plain-
English narrative. Single user role - every logged-in user only ever sees
their own categories, transactions and insights. React + Vite + TypeScript
frontend, Django REST Framework backend, **plain PostgreSQL** (no
pgvector, no vector database of any kind - the only AI-specific piece is a
single OpenAI chat-completion call). No Celery/Redis - nothing async to
run or desync.

## Data model

- **User** - custom user model, `email` as `USERNAME_FIELD`, a single
  `full_name` field (no username, no first/last name split). Single role.
- **Category** - `user`, `name`, unique `(user, name)`.
- **Transaction** - `user`, `category`, `transaction_type`
  (`income`/`expense`), `amount` (always stored positive - the sign/meaning
  comes from `transaction_type`), `description`, `transaction_date`,
  `created_at`.
- **MonthlyInsight** - `user`, `month` (always the first day of the month,
  e.g. `2026-11-01` means "November 2026"), `narrative`, `generated_at`,
  unique `(user, month)`. Regenerating an insight replaces its narrative in
  place rather than creating a second row.

## AI feature

`apps/insights/services.py` computes plain Postgres/Django aggregates from
real `Transaction` rows - `compute_category_totals()` and
`compute_month_summary()` (total income, total expenses, this month's
expense breakdown by category, and the same breakdown for the prior
month). `apps/common/ai.py` turns those aggregates into a narrative
paragraph via a single OpenAI chat-completion call. The AI never sees
individual transactions, only the aggregates Python/Postgres already
computed.

- **Real mode** (`OPENAI_API_KEY` set): calls the OpenAI chat completions
  API with `OPENAI_CHAT_MODEL` (default **`gpt-5.4-mini`** - deliberately
  different from the `gpt-5.6-sol` default used by several sibling apps in
  this workspace).
- **Stub mode** (`OPENAI_API_KEY` unset - the default for local dev/tests):
  a fully offline, deterministic narrative built with string templating
  from the same aggregates (sorted internally so output never depends on
  input dict ordering). Same inputs always produce the exact same
  narrative, byte-for-byte - no network, no cost, nothing to flake in
  tests.

## REST API

- `POST /api/auth/register/`, `POST /api/auth/login/` (JWT),
  `POST /api/auth/refresh/`, `POST /api/auth/logout/`
- `GET /api/users/me/`
- `/api/categories/` - list/create/retrieve/update/delete, scoped to the
  authenticated user
- `/api/transactions/` - list/create/retrieve/update/delete, scoped to the
  authenticated user, `?month=YYYY-MM`, `?category=`, `?transaction_type=`
- `GET /api/insights/{year}/{month}/` - computed aggregates for that month
  plus the stored narrative, if any. Always 200; `narrative` is `null`
  until generated.
- `POST /api/insights/{year}/{month}/generate/` - recomputes aggregates
  fresh and creates/replaces the `MonthlyInsight` for that user+month.

Every endpoint scopes its queryset to `request.user` - there is no
cross-user access even by guessing another user's object ID.

## Running locally with Docker (Postgres)

```bash
cp .env.example .env
docker compose up --build
```

Backend on http://localhost:8000, frontend on http://localhost:5173.

## Running the backend without Docker

This machine already has native Postgres 18 running on `localhost:5432`
with the `budget_insights_narrator` role/database provisioned, and
`backend/.env` is set up to use it directly (`USE_SQLITE=False`):

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt

python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test
python manage.py runserver
```

Demo login (seeded by a data migration, idempotent via `get_or_create`):
**demo@example.com / demo12345** - comes with 7 categories, ~48
transactions spread across the last 3 months, and a generated
`MonthlyInsight` for the most recent 2 months.

### DEV-ONLY SQLite override

For running on a machine without Postgres/Docker, set `USE_SQLITE=True`
(see `backend/config/settings/base.py`) to fall back to local SQLite for
`manage.py check`/`makemigrations`/`test`. **Never set this in
docker-compose or production** - `backend/.env` in this checkout is
already set to `USE_SQLITE=False` to use the real Postgres instance above.

## Running the frontend

```bash
cd frontend
npm install
npm run dev      # dev server on :5173
npm run build    # production build (tsc -b && vite build)
```

Set `VITE_API_BASE_URL` (see `frontend/.env.example`) if the backend isn't
at `http://localhost:8000/api`.

## Auth trade-off (dev-only)

The access token is kept in memory only; the refresh token is kept in
`localStorage` and the client refreshes on a 401. A real deployment would
instead issue the refresh token as an httpOnly cookie from the backend -
this simplified pattern (same as the sibling apps in this workspace) is a
deliberate trade-off for a small demo app, not a recommendation for
production.
