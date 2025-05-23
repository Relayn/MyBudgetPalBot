"""
Тесты для модуля database.db.
"""

import pytest
import aiosqlite
from database.db import init_db


@pytest.mark.asyncio
async def test_init_db_creates_table(mock_aiosqlite_conn_cursor):
    """
    Проверяет, что функция init_db корректно вызывает создание таблицы 'users'.
    Использует моки для aiosqlite.connect и его методов.
    """
    mock_conn, mock_cursor = mock_aiosqlite_conn_cursor

    # Вызываем функцию init_db
    await init_db(
        ":memory:"
    )  # Имя БД не имеет значения, так как aiosqlite.connect мокирован

    # Проверяем, что mock_cursor.execute был вызван с запросом CREATE TABLE
    mock_cursor.execute.assert_called_once()
    assert "CREATE TABLE IF NOT EXISTS users" in mock_cursor.execute.call_args[0][0]

    # Проверяем, что mock_conn.commit был вызван
    mock_conn.commit.assert_called_once()
