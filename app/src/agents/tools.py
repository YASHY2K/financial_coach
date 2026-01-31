# app/src/agents/tools.py
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy import create_engine

try:
    from ..config import settings
except ImportError:
    from config import settings


def get_financial_tools(llm: ChatGoogleGenerativeAI):
    """
    Creates a toolkit that allows the AI to query the database.
    """
    # Convert Async URL to Sync URL (asyncpg -> psycopg2)
    # The AI needs standard synchronous connection to 'think' linearly
    sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")

    # Create Engine & Database wrapper
    engine = create_engine(sync_db_url)
    db = SQLDatabase(engine)

    # Create Toolkit
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Return specific tools (QuerySQL, InfoSQL, etc.)
    return toolkit.get_tools()
