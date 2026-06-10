# mini-bank — interactive mBank workshop demo

Full-stack banking-flavoured demo for the mBank agentic-best-practices workshop.
FastAPI backend + React/MUI frontend + Postgres (or SQLite). Dual-version:
`main` branch = attendee starting state with planted bugs; `solutions` branch =
fixes applied.

## Quickstart

```bash
# Run the full stack with Postgres
make dev

# Or with SQLite (single container DB)
make dev-sqlite

# Load demo data (run after backend is up — in a separate terminal)
make seed

# Open in browser
open http://localhost:5173
```

## Demo accounts

| Email | Password | Role |
|---|---|---|
| customer1@minibank.pl ... customer32@minibank.pl | Demo1234! | klient (PL) |
| ukr1@minibank.pl ... ukr8@minibank.pl | Demo1234! | klient (UA) |
| agent.helpdesk@minibank.pl | Agent1234! | agent |
| agent.branch@minibank.pl | Agent1234! | agent |
| agent.supervisor@minibank.pl | Agent1234! | supervisor |

## Tests

```bash
make test       # backend pytest + frontend build
make test-be    # backend only
```

Expected on the starting tree: **11 xfail** (planted BUG-01..10, BUG-05 has two)
plus 1 known XPASS (the e2e race variant of BUG-01 is timing-flaky — use the unit
variant as the gate). Run `pytest -m planted` to list only the planted traps.
Expected on `solutions` branch: 0 xfail, all pass.

## Planted items

All ten bugs are present and active (xfail) on the starting tree. See
`CODE_REVIEW.md` for the full assessment and `file:line` locations.

| ID | File | Block |
|---|---|---|
| BUG-01 | `backend/src/minibank/transfers/concurrent_transfer.py` (race; `transfer_service` delegates) | concurrency |
| BUG-02 | `backend/src/minibank/timezone_check.py` | timezone correctness |
| BUG-03 | `backend/src/minibank/interest.py` | money math |
| BUG-04 | `backend/src/minibank/fraud_score.py` | robustness |
| BUG-05 | audit_log migration (no immutability trigger) | audit integrity |
| BUG-06 | `backend/src/minibank/services/access_grant_service.py` (no `expires_at` check) | authz |
| BUG-07 | `backend/src/minibank/services/audit_service.py` (PESEL plaintext) | data privacy |
| BUG-08 | `backend/src/minibank/services/sca_service.py` (SCA dynamic-linking bypass) | PSD2 / SCA |
| BUG-09 | `backend/src/minibank/middleware/idempotency.py` (cache by key only) | idempotency |
| BUG-10 | `backend/src/minibank/middleware/step_up.py` (`last_login` vs `last_step_up`) | step-up auth |
| REF-01 | `backend/src/minibank/fraud_score.py` (god function) | refactoring |

M4 (dema 14–23) uses BUG-03, BUG-01, BUG-08, BUG-09, BUG-06 + 5 features — see
`LAB_BACKLOG.md`.

## Structure

```
mini-bank/
├── backend/         FastAPI + SQLAlchemy + Alembic
├── frontend/        React + Vite + TypeScript + MUI
├── docker-compose.yml
└── Makefile
```

## Stack

- **Backend**: Python 3.12 · FastAPI 0.115 · SQLAlchemy 2 · Alembic · Pydantic v2 · bcrypt · PyJWT · Faker[pl_PL]
- **Frontend**: React 19 · Vite · TypeScript · Material-UI v6 · react-router v7 · axios
- **Storage**: Postgres 16 (prod) / SQLite (dev override)
- **Deploy** (v3+): Terraform → GCP Cloud Run + Cloud SQL + Secret Manager
