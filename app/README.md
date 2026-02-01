# Smart Financial Coach - Backend

This is the FastAPI-based backend for the Smart Financial Coach application. it leverages LangGraph to coordinate multiple AI agents that analyze financial data and provide personalized insights.

## Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Orchestration:** [LangGraph](https://langchain-ai.github.io/langgraph/) & [LangChain](https://www.langchain.com/)
- **LLM:** [Google Gemini](https://ai.google.dev/) (via `langchain-google-genai`)
- **Database:** [PostgreSQL](https://www.postgresql.org/)
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async)
- **Package Manager:** [uv](https://github.com/astral-sh/uv)

## Architecture

### AI Agents (`app/src/coach/agents`)

The system uses a supervisor-worker pattern implemented with LangGraph:

- **Supervisor:** Orchestrates the conversation and delegates tasks.
- **SQL Expert:** Specializes in generating and executing read-only SQL queries to answer data-specific questions.
- **Data Analyst:** Processes transaction patterns, computes metrics, and identifies trends.

### Services (`app/src/coach/services`)

- **Insight Service:** Periodically (or on-demand) analyzes user metrics to generate proactive financial advice and alerts.

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) installed
- A running PostgreSQL instance
- Google Gemini API Key

### Environment Setup

Create a `.env` file in the `app/` directory (or use the one in the root) with the following:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=financial_coach
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
LLM_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-2.0-flash
```

### Installation

```bash
cd app
uv sync
```

### Running Locally

1. **Database Seeding:**
   Initialize tables and add demo data:

   ```bash
   uv run python -m coach.seeder
   ```

2. **Start the Server:**
   ```bash
   uv run uvicorn coach.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

## API Endpoints

### Chat

- `POST /chat`: Main entry point for AI coaching. Handles thread management and conversation history.
- `POST /reset-session`: Clears conversation state for a specific thread.

### Dashboard & Data

- `GET /api/dashboard/summary`: Income, expenses, and savings rate.
- `GET /api/dashboard/categories`: Spending breakdown by category.
- `GET /api/dashboard/trend`: Daily spending trend for the last 30 days.
- `GET /api/transactions`: Paginated transaction list.
- `GET /api/subscriptions`: Identified recurring subscriptions.

### Insights

- `GET /api/insights`: Retrieve recent AI-generated insights.
- `POST /api/insights/generate`: Manually trigger the insight generation engine.

## Testing

Tests are located in `app/src/tests`.

```bash
cd app
uv run pytest
```

## Docker

The backend is dockerized and intended to be run via the root `docker-compose.yml`.

```bash
docker compose up financial_coach_backend
```
