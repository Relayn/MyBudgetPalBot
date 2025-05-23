"""
Основной файл для запуска Telegram бота.
Инициализирует бота, диспетчер и регистрирует все обработчики.
"""

import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties # ИМПОРТИРУЕМ ЭТО

# Импортируем функции и роутеры из новых модулей
from database.db import init_db
from handlers import start, registration, exchange, tips, finances, other

# Загружаем переменные окружения из файла .env
load_dotenv()

# Инициализируем токен бота из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logging.error("BOT_TOKEN не найден в переменных окружения. Убедитесь, что он указан в файле .env")
    exit("BOT_TOKEN не найден. Завершение работы.")

# --- Настройка логирования ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = RotatingFileHandler('bot.log', maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# --- Инициализация объекта Bot и Dispatcher ---
# ИСПРАВЛЕНИЕ: Новый способ передачи parse_mode
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

async def main():
    """
    Основная функция, которая запускает процесс опроса (polling) бота.
    Регистрирует все роутеры с хэндлерами.
    """
    await init_db()

    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(exchange.router)
    dp.include_router(tips.router)
    dp.include_router(finances.router)
    dp.include_router(other.router)

    logging.info("Бот запущен. Начинаю опрос...")
    if TOKEN:
        await dp.start_polling(bot)
    else:
        logging.critical("Бот не может быть запущен: отсутствует BOT_TOKEN.")

# Точка входа в программу.
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную.")
    except Exception as e:
        logging.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)