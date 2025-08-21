from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
import logging

from app.models.base import Base

logger = logging.getLogger(__name__)

# Construct the AsyncPostgreSQL connection URL
ASYNC_SQLALCHEMY_DATABASE_URL = settings.database_url

# Create the async engine with optimized settings
engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    pool_size=settings.DB_POOL_MIN,
    max_overflow=settings.DB_POOL_MAX - settings.DB_POOL_MIN,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Disable in production
    future=True,
)

# Create an async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Define the base class for models


async def get_async_db() -> AsyncGenerator[AsyncSession | Any, Any]:
    """
    Async generator that yields database sessions.
    Ensures sessions are properly closed after use.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session failed: {str(e)}")
            raise
        finally:
            await session.close()

async def init_db():
    """
    Initialize the database by creating all tables.
    Should be called during application startup.
    """
    logger.info("Initializing database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully")

async def close_db():
    """
    Close all database connections.
    Should be called during application shutdown.
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed successfully")