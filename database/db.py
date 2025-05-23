# database/db.py

import aiosqlite
import logging
from contextlib import asynccontextmanager

# Удаляем глобальные conn и cursor, они больше не нужны
# conn = None
# cursor = None


async def init_db(db_name: str = "user.db"):
    """
    Инициализирует соединение с базой данных SQLite и создает необходимые таблицы, если они не существуют.
    Эта функция теперь асинхронная.

    Args:
        db_name: Имя файла базы данных.
    """
    logging.info(f"Инициализация базы данных: {db_name}")
    async with aiosqlite.connect(db_name) as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    name TEXT,
                    category1 TEXT,
                    category2 TEXT,
                    category3 TEXT,
                    expenses1 REAL,
                    expenses2 REAL,
                    expenses3 REAL
                )
            """
            )
            await conn.commit()
            logging.info("База данных успешно инициализирована.")


@asynccontextmanager
async def get_db_connection(db_name: str = "user.db"):
    """
    Асинхронный контекстный менеджер для получения соединения с базой данных.
    Гарантирует правильное закрытие соединения после использования.

    Args:
        db_name: Имя файла базы данных.

    Yields:
        aiosqlite.Connection: Соединение с базой данных.
    """
    conn = None
    try:
        conn = await aiosqlite.connect(db_name)
        yield conn
    finally:
        if conn:
            await conn.close()
