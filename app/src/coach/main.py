from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from coach.schema import ChatRequest, ChatResponse, Message
from typing import List, Dict
import logging
import sys
from langchain_core.messages import HumanMessage

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("fastapi_app")

try:
    from coach.agents.graph import graph

    logger.info("Successfully imported graph from src.agents")
except ImportError:
    from agents.graph import graph

    logger.info("Successfully imported graph from agents (fallback)")

# --- FastAPI App Setup ---
app = FastAPI(
    title="Smart Financial Coach API",
    description="API for financial coaching and spending analysis",
    version="1.0.0",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
