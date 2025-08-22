# tests/conftest.py
from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from budget_bot.db.session import get_session
from budget_bot.main import app

# Используем отдельную БД для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# ИСПОЛЬЗУЕМ СОВРЕМЕННЫЙ ASYNC_SESSIONMAKER
AsyncTestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для подмены сессии БД на тестовую."""
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def db_setup_and_teardown(
    db_session: AsyncSession,
) -> AsyncGenerator[None, None]:
    """
    Создает таблицы перед каждым тестом и удаляет их после.
    Применяется автоматически ко всем тестам.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Универсальный асинхронный клиент для API.
    Эта фикстура подменяет зависимость сессии БД на тестовую
    и очищает все переопределения зависимостей после завершения теста.
    """

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(name="user_a_data")
def user_a_data_fixture() -> Dict[str, Any]:
    """Возвращает тестовые данные для пользователя А."""
    return {
        "id": 12345678,
        "first_name": "User",
        "last_name": "A",
        "username": "user_a",
    }


@pytest.fixture(name="user_b_data")
def user_b_data_fixture() -> Dict[str, Any]:
    """Возвращает тестовые данные для пользователя Б."""
    return {"id": 999999, "first_name": "UserB"}
