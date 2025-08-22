from unittest.mock import AsyncMock

import pytest
from aiogram.types import WebAppInfo

from budget_bot.handlers.common import command_start

pytestmark = pytest.mark.asyncio


async def test_command_start() -> None:
    """Тест: хэндлер /start отправляет корректное сообщение с кнопкой."""
    # Создаем мок-объект Message с методом answer, который тоже является моком
    mock_message = AsyncMock()
    test_web_app_url = "https://test.app"

    # Вызываем хэндлер
    await command_start(mock_message, web_app_url=test_web_app_url)

    # Проверяем, что метод answer был вызван ровно один раз
    mock_message.answer.assert_called_once()

    # Проверяем аргументы, с которыми был вызван метод answer
    # call_args[0] - это позиционные аргументы, call_args[1] - именованные
    args, kwargs = mock_message.answer.call_args
    assert "Добро пожаловать" in args[0]
    assert "reply_markup" in kwargs

    # Проверяем содержимое клавиатуры
    keyboard = kwargs["reply_markup"]
    button = keyboard.inline_keyboard[0][0]
    assert isinstance(button.web_app, WebAppInfo)
    assert button.web_app.url == test_web_app_url
