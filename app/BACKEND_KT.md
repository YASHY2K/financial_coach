# Backend Knowledge Transfer (KT) Document

## 1. High-Level Overview

### Purpose

The backend is a FastAPI-based REST API that serves as the intelligence layer for the Smart Financial Coach application. It orchestrates AI agents (via LangGraph) to analyze financial data, provides dashboard analytics endpoints, and manages proactive insight generation. The backend acts as the bridge between the PostgreSQL database and the React frontend, handling all business logic, AI orchestration, and data transformations.

### Architecture

- **Pattern**: Layered architecture with AI agent orchestration
  - **API Layer**: FastAPI endpoints (REST)
  - **Agent Layer**: LangGraph supervisor-worker pattern (3 agents)
  - **Service Layer**: Business logic (InsightService)
  - **Data Layer**: SQLAlchemy ORM with async/sync dual engines
- **AI Orchestration**: Supervisor delegates to SQL Expert and Data Analyst agents
- **State Management**: In-memory session storage (dict) for chat history + LangGraph MemorySaver for agent state

### Tech Stack

- **Framework**: FastAPI (latest)
- **Language**: Python 3.12+
- **Package Manager**: uv (Astral's fast Python package manager)
- **AI Orchestration**: LangGraph + LangChain
- **LLM**: Google Gemini 2.5 Flash (via `langchain-google-genai`)
- **Database**: PostgreSQL 15 (via SQLAlchemy 2.0 Async + psycopg2 sync)
- **Validation**: Pydantic v2 (BaseModel, Settings)
- **Testing**: pytest + pytest-asyncio + httpx (3 tests currently)
- **Container**: Docker with non-root user, health checks

---

## 2. Folder Structure & Key Files

```
app/
├── src/
│   ├── coach/
│   │   ├── agents/
│   │   │   ├── graph.py              # Core: LangGraph workflow definition
│   │   │   ├── state.py              # AgentState schema for message passing
│   │   │   ├── tools.py              # SQL toolkit initialization
│   │   │   └── prompts.py            # System prompts for all 3 agents
│   │   ├── services/
│   │   │   ├── insights.py           # Core: Proactive insight generation service
│   │   │   └── prompts.py            # Prompts for insight generation
│   │   ├── main.py                   # Core: FastAPI app + all endpoints
│   │   ├── config.py                 # Core: Pydantic settings (env vars)
│   │   ├── database.py               # Dual engine setup (async + sync)
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   ├── schema.py                 # Pydantic request/response schemas
│   │   └── seeder.py                 # Database seeding script
│   └── tests/
│       ├── conftest.py               # Pytest fixtures (AsyncClient)
│       └── test_api.py               # Basic health check tests
├── Dockerfile                        # Container definition
├── pyproject.toml                    # Dependencies + project metadata
└── uv.lock                           # Locked dependency versions
```

**Key File Annotations:**

- **`main.py`**: 400+ lines. Defines 15 endpoints (chat, dashboard, insights). Uses dependency injection for DB sessions.
- **`agents/graph.py`**: Builds LangGraph workflow. Supervisor node delegates to SQL Expert or Data Analyst via tool calls.
- **`agents/prompts.py`**: 200+ lines of XML-structured system prompts. Defines agent roles, constraints, and examples.
- **`services/insights.py`**: Async service that calculates metrics, prompts LLM, and persists insights to DB.
- **`config.py`**: Pydantic Settings with computed fields for database URLs. Loads from `.env` files.
- **`database.py`**: Creates TWO engines (async for FastAPI, sync for LangChain SQL tools). Singleton pattern for sync DB.

---

## 3. Key Logic & Data Flow

### Core Flows

#### A. Chat Request (AI Agent Orchestration)

```
POST /chat
  → main.py: chat() endpoint
    → Retrieve/initialize session history (in-memory dict)
      → Add user message to history
        → Prepare LangGraph inputs: {"messages": [HumanMessage(...)]}
          → graph.invoke(inputs, config={"thread_id": ...})
            → Supervisor Node (supervisor_node)
              → LLM with tools bound (query_sql_expert, analyze_transactions)
                → Conditional edge: tools_condition
                  → If tool call: ToolNode executes
                    → Tool invokes sub-agent (sql_expert_agent or analyst_agent)
                      → Sub-agent uses SQLDatabaseToolkit
                        → Queries DB via read-only user
                          → Returns result to supervisor
                            → Supervisor synthesizes final response
                              → Extract final message content
                                → Add to session history
                                  → Return ChatResponse to frontend
```

#### B. Dashboard Data Retrieval

```
GET /api/dashboard/summary
  → main.py: get_dashboard_summary()
    → Dependency injection: get_db() provides AsyncSession
      → Execute 5 SQL queries in sequence:
        1. SUM(amount) WHERE type='credit' (total income)
        2. SUM(amount) WHERE type='debit' (total expense)
        3. SUM(amount) WHERE type='debit' AND date >= start_of_month (monthly spending)
        4. SUM(amount) WHERE type='credit' AND date >= start_of_month (monthly income)
        5. Calculate savings_rate = ((income - spending) / income) * 100
      → Return JSON: {total_balance, monthly_spending, savings_rate, currency}
```

#### C. Proactive Insight Generation

```
POST /api/insights/generate
  → main.py: generate_insights()
    → InsightService.generate_proactive_insights(db, user_id=1)
      → _get_user_metrics(): Query DB for:
        - Current month spending
        - Last month spending
        - Top category + amount
        - User financial goals
      → _ask_ai_for_insight(metrics)
        → Construct prompt with INSIGHT_COACH_SYSTEM + metrics
          → LLM.ainvoke() (async call to Gemini)
            → Parse JSON response (list of insights)
              → Create Insight ORM objects
                → db.add() + db.commit()
                  → Return list of new insights
```

### State Management

- **Chat Sessions**: In-memory Python dict `sessions: Dict[str, List[Message]]` (NOT persisted, lost on restart)
- **Agent State**: LangGraph MemorySaver (in-memory checkpointer) tracks agent conversation state per thread_id
- **Database State**: SQLAlchemy async sessions with context managers (`async with`) for automatic commit/rollback
- **Configuration State**: Pydantic Settings singleton loaded once at startup

---

## 4. Configuration & Environment

### Required Environment Variables (`.env`)

```bash
# Database (Full Access)
POSTGRES_USER=admin_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=financial_coach
POSTGRES_HOST=db                      # 'db' for Docker, 'localhost' for local
POSTGRES_PORT=5432

# Database (Read-Only for AI Agents)
POSTGRES_READONLY_USER=ai_reader
POSTGRES_READONLY_PASSWORD=read_pass

# LLM Configuration
LLM_API_KEY=your_gemini_api_key_here  # REQUIRED: Get from Google AI Studio
LLM_MODEL=gemini-2.5-flash            # Default model

# Application Settings (Optional)
APP_NAME="Smart Financial Coach"
DEBUG=True
```

### Hardcoded Constants

- **User ID**: `user_id = 1` hardcoded in ALL dashboard and insight endpoints (no multi-user support)
- **Default Thread ID**: `"demo_session_1"` in ChatRequest schema
- **Recursion Limit**: 50 (set in graph compilation and agent invocations)
- **Insight Limit**: 5 insights returned from `/api/insights` endpoint
- **Transaction Limit**: Default 10 transactions per page in `/api/transactions`
- **Trend Days**: Default 30 days for `/api/dashboard/trend`

### Connection String Construction

Built in `config.py` via computed fields:

- **Async**: `postgresql+asyncpg://{user}:{pass}@{host}:{port}/{db}`
- **Sync**: `postgresql+psycopg2://{readonly_user}:{readonly_pass}@{host}:{port}/{db}`

---

## 5. "Gotchas" & Technical Debt

### Tricky Parts

1. **Dual Database Engine Pattern**
   - FastAPI uses async engine (`asyncpg`) for endpoints
   - LangChain SQL tools use sync engine (`psycopg2`) with read-only user
   - **Why**: LangChain's SQLDatabaseToolkit doesn't support async
   - **Risk**: Two connection pools can exhaust DB connections under load
   - **Location**: `database.py` lines 8-30

2. **In-Memory Session Storage**
   - Chat history stored in Python dict: `sessions: Dict[str, List[Message]]`
   - **Impact**: All chat history lost on server restart
   - **Workaround**: None currently. Should use Redis or DB persistence.
   - **Location**: `main.py` line 50

3. **Hardcoded User ID**
   - Every endpoint assumes `user_id = 1`
   - **Impact**: No multi-user support. All users see same data.
   - **Location**: All dashboard endpoints in `main.py` (lines 170, 220, 250, 280, 310, 340, 370)

4. **LLM Response Parsing**
   - Insight generation expects JSON from LLM, with fallback parsing for markdown code blocks
   - **Risk**: If LLM returns malformed JSON, fallback creates generic insight
   - **Location**: `services/insights.py` lines 90-105

5. **Agent Recursion Limits**
   - Graph compiled with `recursion_limit=50` to prevent infinite loops
   - **Risk**: Complex queries may hit limit and fail silently
   - **Location**: `agents/graph.py` line 95

### Known Issues

- **No Authentication**: No user login, JWT, or session management. Anyone can access any endpoint.
- **No Rate Limiting**: Chat endpoint can be spammed, potentially exhausting LLM API quota.
- **Test Coverage**: Only 3 tests (2 health checks, 1 service test per TEST_COVERAGE.md). Critical `/chat` endpoint untested.
- **Error Handling**: Generic 500 errors returned. No structured error responses or error codes.
- **No Logging Configuration**: Uses default Python logging. No structured logging (JSON), log levels, or rotation.
- **No Database Migrations**: Schema changes require manual SQL or `docker-compose down -v` (destroys data).
- **Session Memory Leak**: `sessions` dict grows unbounded. No TTL or cleanup mechanism.
- **No CORS Configuration**: `allow_origins=["*"]` allows any origin (security risk in production).

### Workarounds

- **Agent State Persistence**: LangGraph uses MemorySaver (in-memory). For production, switch to PostgresSaver or RedisSaver.
- **Multimodal LLM Responses**: Chat endpoint handles list-type responses from LLM (lines 120-127 in `main.py`).
- **JSON Cleanup**: Insight service strips markdown code blocks from LLM JSON responses (lines 95-98 in `services/insights.py`).

---

## 6. Development Workflow

### Commands

#### Initial Setup

```bash
# 1. Ensure uv is installed
# Windows: https://docs.astral.sh/uv/getting-started/installation/
# Or: pip install uv

# 2. Navigate to backend directory
cd app

# 3. Install dependencies
uv sync

# 4. Copy environment template
cp ../.env.example ../.env
# Edit .env with your credentials (especially LLM_API_KEY)
```

#### Development (Docker - Recommended)

```bash
# From project root
docker-compose up backend

# View logs
docker-compose logs -f backend

# Restart after code changes (hot reload enabled)
# No restart needed - Uvicorn --reload watches files

# Run seeder
docker-compose exec backend uv run python -m coach.seeder

# Access API docs
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

#### Development (Local - Without Docker)

```bash
cd app

# Activate virtual environment (created by uv sync)
source .venv/bin/activate  # Linux/Mac
# Or: .venv\Scripts\activate  # Windows

# Run development server
uv run uvicorn coach.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_api.py::test_root_endpoint -v

# Run seeder
uv run python -m coach.seeder
```

#### Testing

```bash
# Run all tests
docker-compose exec backend uv run pytest

# Run with coverage
docker-compose exec backend uv run pytest --cov=coach --cov-report=html

# Run specific test file
docker-compose exec backend uv run pytest tests/test_api.py -v

# Run with verbose output
docker-compose exec backend uv run pytest -vv
```

#### Debugging

```bash
# Check if graph loads correctly
docker-compose exec backend uv run python -c "from coach.agents.graph import graph; print('Graph loaded:', graph is not None)"

# Test database connection
docker-compose exec backend uv run python -c "from coach.database import engine; import asyncio; asyncio.run(engine.connect())"

# Interactive Python shell with app context
docker-compose exec backend uv run python
>>> from coach.main import app
>>> from coach.agents.graph import graph
>>> from coach.database import get_db
```

#### Common Tasks

**Add a New Endpoint**

1. Open `app/src/coach/main.py`
2. Add function with `@app.get()` or `@app.post()` decorator
3. Use `Depends(get_db)` for database access
4. Define Pydantic schemas in `schema.py` if needed
5. Test with Swagger UI at `/docs`

**Modify Agent Behavior**

1. Edit system prompts in `app/src/coach/agents/prompts.py`
2. Restart backend (hot reload should pick up changes)
3. Test via `/chat` endpoint

**Add a New Agent Tool**

1. Define tool function in `agents/tools.py` or as `@tool` decorator
2. Add to `supervisor_tools` list in `agents/graph.py`
3. Update supervisor prompt to mention new tool capability

**Change LLM Model**

1. Update `LLM_MODEL` in `.env` (e.g., `gemini-2.0-flash-exp`)
2. Restart backend
3. Verify in logs: "Using model: gemini-2.0-flash-exp"

---

## Quick Reference

| Task              | Command                                                     |
| ----------------- | ----------------------------------------------------------- |
| Start Backend     | `docker-compose up backend`                                 |
| View Logs         | `docker-compose logs -f backend`                            |
| Run Tests         | `docker-compose exec backend uv run pytest`                 |
| Seed Database     | `docker-compose exec backend uv run python -m coach.seeder` |
| API Docs          | http://localhost:8000/docs                                  |
| Health Check      | `curl http://localhost:8000/health`                         |
| Interactive Shell | `docker-compose exec backend uv run python`                 |

---

## API Endpoint Reference

### Chat Endpoints

| Endpoint         | Method | Purpose                       | Auth |
| ---------------- | ------ | ----------------------------- | ---- |
| `/chat`          | POST   | Send message to AI agent      | None |
| `/reset-session` | POST   | Clear chat history for thread | None |
| `/sessions`      | GET    | List active chat sessions     | None |

### Dashboard Endpoints

| Endpoint                    | Method | Purpose                              | User ID       |
| --------------------------- | ------ | ------------------------------------ | ------------- |
| `/api/dashboard/summary`    | GET    | Balance, spending, savings rate      | 1 (hardcoded) |
| `/api/dashboard/categories` | GET    | Spending by category (current month) | 1             |
| `/api/dashboard/trend`      | GET    | Daily spending trend (30 days)       | 1             |
| `/api/transactions`         | GET    | Paginated transaction list           | 1             |
| `/api/subscriptions`        | GET    | Active subscriptions                 | 1             |

### Insight Endpoints

| Endpoint                  | Method | Purpose                       | User ID |
| ------------------------- | ------ | ----------------------------- | ------- |
| `/api/insights`           | GET    | Get recent insights (limit 5) | 1       |
| `/api/insights/generate`  | POST   | Trigger AI insight generation | 1       |
| `/api/insights/{id}/read` | PATCH  | Mark insight as read          | Any     |

### Health Endpoints

| Endpoint  | Method | Purpose                        |
| --------- | ------ | ------------------------------ |
| `/`       | GET    | Basic health check             |
| `/health` | GET    | Detailed health (graph loaded) |

---

## Agent Architecture Deep Dive

### Supervisor Agent

- **Role**: Orchestrates conversation, delegates to specialists
- **Tools**: `query_sql_expert`, `analyze_transactions`
- **Prompt**: `SUPERVISOR_SYSTEM` (200+ lines, XML-structured)
- **Behavior**: Decides which specialist to call based on user query

### SQL Expert Agent

- **Role**: Writes and executes read-only SQL queries
- **Tools**: SQLDatabaseToolkit (QuerySQLDataBaseTool, InfoSQLDatabaseTool, ListSQLDatabaseTool)
- **Prompt**: `SQL_EXPERT_SYSTEM` (strict constraints: no DDL, no DML, only SELECT/CTEs)
- **Database Access**: Read-only user via sync engine

### Data Analyst Agent

- **Role**: Analyzes transaction patterns, computes metrics
- **Tools**: Same SQL toolkit as SQL Expert
- **Prompt**: `ANALYST_SYSTEM` (focuses on aggregations, category breakdowns)
- **Output**: JSON summaries, CSV-like tables

### Tool Execution Flow

```
User: "How much did I spend on food last month?"
  → Supervisor receives message
    → Decides to call analyze_transactions tool
      → Tool invokes analyst_agent
        → Analyst uses QuerySQLDataBaseTool
          → Executes: SELECT SUM(amount) FROM transactions WHERE category='Food' AND ...
            → Returns result to analyst
              → Analyst formats response
                → Returns to supervisor
                  → Supervisor synthesizes final answer
                    → Returns to user
```

---

## Dependency Management (uv)

### Key Files

- **`pyproject.toml`**: Project metadata + dependencies
- **`uv.lock`**: Locked versions (like package-lock.json)

### Common Commands

```bash
# Add new dependency
uv add <package-name>

# Add dev dependency
uv add --dev <package-name>

# Update dependencies
uv lock --upgrade

# Sync environment with lock file
uv sync

# Run command in virtual environment
uv run <command>
```

---

## Testing Strategy

### Current State

- **Total Tests**: 3 (per TEST_COVERAGE.md)
- **Coverage**: Health checks only
- **Framework**: pytest + pytest-asyncio + httpx

### Test Structure

```python
# conftest.py: Fixtures
@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

# test_api.py: Tests
@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
```

### Recommended Test Additions

1. **Chat Endpoint**: Mock LangGraph graph.invoke()
2. **Dashboard Endpoints**: Use test database with fixtures
3. **Insight Service**: Mock LLM responses
4. **Agent Tools**: Test SQL query generation
5. **Error Handling**: Test 404, 500 responses

---

## Production Readiness Checklist

- [ ] Add authentication (JWT, OAuth)
- [ ] Implement rate limiting (slowapi, Redis)
- [ ] Add structured logging (structlog, JSON format)
- [ ] Persist chat sessions (Redis, PostgreSQL)
- [ ] Add database migrations (Alembic)
- [ ] Implement multi-user support (remove hardcoded user_id=1)
- [ ] Add comprehensive tests (target 80%+ coverage)
- [ ] Configure CORS properly (whitelist specific origins)
- [ ] Add monitoring (Prometheus, Grafana)
- [ ] Implement graceful shutdown
- [ ] Add request validation middleware
- [ ] Set up CI/CD pipeline
- [ ] Add API versioning (/v1/chat)
- [ ] Implement caching (Redis for dashboard data)
- [ ] Add LLM response streaming (SSE)

---

**Last Updated**: February 3, 2026  
**Maintainer**: Backend Team  
**Questions?** Check `DESIGN_DOC.md` for architecture context or `app/README.md` for setup instructions.
