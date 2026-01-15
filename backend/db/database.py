"""Database connection and session management."""

import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from core.config import settings

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    echo=False,  # Set to True for SQL query logging
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db() -> None:
    """Initialize database by creating all tables."""
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from models.document import Document
        from models.chunk import Chunk
        from models.job import Job, JobState, JobEvent
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")


@asynccontextmanager
async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
