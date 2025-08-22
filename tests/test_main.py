# tests/test_main.py
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_root_endpoint(client: AsyncClient) -> None:
    """Тест: корневой эндпоинт отдает HTML-файл."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Учет Расходов" in response.text


async def test_lifespan_creates_tables(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """
    Тест: контекстный менеджер lifespan корректно создает таблицы в БД.
    Фикстура `client` автоматически запускает lifespan приложения.
    Нам нужно лишь проверить, что таблицы были созданы.
    """

    def check_tables_exist(conn: Any) -> bool:
        inspector = inspect(conn.bind)
        # Проверяем наличие таблиц, определенных в db/models.py
        return all(
            inspector.has_table(table_name)
            for table_name in ["user", "category", "expense"]
        )

    # Запускаем синхронную функцию проверки внутри асинхронной сессии
    tables_exist = await db_session.run_sync(check_tables_exist)
    assert tables_exist is True
