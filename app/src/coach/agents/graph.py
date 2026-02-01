# app/src/agents/graph.py (Recommended Manual Pattern)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

try:
    from .state import AgentState
    from .tools import get_financial_tools
    from .prompts import SUPERVISOR_SYSTEM, ANALYST_SYSTEM, SQL_EXPERT_SYSTEM
    from ..config import settings
except ImportError:
    from agents.state import AgentState
    from agents.tools import get_financial_tools
    from agents.prompts import SUPERVISOR_SYSTEM, ANALYST_SYSTEM, SQL_EXPERT_SYSTEM
    from config import settings

# Initialize Model & Tools
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0, api_key=settings.LLM_API_KEY
)
tools = get_financial_tools(llm)

# ========== Create Sub-Agents ==========

sql_expert_agent = create_agent(
    model=llm,
    tools=tools,
    state_schema=AgentState,
    system_prompt=SQL_EXPERT_SYSTEM,
)

analyst_agent = create_agent(
    model=llm,
    tools=tools,
    state_schema=AgentState,
    system_prompt=ANALYST_SYSTEM,
)

# ========== Wrap Sub-Agents as Tools for Supervisor ==========


@tool
def query_sql_expert(request: str) -> str:
    """
    Use when user asks about database queries, SQL optimization, or schema information.

    Args:
        request: Natural language question about SQL/database operations

    Returns:
        Response from SQL expert agent
    """
    result = sql_expert_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config={"recursion_limit": 50},
    )
    # Extract the final message content
    final_message = result["messages"][-1]
    return (
        final_message.content
        if hasattr(final_message, "content")
        else str(final_message)
    )


@tool
def analyze_transactions(request: str) -> str:
    """
    Use when user asks about spending patterns, budgets, financial insights, or transaction analysis.

    Args:
        request: Natural language question about financial analysis

    Returns:
        Response from data analyst agent
    """
    result = analyst_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config={"recursion_limit": 50},
    )
    # Extract the final message content
    final_message = result["messages"][-1]
    return (
        final_message.content
        if hasattr(final_message, "content")
        else str(final_message)
    )


# ========== Create Supervisor ==========

supervisor_tools = [query_sql_expert, analyze_transactions]
llm_with_tools = llm.bind_tools(supervisor_tools)


def supervisor_node(state: AgentState):
    """
    Main supervisor that coordinates between SQL Expert and Data Analyst
    """
    messages = state["messages"]

    # Prepend system prompt if not present
    if not messages or (hasattr(messages[0], "type") and messages[0].type != "system"):
        from langchain_core.messages import SystemMessage

        system_msg = SystemMessage(content=SUPERVISOR_SYSTEM)
        messages = [system_msg] + list(messages)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# ========== Build Graph ==========

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("tools", ToolNode(supervisor_tools))

# Add edges
workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges("supervisor", tools_condition)
workflow.add_edge("tools", "supervisor")

# Compile with memory
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
graph = graph.with_config({"recursion_limit": 50})
