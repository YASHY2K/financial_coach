from pydantic import BaseModel
from typing import List, Optional


# --- Pydantic Schema ---
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = "demo_session_1"
    conversation_history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    conversation_history: List[Message]
