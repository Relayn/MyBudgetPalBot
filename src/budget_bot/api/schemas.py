from datetime import date, datetime

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int


class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0)
    expense_date: date


class CreateExpense(ExpenseBase):
    """Схема для создания нового расхода."""

    category_id: int


class ExpenseRead(ExpenseBase):
    """Схема для чтения данных о расходе."""

    id: int
    created_at: datetime
    category: CategoryRead
