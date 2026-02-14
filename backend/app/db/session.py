from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# asyncpg rejects sslmode; use ssl=True for cloud DBs (Neon, Render Postgres)
_connect_args = {}
if any(x in settings.database_url for x in ("neon.tech", "render.com", "amazonaws.com")):
    _connect_args["ssl"] = True

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args=_connect_args if _connect_args else None,
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
