# app/src/agents/tools.py
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    from coach.database import sync_db
except ImportError:
    from database import sync_db


def get_financial_tools(llm: ChatGoogleGenerativeAI):
    """
    Creates a toolkit that allows the AI to query the database.
    """
    # Create Toolkit using the singleton db instance
    toolkit = SQLDatabaseToolkit(db=sync_db, llm=llm)

    # Return specific tools (QuerySQL, InfoSQL, etc.)
    return toolkit.get_tools()
