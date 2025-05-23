"""
Тесты для основных хэндлеров бота.
Использует моки для aiogram объектов и тестовую БД.
"""

import pytest
from unittest.mock import patch
from aiogram import F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

# Импортируем сами функции-хэндлеры из их модулей для прямого вызова
from handlers.start import send_start
from handlers.registration import registration
from handlers.finances import cmd_cancel
from handlers.finances import (
    finances_start,
    process_category1,
    process_expenses1,
    process_category2,
    process_expenses2,
    process_category3,
    process_expenses3,
)
from handlers.other import handle_unknown_message

from states import FinancesForm


# Тест для хэндлера /start
@pytest.mark.asyncio
async def test_send_start(bot_mock, message_mock, state_mock):
    """
    Проверяет, что хэндлер /start отправляет приветственное сообщение
    и главную клавиатуру.
    """
    message_mock.text = "/start"
    await send_start(message_mock)

    message_mock.answer.assert_called_once()
    args, kwargs = message_mock.answer.call_args
    assert "Привет! Я ваш личный финансовый помощник." in args[0]
    assert "reply_markup" in kwargs
    assert kwargs["reply_markup"] is not None


# Тест для хэндлера регистрации (новый пользователь)
@pytest.mark.asyncio
async def test_registration_new_user(
    bot_mock, message_mock, state_mock, mock_aiosqlite_conn_cursor
):
    """
    Проверяет, что новый пользователь успешно регистрируется.
    """
    mock_conn, mock_cursor = mock_aiosqlite_conn_cursor

    message_mock.text = "Регистрация в телеграм-боте"
    message_mock.from_user.id = 10001
    message_mock.from_user.full_name = "New User"

    # Настраиваем мок, чтобы fetchone вернул None (пользователь не найден)
    mock_cursor.fetchone.return_value = None

    await registration(message_mock)

    # Проверяем вызов SELECT
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM users WHERE telegram_id = ?", (10001,)
    )
    mock_cursor.fetchone.assert_called_once()

    # Проверяем вызов INSERT
    mock_cursor.execute.assert_any_call(
        "INSERT INTO users (telegram_id, name) VALUES (?, ?)", (10001, "New User")
    )
    mock_conn.commit.assert_called_once()
    message_mock.answer.assert_called_once_with("Вы успешно зарегистрированы!")


# Тест для хэндлера регистрации (существующий пользователь)
@pytest.mark.asyncio
async def test_registration_existing_user(
    bot_mock, message_mock, state_mock, mock_aiosqlite_conn_cursor
):
    """
    Проверяет, что существующий пользователь корректно обрабатывается.
    """
    mock_conn, mock_cursor = mock_aiosqlite_conn_cursor

    message_mock.text = "Регистрация в телеграм-боте"
    message_mock.from_user.id = 10002
    message_mock.from_user.full_name = "Existing User"

    # Настраиваем мок, чтобы fetchone вернул пользователя (пользователь найден)
    mock_cursor.fetchone.return_value = (
        1,
        10002,
        "Existing User",
        None,
        None,
        None,
        None,
        None,
        None,
    )

    await registration(message_mock)

    # Проверяем вызов SELECT
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM users WHERE telegram_id = ?", (10002,)
    )
    mock_cursor.fetchone.assert_called_once()
    mock_conn.commit.assert_not_called()  # Не должно быть коммита при существующем пользователе
    message_mock.answer.assert_called_once_with("Вы уже зарегистрированы!")


# Тест для хэндлера команды /cancel
@pytest.mark.asyncio
async def test_cmd_cancel_active_state(bot_mock, message_mock, state_mock):
    """
    Проверяет, что команда /cancel очищает активное состояние FSM.
    """
    # Устанавливаем активное состояние
    state_mock.get_state.return_value = FinancesForm.category1
    message_mock.text = "/cancel"

    await cmd_cancel(message_mock, state_mock)

    state_mock.clear.assert_called_once()
    message_mock.answer.assert_called_once()
    args, kwargs = message_mock.answer.call_args
    assert "Действие отменено" in args[0]
    assert "reply_markup" in kwargs


# Тест для хэндлера команды /cancel без активного состояния
@pytest.mark.asyncio
async def test_cmd_cancel_no_active_state(bot_mock, message_mock, state_mock):
    """
    Проверяет поведение команды /cancel, когда нет активного состояния.
    """
    state_mock.get_state.return_value = None
    message_mock.text = "/cancel"

    await cmd_cancel(message_mock, state_mock)

    state_mock.clear.assert_not_called()
    message_mock.answer.assert_called_once_with("Нет активного диалога для отмены.")


# Тест для хэндлера неизвестного сообщения
@pytest.mark.asyncio
async def test_handle_unknown_message(bot_mock, message_mock, state_mock):
    """
    Проверяет, что хэндлер неизвестных сообщений отвечает корректно.
    """
    message_mock.text = "Какой-то случайный текст"

    await handle_unknown_message(message_mock)

    message_mock.answer.assert_called_once()
    args, kwargs = message_mock.answer.call_args
    assert "Извините, я не понял вашу команду." in args[0]
    assert "reply_markup" in kwargs
