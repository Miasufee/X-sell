from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from app.config import settings


# Construct the AsyncPostgreSQL connection URL
ASYNC_SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@"
    f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"
)

# Create the async engine
engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Maximum number of connections in the pool
    max_overflow=10,  # Allow a small overflow to handle spikes
    echo=True,  # Set to False in production to reduce logging noise
)

# Create an async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keeps objects in the session state after commit
    autocommit=False,  # Ensures transactions are explicitly committed
    autoflush=False,  # Avoids automatic flushes to improve performance control
)

# Define the base class for models
Base = declarative_base()


# Dependency for async database session
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()  # Explicit close to release the connection back to the pool


# Initialize the database (create tables)
async def init_db():
    async with engine.begin() as conn:  # Ensures proper transaction handling
        await conn.run_sync(Base.metadata.create_all)  # Run synchronous metadata creation


# Close the database (dispose of the engine)
async def close_db():
    await engine.dispose()  # Properly dispose of the engine and close connections
