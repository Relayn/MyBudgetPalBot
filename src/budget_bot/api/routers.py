import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from budget_bot.db.models import Category, Expense, User
from budget_bot.db.session import get_session
from budget_bot.utils.security import get_validated_user_data

from .schemas import (
    CategoryCreate,
    CategoryRead,
    CreateExpense,
    ExpenseRead,
)

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


# --- Эндпоинты для Категорий ---


@router.get("/categories", response_model=List[CategoryRead])
async def get_categories(
    user_data: Dict[str, Any] = Depends(get_validated_user_data),
    session: AsyncSession = Depends(get_session),
) -> List[Category]:
    """Возвращает список категорий для текущего пользователя."""
    telegram_id = user_data.get("id")
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().one_or_none()
    if not user:
        return []

    result = await session.execute(
        select(Category).where(Category.user_id == user.id).order_by(Category.name)
    )
    categories = result.scalars().all()
    return list(categories)


@router.post("/categories", response_model=CategoryRead, status_code=201)
async def create_category(
    category_data: CategoryCreate,
    user_data: Dict[str, Any] = Depends(get_validated_user_data),
    session: AsyncSession = Depends(get_session),
) -> Category:
    """Создает новую категорию для текущего пользователя."""
    telegram_id = user_data.get("id")
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().one_or_none()
    if not user:
        # В тестах пользователь еще не создан, создадим его здесь
        full_name = user_data.get("first_name", "")
        if last_name := user_data.get("last_name"):
            full_name += f" {last_name}"
        user = User(telegram_id=telegram_id, full_name=full_name.strip())
        session.add(user)
        await session.commit()
        await session.refresh(user)

    new_category = Category.model_validate(category_data, update={"user_id": user.id})
    session.add(new_category)
    await session.commit()
    await session.refresh(new_category)
    return new_category


# --- Эндпоинты для Расходов ---


async def get_user_from_db(telegram_id: int, session: AsyncSession) -> User:
    """Вспомогательная функция для получения пользователя."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalars().one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User not found."
        )
    return user


async def verify_category_owner(
    category_id: int, user_id: int, session: AsyncSession
) -> None:
    """Проверяет, что категория принадлежит пользователю."""
    result = await session.execute(select(Category).where(Category.id == category_id))
    category = result.scalars().one_or_none()
    if not category or category.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or access denied.",
        )


@router.post("/expenses", status_code=201)
async def add_expense(
    expense_data: CreateExpense,
    user_data: Dict[str, Any] = Depends(get_validated_user_data),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Добавляет новый расход."""
    telegram_id = user_data.get("id")
    if not isinstance(telegram_id, int):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user ID in initData.",
        )
    user = await get_user_from_db(telegram_id, session)
    await verify_category_owner(expense_data.category_id, user.id, session)

    new_expense = Expense.model_validate(expense_data, update={"user_id": user.id})
    session.add(new_expense)
    await session.commit()
    return JSONResponse(
        content={"message": "Expense added successfully"}, status_code=201
    )


@router.get("/expenses", response_model=List[ExpenseRead])
async def get_expenses(
    user_data: Dict[str, Any] = Depends(get_validated_user_data),
    session: AsyncSession = Depends(get_session),
) -> List[Expense]:
    """Возвращает список расходов текущего пользователя."""
    # В этом эндпоинте не бросаем ошибку, если юзера нет, а возвращаем [].
    # Это штатная ситуация для нового пользователя.
    result = await session.execute(
        select(User).where(User.telegram_id == user_data.get("id"))
    )
    user = result.scalars().one_or_none()
    if not user:
        return []

    statement = (
        select(Expense)
        .where(Expense.user_id == user.id)
        .options(selectinload(Expense.category))
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
    )
    result = await session.execute(statement)
    expenses = result.scalars().all()
    return list(expenses)


@router.put("/expenses/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: int,
    expense_data: CreateExpense,
    user_data: Dict[str, Any] = Depends(get_validated_user_data),
    session: AsyncSession = Depends(get_session),
) -> Expense:
    """Обновляет расход."""
    telegram_id = user_data.get("id")
    if not isinstance(telegram_id, int):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user ID in initData.",
        )
    user = await get_user_from_db(telegram_id, session)
    await verify_category_owner(expense_data.category_id, user.id, session)

    result = await session.execute(
        select(Expense)
        .where(Expense.id == expense_id)
        .options(selectinload(Expense.category))
    )
    expense = result.scalars().one_or_none()

    if not expense or expense.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found or access denied.",
        )

    update_data = expense_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(expense, key, value)

    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: int,
    user_data: Dict[str, Any] = Depends(get_validated_user_data),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Удаляет расход."""
    telegram_id = user_data.get("id")
    if not isinstance(telegram_id, int):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user ID in initData.",
        )
    user = await get_user_from_db(telegram_id, session)
    result = await session.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalars().one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found.",
        )

    if expense.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you can only delete your own expenses.",
        )

    await session.delete(expense)
    await session.commit()
    return None
