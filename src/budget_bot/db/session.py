# src/budget_bot/db/session.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from budget_bot.db.engine import engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI зависимость для получения асинхронной сессии БД.
    """
    async with AsyncSession(engine) as session:
        yield session
