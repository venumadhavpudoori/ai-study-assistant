from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

async_engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
)

async_session_maker = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_db():
    async with async_session_maker() as session:
        yield session
