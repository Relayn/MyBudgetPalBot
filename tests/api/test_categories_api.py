from typing import Any, Dict

import pytest
from httpx import AsyncClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

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


# Стратегия для генерации валидных данных пользователя
user_data_strategy: SearchStrategy[Dict[str, Any]] = st.builds(
    dict,
    id=st.integers(min_value=1, max_value=1_000_000_000),
    first_name=st.text(min_size=1, max_size=50),
    last_name=st.text(max_size=50),
    username=st.text(min_size=3, max_size=32),
)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    name=st.text(min_size=1, max_size=100),
    user_data=user_data_strategy,
)
async def test_create_category_with_any_valid_name(
    client: AsyncClient, name: str, user_data: Dict[str, Any]
) -> None:
    """
    Тест (Hypothesis): эндпоинт создания категории успешно обрабатывает
    любое валидное имя для любого сгенерированного пользователя.
    """
    # Каждый запуск использует уникального пользователя, обеспечивая изоляцию
    app.dependency_overrides[get_validated_user_data] = lambda: user_data
    response = await client.post("/api/categories", json={"name": name})
    assert response.status_code == 201
    assert response.json()["name"] == name


# В конец файла tests/api/test_categories_api.py

# Стратегия для генерации невалидных имен: пустая строка ИЛИ слишком длинная
invalid_name_strategy = st.one_of(
    st.just(""),  # Пустая строка
    st.text(min_size=101, max_size=200),  # Слишком длинная строка
)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(invalid_name=invalid_name_strategy)
async def test_create_category_with_any_invalid_name(
    client: AsyncClient,
    user_a_data: Dict[str, Any],
    invalid_name: str,
) -> None:
    """
    Тест (Hypothesis): эндпоинт создания категории возвращает ошибку 422
    для любого невалидного имени (пустого или слишком длинного).
    """
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    response = await client.post("/api/categories", json={"name": invalid_name})
    assert response.status_code == 422
