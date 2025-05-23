"""
Обработчик для неизвестных команд или сообщений.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message

from keyboards.reply import main_keyboard # Импортируем клавиатуру

router = Router()

@router.message() # Этот хэндлер будет срабатывать на любые сообщения, не обработанные другими хэндлерами
async def handle_unknown_message(message: Message):
    """
    Обрабатывает сообщения, которые не соответствуют ни одной из зарегистрированных команд или состояний.
    """
    logging.info(f"Получено неизвестное сообщение от пользователя {message.from_user.id}: '{message.text}'")
    await message.answer(
        "Извините, я не понял вашу команду. Пожалуйста, выберите одну из опций в меню.",
        reply_markup=main_keyboard()
    )