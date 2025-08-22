# src/budget_bot/db/models.py
from datetime import UTC, date, datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """Модель пользователя."""

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True)
    full_name: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    categories: List["Category"] = Relationship(back_populates="user")


class Category(SQLModel, table=True):
    """Модель категории расходов."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id", index=True)

    user: User = Relationship(back_populates="categories")
    expenses: List["Expense"] = Relationship(back_populates="category")


class Expense(SQLModel, table=True):
    """Модель расхода."""

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    category_id: int = Field(foreign_key="category.id", index=True)
    amount: float
    expense_date: date = Field(default_factory=date.today, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    category: Category = Relationship(back_populates="expenses")
