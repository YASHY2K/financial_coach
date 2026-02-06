# Database Knowledge Transfer (KT) Document

## 1. High-Level Overview

### Purpose

The database layer serves as the persistent storage foundation for the Smart Financial Coach application. It stores user profiles, financial transactions (2+ years of synthetic data), and AI-generated insights. The DB is designed with a dual-access pattern: full read-write access for the backend application and restricted read-only access for AI agents to ensure data safety during natural language query execution.

### Architecture

- **Pattern**: Traditional relational database with ORM abstraction
- **Access Model**: Dual-user system (admin + read-only)
- **ORM Strategy**: SQLAlchemy 2.0 with async/await support for the application layer, synchronous access for LangChain AI tools
- **Initialization**: Docker entrypoint scripts handle schema creation and user provisioning

### Tech Stack

- **Database**: PostgreSQL 15 (Alpine Linux container)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Migration Tool**: None currently (schema managed via `Base.metadata.create_all`)
- **Seeding**: Custom async seeder using Faker library
- **Connection Pooling**: Built-in SQLAlchemy pooling (10 base connections, 20 overflow)

---

## 2. Folder Structure & Key Files

```
db/
└── init-read-only-user.sh          # Creates read-only DB user for AI agents

app/src/coach/
├── database.py                      # Core: Engine setup, session factory, Base class
├── models.py                        # Core: SQLAlchemy ORM models (User, Transaction, Insight)
├── seeder.py                        # Generates 2 years of synthetic financial data
└── schema.py                        # Pydantic schemas for API validation (not DB schema)

docker-compose.yml                   # DB service definition with health checks
.env / .env.example                  # Database credentials and configuration
```

**Key File Annotations:**

- **`database.py`**: Defines both async engine (for FastAPI) and sync engine (for LangChain SQL tools). Contains the singleton `get_sync_db()` function.
- **`models.py`**: Three core tables with relationships. Uses SQLAlchemy 2.0 `Mapped` type hints.
- **`init-read-only-user.sh`**: Bash script executed on first DB startup. Creates a restricted user that can only SELECT.
- **`seeder.py`**: Run manually or via Docker to populate demo data. Generates subscriptions, income, and daily spending patterns.

---

## 3. Key Logic & Data Flow

### Core Flows

#### A. Database Initialization (First Run)

1. Docker Compose starts `postgres:15-alpine` container
2. PostgreSQL runs scripts in `/docker-entrypoint-initdb.d/` (mounted from `db/init-read-only-user.sh`)
3. Script creates:
   - Read-only role with `SELECT` privileges
   - Default privileges for future tables
4. Backend starts and calls `Base.metadata.create_all()` via `seeder.py` to create tables

#### B. Application Data Access (FastAPI Backend)

```
FastAPI Request
  → Dependency Injection: get_db()
    → AsyncSessionLocal() creates session
      → SQLAlchemy executes async query
        → PostgreSQL (full read-write user)
          → Response returned to API
            → Session closed in finally block
```

#### C. AI Agent Data Access (LangChain SQL Tools)

```
User Chat Message
  → LangGraph Supervisor
    → SQL Expert Agent invoked
      → get_sync_db() returns singleton SQLDatabase
        → Synchronous query executed
          → PostgreSQL (read-only user)
            → Results formatted as natural language
              → Returned to chat interface
```

### State Management

- **Schema State**: Managed by SQLAlchemy's `Base.metadata`. No formal migration system (Alembic not implemented).
- **Connection State**: Pooled connections with pre-ping health checks to handle stale connections.
- **Transaction State**: Async sessions use context managers (`async with`) to ensure proper commit/rollback.

---

## 4. Configuration & Environment

### Required Environment Variables (`.env`)

```bash
# Primary Database User (Full Access)
POSTGRES_USER=admin_user              # Used by backend for CRUD operations
POSTGRES_PASSWORD=secure_password     # Strong password required
POSTGRES_DB=financial_coach           # Database name
POSTGRES_PORT=5432                    # Default PostgreSQL port

# Read-Only User (AI Agent Access)
POSTGRES_READONLY_USER=ai_reader      # Restricted to SELECT only
POSTGRES_READONLY_PASSWORD=read_pass  # Separate credentials for safety
```

### Connection String Construction

- **Async (Backend)**: `postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}`
- **Sync (AI Tools)**: `postgresql+psycopg2://{POSTGRES_READONLY_USER}:{POSTGRES_READONLY_PASSWORD}@db:5432/{POSTGRES_DB}`

These are built in `app/src/coach/config.py` (referenced but not shown in files).

### Hardcoded Constants

- **Pool Size**: 10 base connections, 20 max overflow (in `database.py`)
- **Seeder Date Range**: 730 days (2 years) of transaction history
- **Demo Username**: `demo_user` (hardcoded in seeder)

---

## 5. "Gotchas" & Technical Debt

### Tricky Parts

