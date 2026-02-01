from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from coach.schema import ChatRequest, ChatResponse, Message
from typing import List, Dict
import logging
from datetime import date, timedelta
from langchain_core.messages import HumanMessage

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from coach.agents.graph import graph
from coach.database import get_db
from coach.models import Transaction, Insight
from coach.services.insights import InsightService

logger = logging.getLogger("fastapi_app")
logger.info("Successfully imported graph and models")

insight_service = InsightService()


# --- Lifespan (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Database permissions managed externally
    yield
    # Shutdown: Clean up resources if needed
    logger.info("Shutdown: Application stopping...")


# --- FastAPI App Setup ---
app = FastAPI(
    title="Smart Financial Coach API",
    description="API for financial coaching and spending analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory session storage (replace with Redis/DB in production) ---
sessions: Dict[str, List[Message]] = {}


# --- API Endpoints ---
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart Financial Coach API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {"status": "healthy", "graph_loaded": graph is not None}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI response

    - message: User's message/question
    - thread_id: Optional session identifier for conversation continuity
    - conversation_history: Optional list of previous messages in the conversation
    """
    try:
        logger.info(f"User Input (Thread: {request.thread_id}): {request.message}")

        # Initialize or retrieve session history
        if request.thread_id not in sessions:
            sessions[request.thread_id] = []

        # Use provided history or session history
        if request.conversation_history:
            conversation_history = request.conversation_history
        else:
            conversation_history = sessions[request.thread_id]

        # Add user message to history
        conversation_history.append(Message(role="user", content=request.message))

        # Prepare inputs for the graph
        config = {"configurable": {"thread_id": request.thread_id}}
        inputs = {"messages": [HumanMessage(content=request.message)]}

        logger.info("Invoking AI Agent...")

        # Invoke the graph
        result = graph.invoke(inputs, config=config)

        # Debug logging
        logger.debug("\n========== GRAPH MESSAGES ==========")
        for msg in result["messages"]:
            logger.debug(f"[{type(msg).__name__}]: {msg.content}")
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                logger.debug(f"   Tool Calls: {msg.tool_calls}")
        logger.debug("====================================\n")

        # Extract final response
        final_response = result["messages"][-1].content

        # Handle case where content is a list (e.g. multimodal output)
        if isinstance(final_response, list):
            text_parts = []
            for block in final_response:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            final_response = "".join(text_parts)

        logger.info(f"AI Response generated (Length: {len(final_response)} chars)")

        # Add assistant message to history
        conversation_history.append(Message(role="assistant", content=final_response))

        # Update session storage
        sessions[request.thread_id] = conversation_history

        return ChatResponse(
            response=final_response,
            thread_id=request.thread_id,
            conversation_history=conversation_history,
        )

    except Exception as e:
        logger.error("Error during AI execution", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}",
        )


@app.post("/reset-session")
async def reset_session(thread_id: str = "demo_session_1"):
    """Reset conversation history for a specific session"""
    if thread_id in sessions:
        del sessions[thread_id]
        logger.info(f"Session {thread_id} reset")
        return {"status": "success", "message": f"Session {thread_id} has been reset"}
    return {"status": "success", "message": "Session did not exist"}


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {"sessions": list(sessions.keys()), "count": len(sessions)}


# --- Dashboard API Endpoints ---


@app.get("/api/dashboard/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """
    Get summary statistics: Total Balance (Income - Expense), Monthly Spending, Savings Rate.
    Note: For this demo, we assume 'demo_user' (user_id=1).
    """
    user_id = 1  # Hardcoded for demo simplicity

    # 1. Total Balance Calculation
    # Sum of all credits (Income) - Sum of all debits (Expenses)
    income_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.transaction_type == "credit"
    )
    expense_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.transaction_type == "debit"
    )

    total_income = (await db.execute(income_stmt)).scalar() or 0
    total_expense = (await db.execute(expense_stmt)).scalar() or 0
    balance = float(total_income - total_expense)

    # 2. Monthly Spending (Current Month)
    today = date.today()
    start_of_month = today.replace(day=1)

    monthly_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "debit",
        Transaction.date >= start_of_month,
    )
    monthly_spending = (await db.execute(monthly_stmt)).scalar() or 0

    # 3. Savings Rate (Income vs Expense for current month)
    monthly_income_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "credit",
        Transaction.date >= start_of_month,
    )
    monthly_income = (await db.execute(monthly_income_stmt)).scalar() or 0

    savings_rate = 0
    if monthly_income > 0:
        savings_rate = ((monthly_income - monthly_spending) / monthly_income) * 100

    return {
        "total_balance": balance,
        "monthly_spending": float(monthly_spending),
        "savings_rate": round(float(savings_rate), 1),
        "currency": "$",
    }


@app.get("/api/dashboard/categories")
async def get_spending_by_category(db: AsyncSession = Depends(get_db)):
    """
    Get spending breakdown by category for the current month.
    """
    user_id = 1
    today = date.today()
    start_of_month = today.replace(day=1)

    stmt = (
        select(Transaction.category, func.sum(Transaction.amount).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.date >= start_of_month,
            Transaction.category.isnot(None),
        )
        .group_by(Transaction.category)
    )

    results = await db.execute(stmt)
    data = [{"name": row.category, "value": float(row.total)} for row in results]

    return data


@app.get("/api/dashboard/trend")
async def get_spending_trend(db: AsyncSession = Depends(get_db), days: int = 30):
    """
    Get daily spending trend for the last N days.
    """
    user_id = 1
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    stmt = (
        select(Transaction.date, func.sum(Transaction.amount).label("daily_total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.date >= start_date,
        )
        .group_by(Transaction.date)
        .order_by(Transaction.date)
    )

    results = await db.execute(stmt)

    # Format for chart: "Jan 01"
    data = [
        {"date": row.date.strftime("%b %d"), "amount": float(row.daily_total)}
        for row in results
    ]
    return data


@app.get("/api/transactions")
async def get_transactions(
    db: AsyncSession = Depends(get_db), limit: int = 10, offset: int = 0
):
    """
    Get paginated list of transactions.
    """
    user_id = 1
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.date))
        .limit(limit)
        .offset(offset)
    )

    results = await db.execute(stmt)
    transactions = results.scalars().all()

    return [
        {
            "id": t.id_,
            "merchant": t.merchant,
            "amount": float(t.amount),
            "date": t.date.isoformat(),
            "category": t.category or "Uncategorized",
            "type": t.transaction_type,
        }
        for t in transactions
    ]


@app.get("/api/subscriptions")
async def get_subscriptions(db: AsyncSession = Depends(get_db)):
    """
    Get active subscriptions.
    """
    user_id = 1

    # Improved logic: Find the latest transaction for each subscription merchant
    # For now, simple query to get all sub transactions and dedupe in python
    stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id, Transaction.is_subscription == True)
        .order_by(desc(Transaction.date))
    )

    results = await db.execute(stmt)
    all_subs = results.scalars().all()

    unique_subs = {}
    for sub in all_subs:
        if sub.merchant not in unique_subs:
            unique_subs[sub.merchant] = {
                "id": sub.id_,
                "name": sub.merchant,
                "amount": float(sub.amount),
                "due_date": sub.date.day,  # rudimentary "due day"
                "category": sub.category,
            }

    return list(unique_subs.values())


@app.get("/api/insights")
async def get_insights(db: AsyncSession = Depends(get_db)):
    """
    Get all insights for the demo user.
    """
    user_id = 1
    stmt = (
        select(Insight)
        .where(Insight.user_id == user_id)
        .order_by(desc(Insight.created_at))
        .limit(5)
    )
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    return [
        {
            "id": i.id_,
            "title": i.title,
            "message": i.message,
            "type": i.type,
            "created_at": i.created_at.isoformat(),
            "is_read": i.is_read
        }
        for i in insights
    ]


@app.post("/api/insights/generate")
async def generate_insights(db: AsyncSession = Depends(get_db)):
    """
    Manually trigger insight generation.
    """
    user_id = 1
    new_insights = await insight_service.generate_proactive_insights(db, user_id)
    return {"status": "success", "count": len(new_insights)}


@app.patch("/api/insights/{insight_id}/read")
async def mark_insight_as_read(insight_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mark an insight as read.
    """
    stmt = select(Insight).where(Insight.id_ == insight_id)
    result = await db.execute(stmt)
    insight = result.scalars().first()
    
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    insight.is_read = True
    await db.commit()
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)