# src/budget_bot/db/engine.py
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

DATABASE_URL = "sqlite+aiosqlite:///budget.db"

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)


async def create_db_and_tables() -> None:
    """Инициализирует базу данных и создает таблицы."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