1. **Dual Engine Pattern**
   - The app maintains TWO SQLAlchemy engines: one async (for FastAPI) and one sync (for LangChain).
   - **Why**: LangChain's SQL tools don't support async operations yet.
   - **Risk**: Connection pool exhaustion if both systems query heavily under load.

2. **No Migration System**
   - Schema changes require manual SQL or dropping/recreating tables.
   - **Workaround**: Currently using `docker-compose down -v` to reset (destroys all data).
   - **Impact**: Not production-ready. Alembic should be added before real deployment.

3. **Read-Only User Timing**
   - The `init-read-only-user.sh` script runs BEFORE tables exist.
   - The `ALTER DEFAULT PRIVILEGES` ensures future tables get read permissions.
   - **Gotcha**: If you manually create tables outside the ORM, the read-only user won't have access unless you re-grant.

4. **Seeder Idempotency**
   - The seeder checks for existing `demo_user` but doesn't handle partial failures well.
   - If seeding crashes mid-transaction, you may have a user with no transactions.

### Known Issues

- **No Alembic Migrations**: Schema versioning is manual. Adding/removing columns requires custom SQL or DB reset.
- **Hardcoded Demo User**: The seeder always creates `demo_user`. Multi-user support requires refactoring.
- **Test Coverage**: Only 3 tests exist (per `TEST_COVERAGE.md`). No DB-specific integration tests for edge cases.
- **Connection String Security**: Database URLs are built from env vars but not validated. Malformed values cause cryptic startup errors.

### Workarounds

- **Backend Restart After Seeding**: The AI agent caches table metadata. After seeding, restart the backend container to refresh:
  ```bash
  docker-compose restart backend
  ```

---

## 6. Development Workflow

### Commands

#### Initial Setup

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your credentials
# (Set POSTGRES_USER, POSTGRES_PASSWORD, etc.)

# 3. Start database
docker-compose up -d db

# 4. Wait for health check (automatic via depends_on)
docker-compose ps  # Check status
```

#### Seeding Data

```bash
# Option A: Run seeder inside backend container
docker-compose exec backend uv run python -m coach.seeder

# Option B: Run seeder standalone (if backend not running)
cd app
uv run python -m coach.seeder

# Verify data
docker-compose exec db psql -U admin_user -d financial_coach -c "SELECT COUNT(*) FROM transactions;"
```

#### Database Inspection

```bash
# Connect to PostgreSQL CLI
docker-compose exec db psql -U admin_user -d financial_coach

# Useful queries
\dt                          # List tables
\d users                     # Describe users table
SELECT * FROM users LIMIT 5; # Sample data
\du                          # List database roles
```

#### Reset Database (Nuclear Option)

```bash
# WARNING: Destroys all data and volumes
docker-compose down -v
docker-compose up -d
# Re-run seeder after this
```

#### Testing Read-Only User

```bash
# Connect as read-only user
docker-compose exec db psql -U ai_reader -d financial_coach

# Try a SELECT (should work)
SELECT COUNT(*) FROM transactions;

# Try an INSERT (should fail with permission error)
INSERT INTO users (username) VALUES ('hacker');
```

#### Logs & Debugging

```bash
# View database logs
docker-compose logs -f db

# View SQLAlchemy query logs (echo=True in database.py)
docker-compose logs -f backend | grep "SELECT"
```

### Local Development Without Docker

If you want to run PostgreSQL locally (not recommended but possible):

1. Install PostgreSQL 15
2. Create database: `createdb financial_coach`
3. Run `init-read-only-user.sh` manually (replace env vars)
4. Update `.env` to use `localhost` instead of `db`
5. Run seeder: `cd app && uv run python -m coach.seeder`

---

## Quick Reference

| Task             | Command                                                        |
| ---------------- | -------------------------------------------------------------- |
| Start DB         | `docker-compose up -d db`                                      |
| Seed Data        | `docker-compose exec backend uv run python -m coach.seeder`    |
| Connect to DB    | `docker-compose exec db psql -U admin_user -d financial_coach` |
| View Logs        | `docker-compose logs -f db`                                    |
| Reset Everything | `docker-compose down -v && docker-compose up -d`               |
| Check Health     | `docker-compose ps` (look for "healthy" status)                |

---

## Schema Quick Reference

### Users Table

- `id_` (PK), `username` (unique), `financial_goals` (text), `created_at`
- Relationships: `transactions` (1:N), `insights` (1:N)

### Transactions Table

- `id_` (PK), `user_id` (FK), `amount` (Decimal), `transaction_type` (debit/credit)
- `merchant`, `date`, `category`, `is_subscription`, `description`
- Relationship: `owner` (N:1 to User)

### Insights Table

- `id_` (PK), `user_id` (FK), `title`, `message`, `type`, `created_at`, `is_read`
- Relationship: `owner` (N:1 to User)

---

**Last Updated**: February 3, 2026  
**Maintainer**: Backend Team  
**Questions?** Check `DESIGN_DOC.md` for architecture context or `app/README.md` for backend setup.
