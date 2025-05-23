"""
Обработчик для команды /start.
"""

import logging
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.reply import main_keyboard # Импортируем клавиатуру

router = Router() # Создаем экземпляр Router для регистрации хэндлеров

@router.message(CommandStart())
async def send_start(message: Message):
    """
    Обрабатывает команду /start.
    Отправляет приветственное сообщение и отображает главную клавиатуру.
    """
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "Привет! Я ваш личный финансовый помощник. Выберите одну из опций в меню:",
        reply_markup=main_keyboard() # Используем функцию для получения клавиатуры
    )