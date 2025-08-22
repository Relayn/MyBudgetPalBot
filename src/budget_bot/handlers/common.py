from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.message(CommandStart())
async def command_start(message: Message, web_app_url: str) -> None:
    """
    Обработчик команды /start. Отправляет приветственное сообщение
    с кнопкой для открытия Web App.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Открыть приложение", web_app=WebAppInfo(url=web_app_url))
    await message.answer(
        "Добро пожаловать в бот для учета финансов! "
        "Нажмите на кнопку ниже, чтобы начать.",
        reply_markup=builder.as_markup(),
    )
