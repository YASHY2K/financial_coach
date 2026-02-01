# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase

try:
    from coach.config import settings
except ImportError:
    from config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# --- Synchronous Engine for LangChain Tools (Singleton) ---
# Convert Async URL to Sync URL (asyncpg -> psycopg2)
sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")

sync_engine = create_engine(
    sync_db_url,
    echo=False,  # Keep logs clean for tools
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Singleton SQLDatabase instance (inspects schema once at startup)
sync_db = SQLDatabase(sync_engine)


class Base(DeclarativeBase):
    pass


# safe db session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
