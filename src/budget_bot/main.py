import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from budget_bot.api import routers as api_routers
from budget_bot.db.engine import create_db_and_tables
from budget_bot.handlers import common

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Контекстный менеджер для FastAPI (startup/shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Контекстный менеджер для событий startup и shutdown."""
    logger.info("Запуск приложения...")
    await create_db_and_tables()
    yield
    logger.info("Остановка приложения...")


# --- Создание и конфигурация экземпляра FastAPI ---
# Теперь 'app' находится на уровне модуля и доступен для импорта
app = FastAPI(lifespan=lifespan)

# Подключаем API роутеры
app.include_router(api_routers.router)

# Монтируем директорию с фронтендом для отдачи статики
app.mount("/static", StaticFiles(directory="tma_frontend"), name="static")


@app.get("/")
async def root() -> FileResponse:
    """Отдаем главный HTML файл нашего Mini App."""
    return FileResponse("tma_frontend/index.html")


# --- Основная логика запуска ---
async def main() -> None:
    """Главная асинхронная функция для запуска бота и веб-сервера."""
    load_dotenv()
    bot_token: str | None = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("BOT_TOKEN не найден в .env файле!")
        return

    web_app_url: str | None = os.getenv("WEB_APP_URL")
    if not web_app_url:
        logger.error("WEB_APP_URL не найден в .env файле!")
        return

    # Инициализация бота и диспетчера aiogram
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_router(common.router)
    dp["web_app_url"] = web_app_url

    # Конфигурация для Uvicorn
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",  # nosec B104
        port=8000,
    )
    server = uvicorn.Server(config)

    # Запускаем обе задачи одновременно
    await asyncio.gather(
        dp.start_polling(bot),
        server.serve(),
    )


def run_main() -> None:
    """Функция-обертка для запуска через poetry scripts."""
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот и сервер остановлены.")
        # Исключение не перевыбрасываем, чтобы poetry не писал ошибку
        raise


if __name__ == "__main__":
    run_main()
