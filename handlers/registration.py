"""
Обработчик для регистрации пользователя.
"""

import logging
import aiosqlite
from aiogram import Router, F
from aiogram.types import Message

from database.db import (
    get_db_connection,
)  # Импортируем функцию для получения соединения

router = Router()


@router.message(F.text == "Регистрация в телеграм-боте")
async def registration(message: Message):
    """
    Обрабатывает нажатие кнопки "Регистрация в телеграм-боте".
    Проверяет, зарегистрирован ли пользователь, и регистрирует его, если нет.
    """
    user_telegram_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f"Пользователь {user_telegram_id} пытается зарегистрироваться.")

    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = ?", (user_telegram_id,)
                )
                user = await cursor.fetchone()

                if user:
                    await message.answer("Вы уже зарегистрированы!")
                    logging.info(
                        f"Пользователь {user_telegram_id} уже зарегистрирован."
                    )
                else:
                    await cursor.execute(
                        "INSERT INTO users (telegram_id, name) VALUES (?, ?)",
                        (user_telegram_id, user_full_name),
                    )
                    await conn.commit()
                    await message.answer("Вы успешно зарегистрированы!")
                    logging.info(
                        f"Пользователь {user_telegram_id} ({user_full_name}) успешно зарегистрирован."
                    )
    except Exception as e:
        logging.error(
            f"Ошибка при регистрации пользователя {user_telegram_id}: {e}",
            exc_info=True,
        )
        await message.answer(
            "Произошла ошибка при регистрации. Пожалуйста, попробуйте позже."
        )
