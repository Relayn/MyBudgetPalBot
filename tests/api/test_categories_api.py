from typing import Any, Dict

import pytest
from httpx import AsyncClient

from budget_bot.main import app
from budget_bot.utils.security import get_validated_user_data

pytestmark = pytest.mark.asyncio


async def test_get_categories_empty(
    client: AsyncClient, user_a_data: Dict[str, Any]
) -> None:
    """Тест: получение пустого списка категорий для нового пользователя."""
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    response = await client.get("/api/categories")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_and_get_categories(
    client: AsyncClient, user_a_data: Dict[str, Any]
) -> None:
    """Тест: успешное создание и получение списка категорий."""
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data

    # 1. Создаем две категории
    response1 = await client.post("/api/categories", json={"name": "Продукты"})
    assert response1.status_code == 201
    assert response1.json()["name"] == "Продукты"

    response2 = await client.post("/api/categories", json={"name": "Транспорт"})
    assert response2.status_code == 201
    assert response2.json()["name"] == "Транспорт"

    # 2. Получаем список категорий
    response = await client.get("/api/categories")
    assert response.status_code == 200
    categories = response.json()

    # 3. Проверяем, что в списке 2 категории и они отсортированы по имени
    assert len(categories) == 2
    assert categories[0]["name"] == "Продукты"
    assert categories[1]["name"] == "Транспорт"


async def test_user_b_cannot_see_user_a_categories(
    client: AsyncClient,
    user_a_data: Dict[str, Any],
    user_b_data: Dict[str, Any],
) -> None:
    """
    Тест безопасности: пользователь Б не видит категории пользователя А.
    """
    # 1. Пользователь А создает свою категорию
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    await client.post("/api/categories", json={"name": "Категория А"})

    # 2. Пользователь Б запрашивает свои категории
    app.dependency_overrides[get_validated_user_data] = lambda: user_b_data
    response = await client.get("/api/categories")

    # 3. Убеждаемся, что для пользователя Б список категорий пуст
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",  # Пустая строка
        "a" * 101,  # Слишком длинное имя
    ],
)
async def test_create_category_with_invalid_data(
    client: AsyncClient,
    user_a_data: Dict[str, Any],
    invalid_name: str,
) -> None:
    """
    Тест: попытка создать категорию с невалидными данными (пустое/длинное имя).
    Ожидаем ошибку валидации 422.
    """
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    response = await client.post("/api/categories", json={"name": invalid_name})
    assert response.status_code == 422  # Unprocessable Entity
