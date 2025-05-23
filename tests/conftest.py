"""
Конфигурационный файл для pytest, содержащий общие фикстуры для тестирования бота.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import aiosqlite
from contextlib import asynccontextmanager

from states import FinancesForm


# Фикстура для мокирования объекта Bot
@pytest_asyncio.fixture
async def bot_mock():
    """Мокирует объект aiogram.Bot."""
    return AsyncMock()


# Фикстура для мокирования объекта Dispatcher
@pytest_asyncio.fixture
async def dispatcher_mock():
    """Мокирует объект aiogram.Dispatcher."""
    dp_mock = MagicMock()
    dp_mock.include_router = MagicMock()
    return dp_mock


# Фикстура для мокирования объекта Message
@pytest_asyncio.fixture
async def message_mock():
    """Мокирует объект aiogram.types.Message."""
    msg = AsyncMock()
    msg.from_user = MagicMock()
    msg.from_user.id = 12345
    msg.from_user.full_name = "Test User"
    msg.text = ""
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    return msg


# Фикстура для мокирования объекта FSMContext
@pytest_asyncio.fixture
async def state_mock():
    """Мокирует объект aiogram.fsm.context.FSMContext."""
    state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


# Фикстура для мокирования асинхронного соединения и курсора aiosqlite
@pytest_asyncio.fixture
async def mock_aiosqlite_conn_cursor():
    """
    Создает мок асинхронного соединения и курсора aiosqlite.
    """
    mock_cursor = AsyncMock()
    mock_conn = AsyncMock()

    # Настраиваем курсор как асинхронный контекстный менеджер
    mock_cursor_context = AsyncMock()
    mock_cursor_context.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor_context.__aexit__ = AsyncMock()
    mock_conn.cursor = AsyncMock(return_value=mock_cursor_context)

    # Настраиваем базовые методы
    mock_conn.commit = AsyncMock()
    mock_conn.close = AsyncMock()

    # Имитация fetchone для SELECT-запросов
    _db_data = {}  # Простое хранилище для имитации БД

    async def mock_execute(query, params=None):
        if "INSERT INTO users" in query:
            user_id = params[0]
            _db_data[user_id] = {"telegram_id": params[0], "name": params[1]}
        elif "SELECT * FROM users" in query:
            user_id = params[0]
            if user_id in _db_data:
                return (
                    1,
                    _db_data[user_id]["telegram_id"],
                    _db_data[user_id]["name"],
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            return None

    mock_cursor.execute = AsyncMock(side_effect=mock_execute)
    mock_cursor.fetchone = AsyncMock()

    return mock_conn, mock_cursor


# Фикстура для подмены aiosqlite.connect
@pytest_asyncio.fixture(autouse=True)
async def patch_aiosqlite_connect(monkeypatch, mock_aiosqlite_conn_cursor):
    """
    Подменяет aiosqlite.connect так, чтобы он всегда возвращал мок асинхронного соединения.
    """
    mock_conn, _ = mock_aiosqlite_conn_cursor

    # Создаем асинхронный контекстный менеджер для соединения
    mock_conn_context = AsyncMock()
    mock_conn_context.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn_context.__aexit__ = AsyncMock()

    async def mock_connect(*args, **kwargs):
        return mock_conn_context

    monkeypatch.setattr(aiosqlite, "connect", mock_connect)
