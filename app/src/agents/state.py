# app/src/agents/state.py
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 'messages' tracks the chat history. 
    # 'add_messages' ensures appending new thoughts instead of deleting old ones
    messages: Annotated[Sequence[BaseMessage], add_messages]