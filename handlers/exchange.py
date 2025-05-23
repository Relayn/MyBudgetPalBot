"""
Обработчик для получения курса валют.
"""

import logging
import os
import aiohttp
from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "Курс валют")
async def exchange_rates(message: Message):
    """
    Обрабатывает нажатие кнопки "Курс валют".
    Получает актуальные курсы валют через API и отправляет их пользователю.
    Использует aiohttp для асинхронных запросов.
    """
    logging.info(f"Пользователь {message.from_user.id} запросил курс валют.")
    api_key_for_exchange = os.getenv("EXCHANGE_RATE_API_KEY")
    if not api_key_for_exchange:
        logging.error("EXCHANGE_RATE_API_KEY не найден в переменных окружения.")
        await message.answer("Ошибка конфигурации: ключ API для курсов валют не найден.")
        return

    url = f"https://v6.exchangerate-api.com/v6/{api_key_for_exchange}/latest/USD"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    error_data = await response.json() # Попытка получить ошибку от API
                    error_message = error_data.get('error-type', 'Неизвестная ошибка API')
                    logging.error(f"Ошибка при получении курсов валют: Статус-код {response.status}, Ошибка API: {error_message}")
                    await message.answer(f"Не удалось получить данные о курсе валют. Ошибка: {error_message}")
                    return

                data = await response.json()

        usd_to_rub = data['conversion_rates']['RUB']
        eur_to_usd = data['conversion_rates']['EUR']
        euro_to_rub = eur_to_usd * usd_to_rub

        await message.answer(
            f"<b>Курсы валют:</b>\n"
            f"1 USD = {usd_to_rub:.2f} RUB\n"
            f"1 EUR = {euro_to_rub:.2f} RUB"
        )
        logging.info(f"Курсы валют успешно отправлены пользователю {message.from_user.id}.")

    except aiohttp.ClientError as e:
        logging.error(f"Ошибка HTTP-запроса при получении курсов валют: {e}")
        await message.answer("Произошла ошибка при подключении к сервису курсов валют. Проверьте ваше интернет-соединение.")
    except KeyError as e:
        logging.error(f"Ошибка парсинга данных курсов валют: Отсутствует ключ {e}. Возможно, структура ответа API изменилась.")
        await message.answer("Произошла ошибка при обработке данных курсов валют. Пожалуйста, сообщите разработчику.")
    except Exception as e:
        logging.error(f"Неизвестная ошибка при получении курсов валют: {e}", exc_info=True)
        await message.answer("Произошла непредвиденная ошибка. Попробуйте позже.")