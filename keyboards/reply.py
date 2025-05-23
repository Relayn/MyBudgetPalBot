"""
Определение Reply-клавиатур для использования в боте.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard() -> ReplyKeyboardMarkup:
    """
    Создает и возвращает главную Reply-клавиатуру бота.
    """
    button_registr = KeyboardButton(text="Регистрация в телеграм-боте")
    button_exchange_rates = KeyboardButton(text="Курс валют")
    button_tips = KeyboardButton(text="Советы по экономии")
    button_finances = KeyboardButton(text="Личные финансы")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button_registr, button_exchange_rates],
            [button_tips, button_finances]
        ],
        resize_keyboard=True,
        one_time_keyboard=False # Клавиатура остается после использования
    )
    return keyboard