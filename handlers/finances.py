"""
Обработчики FSM для функции "Личные финансы" (ввод категорий и расходов).
Также включает общий обработчик для команды /cancel.
"""

import logging
import aiosqlite
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states import FinancesForm
from database.db import get_db_connection
from keyboards.reply import main_keyboard

router = Router()

# --- Общий хэндлер для команды /cancel ---
@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Позволяет пользователю отменить любое текущее действие FSM.
    Очищает состояние и возвращает пользователя к основной клавиатуре.
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активного диалога для отмены.")
        logging.info(f"Пользователь {message.from_user.id} попытался отменить, но не было активного диалога.")
        return

    logging.info(f"Пользователь {message.from_user.id} отменил диалог. Состояние: {current_state}")
    await state.clear()

    await message.answer(
        "Действие отменено. Вы вернулись в главное меню.",
        reply_markup=main_keyboard()
    )

# --- Хэндлеры для функции "Личные финансы" ---

@router.message(F.text == "Личные финансы")
async def finances_start(message: Message, state: FSMContext):
    """
    Начинает процесс ввода данных о личных финансах.
    Устанавливает состояние FSM на category1 и запрашивает первую категорию.
    """
    logging.info(f"Пользователь {message.from_user.id} начал ввод личных финансов.")
    await state.set_state(FinancesForm.category1)
    await message.reply("Введите <b>первую</b> категорию расходов (например, 'Продукты', или /cancel для отмены):")

@router.message(FinancesForm.category1)
async def process_category1(message: Message, state: FSMContext):
    """
    Обрабатывает ввод названия первой категории расходов.
    Сохраняет категорию в FSM контекст и переходит к запросу суммы расходов.
    """
    logging.info(f"Пользователь {message.from_user.id} ввел категорию 1: {message.text}")
    await state.update_data(category1=message.text)
    await state.set_state(FinancesForm.expenses1)
    await message.reply("Введите сумму расходов для <b>первой</b> категории (например, 1500.75):")

@router.message(FinancesForm.expenses1)
async def process_expenses1(message: Message, state: FSMContext):
    """
    Обрабатывает ввод суммы расходов для первой категории.
    Сохраняет сумму (преобразуя в float) и переходит к запросу второй категории.
    """
    logging.info(f"Пользователь {message.from_user.id} ввел расходы 1: {message.text}")
    try:
        expenses = float(message.text)
        if expenses < 0:
            raise ValueError("Отрицательное значение")
        await state.update_data(expenses1=expenses)
        await state.set_state(FinancesForm.category2)
        await message.reply("Введите <b>вторую</b> категорию расходов:")
    except ValueError:
        logging.warning(f"Пользователь {message.from_user.id} ввел некорректное число для расходов 1: {message.text}")
        await message.reply("Некорректный ввод. Пожалуйста, введите числовое значение для расходов (например, 100.50). Расходы не могут быть отрицательными.")
        return

@router.message(FinancesForm.category2)
async def process_category2(message: Message, state: FSMContext):
    """
    Обрабатывает ввод названия второй категории расходов.
    Сохраняет категорию в FSM контекст и переходит к запросу суммы расходов.
    """
    logging.info(f"Пользователь {message.from_user.id} ввел категорию 2: {message.text}")
    await state.update_data(category2=message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.reply("Введите сумму расходов для <b>второй</b> категории:")

@router.message(FinancesForm.expenses2)
async def process_expenses2(message: Message, state: FSMContext):
    """
    Обрабатывает ввод суммы расходов для второй категории.
    Сохраняет сумму (преобразуя в float) и переходит к запросу третьей категории.
    """
    logging.info(f"Пользователь {message.from_user.id} ввел расходы 2: {message.text}")
    try:
        expenses = float(message.text)
        if expenses < 0:
            raise ValueError("Отрицательное значение")
        await state.update_data(expenses2=expenses)
        await state.set_state(FinancesForm.category3)
        await message.reply("Введите <b>третью</b> категорию расходов:")
    except ValueError:
        logging.warning(f"Пользователь {message.from_user.id} ввел некорректное число для расходов 2: {message.text}")
        await message.reply("Некорректный ввод. Пожалуйста, введите числовое значение для расходов (например, 100.50). Расходы не могут быть отрицательными.")
        return

@router.message(FinancesForm.category3)
async def process_category3(message: Message, state: FSMContext):
    """
    Обрабатывает ввод названия третьей категории расходов.
    Сохраняет категорию в FSM контекст и переходит к запросу суммы расходов.
    """
    logging.info(f"Пользователь {message.from_user.id} ввел категорию 3: {message.text}")
    await state.update_data(category3=message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.reply("Введите сумму расходов для <b>третьей</b> категории:")

@router.message(FinancesForm.expenses3)
async def process_expenses3(message: Message, state: FSMContext):
    """
    Обрабатывает ввод суммы расходов для третьей категории.
    Сохраняет все собранные данные в базу данных, очищает состояние FSM.
    """
    logging.info(f"Пользователь {message.from_user.id} ввел расходы 3: {message.text}")
    try:
        expenses = float(message.text)
        if expenses < 0:
            raise ValueError("Отрицательное значение")
        await state.update_data(expenses3=expenses)

        data = await state.get_data()
        user_telegram_id = message.from_user.id

        report = (
            "<b>Ваши расходы:</b>\n"
            f"Категория 1: {data.get('category1', 'N/A')} - {data.get('expenses1', 0.0):.2f} RUB\n"
            f"Категория 2: {data.get('category2', 'N/A')} - {data.get('expenses2', 0.0):.2f} RUB\n"
            f"Категория 3: {data.get('category3', 'N/A')} - {expenses:.2f} RUB\n\n"
            "Данные сохранены!"
        )
        await message.answer(report, reply_markup=main_keyboard())


        logging.info(f"Сохранение данных для пользователя {user_telegram_id}: {data}")

        # ИСПРАВЛЕНИЕ: Добавлено 'await' перед get_db_connection()
        async with await get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT 1 FROM users WHERE telegram_id = ?', (user_telegram_id,))
                if await cursor.fetchone():
                    await cursor.execute(
                        '''
                        UPDATE users
                        SET category1 = ?, expenses1 = ?,
                            category2 = ?, expenses2 = ?,
                            category3 = ?, expenses3 = ?
                        WHERE telegram_id = ?
                        ''',
                        (
                            data.get('category1'), data.get('expenses1'),
                            data.get('category2'), data.get('expenses2'),
                            data.get('category3'), expenses,
                            user_telegram_id
                        )
                    )
                    await conn.commit()

                    await state.clear()
                    logging.info(f"Данные о финансах успешно сохранены для пользователя {user_telegram_id}.")
                else:
                    await message.answer("Ошибка: Пользователь не найден в базе данных. Пожалуйста, сначала зарегистрируйтесь.", reply_markup=main_keyboard())
                    await state.clear()
                    logging.warning(f"Пользователь {user_telegram_id} пытался сохранить финансы, но не зарегистрирован.")

    except ValueError:
        logging.warning(f"Пользователь {message.from_user.id} ввел некорректное число для расходов 3: {message.text}")
        await message.reply("Некорректный ввод. Пожалуйста, введите числовое значение для расходов (например, 100.50). Расходы не могут быть отрицательными.")
        return
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных о финансах для пользователя {message.from_user.id}: {e}", exc_info=True)
        await message.answer("Произошла непредвиденная ошибка при сохранении данных. Попробуйте позже.", reply_markup=main_keyboard())
        await state.clear()