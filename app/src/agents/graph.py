# app/src/agents/graph.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

try:
    from .state import AgentState
    from .tools import get_financial_tools
    from ..config import settings  # Go up one level to find config
except ImportError:
    # Fallback if python path is behaving strictly
    from agents.state import AgentState
    from agents.tools import get_financial_tools
    from config import settings

# Initialize Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", temperature=0, api_key=settings.LLM_API_KEY
)

# Bind Tools to Model
# This gives the LLM the "menu" of functions it can call (like sql_db_query)
tools = get_financial_tools(llm)
llm_with_tools = llm.bind_tools(tools)


# Define Nodes
def agent_node(state: AgentState):
    """
    Main brain. It decides whether to answer directly
    or call SQL tool based on the user's message.
    """
    messages = state["messages"]

    # Enforce 'Coach' persona
    system_message = {
        "role": "system",
        "content": (
            "You are a Smart Financial Coach. "
            "You have access to a SQL database of the user's transactions. "
            "If the user asks about spending, ALWAYS query the database to get exact numbers. "
            "When you find 'Subscription' transactions or monthly recurring charges, flag them. "
            "Be concise, friendly, and non-judgmental."
        ),
    }

    # If history is just user message, prepend system prompt
    if len(messages) == 1 or messages[0].type != "system":
        messages = [system_message] + list(messages)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# Build Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

# Add Edges
workflow.add_edge(START, "agent")

# Conditional Edge:
# If agent decided to call tool -> Go to 'tools' node
# If agent just replied with text -> Go to END
workflow.add_conditional_edges("agent", tools_condition)

# Loop back: After tools run, go back to agent to interpret result
workflow.add_edge("tools", "agent")

# Compile with Memory
# MemorySaver keeps conversation alive in RAM (perfect for Streamlit session state)
checkpointer = MemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
