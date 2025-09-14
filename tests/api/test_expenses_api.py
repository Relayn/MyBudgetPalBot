from datetime import date
from typing import Any, Dict

import pytest
from httpx import AsyncClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy
from pytest import approx

from budget_bot.main import app
from budget_bot.utils.security import get_validated_user_data

pytestmark = pytest.mark.asyncio


async def test_get_expenses_empty(
    client: AsyncClient, user_a_data: Dict[str, Any]
) -> None:
    """Тест: получение пустого списка расходов для нового пользователя."""
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    response = await client.get("/api/expenses")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_and_get_expense(
    client: AsyncClient, user_a_data: Dict[str, Any]
) -> None:
    """
    Тест: успешное создание категории, затем расхода,
    и последующее получение этого расхода.
    """
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data

    # 1. Создаем категорию, т.к. она нужна для создания расхода
    category_data = {"name": "Продукты"}
    response = await client.post("/api/categories", json=category_data)
    assert response.status_code == 201
    created_category = response.json()
    assert created_category["name"] == "Продукты"

    # 2. Создаем расход
    expense_data = {
        "category_id": created_category["id"],
        "amount": 123.45,
        "expense_date": date.today().isoformat(),
    }
    response = await client.post("/api/expenses", json=expense_data)
    assert response.status_code == 201
    assert response.json() == {"message": "Expense added successfully"}

    # 3. Получаем список расходов и проверяем его содержимое
    response = await client.get("/api/expenses")
    assert response.status_code == 200
    expenses_list = response.json()
    assert len(expenses_list) == 1
    expense = expenses_list[0]
    assert expense["amount"] == approx(123.45)
    assert expense["category"]["id"] == created_category["id"]
    assert expense["category"]["name"] == "Продукты"


async def test_update_expense(client: AsyncClient, user_a_data: Dict[str, Any]) -> None:
    """Тест: успешное обновление расхода."""
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    # 1. Создаем категорию и расход
    cat_resp = await client.post("/api/categories", json={"name": "Такси"})
    category_id = cat_resp.json()["id"]
    exp_data = {
        "category_id": category_id,
        "amount": 500.00,
        "expense_date": "2025-08-21",
    }
    exp_resp = await client.post("/api/expenses", json=exp_data)
    assert exp_resp.status_code == 201

    # Получаем ID созданного расхода
    get_resp = await client.get("/api/expenses")
    expense_id = get_resp.json()[0]["id"]

    # 2. Обновляем расход
    updated_data = {
        "category_id": category_id,
        "amount": 555.55,
        "expense_date": "2025-08-22",
    }
    update_resp = await client.put(f"/api/expenses/{expense_id}", json=updated_data)
    assert update_resp.status_code == 200
    updated_expense = update_resp.json()
    assert updated_expense["amount"] == approx(555.55)
    assert updated_expense["expense_date"] == "2025-08-22"


async def test_delete_expense(client: AsyncClient, user_a_data: Dict[str, Any]) -> None:
    """Тест: успешное удаление расхода."""
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    # 1. Создаем категорию и расход
    cat_resp = await client.post("/api/categories", json={"name": "Еда"})
    exp_data = {
        "category_id": cat_resp.json()["id"],
        "amount": 100.00,
        "expense_date": date.today().isoformat(),
    }
    await client.post("/api/expenses", json=exp_data)

    # Получаем ID созданного расхода
    get_resp = await client.get("/api/expenses")
    assert len(get_resp.json()) == 1
    expense_id = get_resp.json()[0]["id"]

    # 2. Удаляем расход
    delete_resp = await client.delete(f"/api/expenses/{expense_id}")
    assert delete_resp.status_code == 204

    # 3. Проверяем, что список расходов теперь пуст
    final_get_resp = await client.get("/api/expenses")
    assert final_get_resp.status_code == 200
    assert final_get_resp.json() == []


async def test_user_cannot_delete_foreign_expense(
    client: AsyncClient,
    user_a_data: Dict[str, Any],
    user_b_data: Dict[str, Any],
) -> None:
    """
    Тест безопасности: пользователь Б не может удалить расход пользователя А.
    """
    # 1. Пользователь А создает свой расход
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    cat_resp_a = await client.post("/api/categories", json={"name": "Категория А"})
    exp_data_a = {
        "category_id": cat_resp_a.json()["id"],
        "amount": 100,
        "expense_date": date.today().isoformat(),
    }
    await client.post("/api/expenses", json=exp_data_a)
    expense_id_a = (await client.get("/api/expenses")).json()[0]["id"]

    # 2. Пользователь Б пытается удалить расход Пользователя А
    app.dependency_overrides[get_validated_user_data] = lambda: user_b_data
    # (Сначала создадим пользователя Б в БД, создав для него категорию)
    await client.post("/api/categories", json={"name": "Категория Б"})
    delete_resp = await client.delete(f"/api/expenses/{expense_id_a}")
    assert delete_resp.status_code in [403, 404]

    # 3. Проверяем, что расход Пользователя А остался на месте
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    get_resp = await client.get("/api/expenses")
    assert len(get_resp.json()) == 1
    assert get_resp.json()[0]["id"] == expense_id_a


async def test_user_cannot_update_foreign_expense(
    client: AsyncClient,
    user_a_data: Dict[str, Any],
    user_b_data: Dict[str, Any],
) -> None:
    """
    Тест безопасности: пользователь Б не может обновить расход пользователя А.
    """
    # 1. Пользователь А создает свой расход
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    cat_resp_a = await client.post("/api/categories", json={"name": "Категория А"})
    category_id_a = cat_resp_a.json()["id"]
    exp_data_a = {
        "category_id": category_id_a,
        "amount": 100.00,
        "expense_date": "2025-08-20",
    }
    await client.post("/api/expenses", json=exp_data_a)
    expense_a = (await client.get("/api/expenses")).json()[0]
    expense_id_a = expense_a["id"]

    # 2. Пользователь Б пытается обновить расход Пользователя А
    app.dependency_overrides[get_validated_user_data] = lambda: user_b_data
    # (Сначала создадим пользователя Б и его категорию в БД)
    await client.post("/api/categories", json={"name": "Категория Б"})
    update_data = {
        "category_id": category_id_a,  # Пытаемся использовать категорию А
        "amount": 999.99,
        "expense_date": "2025-08-21",
    }
    update_resp = await client.put(f"/api/expenses/{expense_id_a}", json=update_data)
    assert update_resp.status_code in [403, 404]

    # 3. Проверяем, что расход Пользователя А не изменился
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    get_resp = await client.get("/api/expenses")
    assert len(get_resp.json()) == 1
    final_expense_a = get_resp.json()[0]
    assert final_expense_a["id"] == expense_id_a
    assert final_expense_a["amount"] == approx(100.00)


async def test_update_non_existent_expense(
    client: AsyncClient, user_a_data: Dict[str, Any]
) -> None:
    """Тест: попытка обновить несуществующий расход."""
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    # Создаем категорию, чтобы было с чем работать
    cat_resp = await client.post("/api/categories", json={"name": "Категория"})
    category_id = cat_resp.json()["id"]

    updated_data = {
        "category_id": category_id,
        "amount": 999.99,
        "expense_date": "2025-08-22",
    }
    # Пытаемся обновить расход с несуществующим ID 999
    update_resp = await client.put("/api/expenses/999", json=updated_data)
    assert update_resp.status_code == 404


async def test_delete_non_existent_expense(
    client: AsyncClient, user_a_data: Dict[str, Any]
) -> None:
    """Тест: попытка удалить несуществующий расход."""
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    # Сначала создаем пользователя А в БД, выполнив любое действие
    await client.post("/api/categories", json={"name": "Категория для setup"})

    # Теперь, когда пользователь существует, get_user_from_db вернет его,
    # и код дойдет до проверки существования расхода.
    delete_resp = await client.delete("/api/expenses/999")
    assert delete_resp.status_code == 404


async def test_create_expense_with_foreign_category(
    client: AsyncClient,
    user_a_data: Dict[str, Any],
    user_b_data: Dict[str, Any],
) -> None:
    """
    Тест безопасности: пользователь Б не может создать расход
    с категорией пользователя А.
    """
    # 1. Пользователь А создает свою категорию
    app.dependency_overrides[get_validated_user_data] = lambda: user_a_data
    cat_resp_a = await client.post("/api/categories", json={"name": "Категория А"})
    category_id_a = cat_resp_a.json()["id"]

    # 2. Пользователь Б пытается создать расход с категорией пользователя А
    app.dependency_overrides[get_validated_user_data] = lambda: user_b_data
    # Сначала создаем пользователя Б в БД, чтобы get_user_from_db не вернул 403
    await client.post("/api/categories", json={"name": "Категория Б для setup"})

    expense_data = {
        "category_id": category_id_a,
        "amount": 500,
        "expense_date": date.today().isoformat(),
    }
    response = await client.post("/api/expenses", json=expense_data)
    # Теперь ожидаем 404, так как verify_category_owner не найдет
    # категорию с ID category_id_a у пользователя Б.
    assert response.status_code == 404


# Стратегия для генерации валидных данных пользователя
user_data_strategy: SearchStrategy[Dict[str, Any]] = st.builds(
    dict,
    id=st.integers(min_value=1, max_value=1_000_000_000),
    first_name=st.text(min_size=1, max_size=50),
)


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=1000)
@given(
    user_data=user_data_strategy,
    amount=st.floats(
        min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False
    ),
    expense_date=st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31)),
)
async def test_create_expense_with_any_valid_data(
    client: AsyncClient,
    user_data: Dict[str, Any],
    amount: float,
    expense_date: date,
) -> None:
    """
    Тест (Hypothesis): эндпоинт создания расхода успешно обрабатывает
    любые валидные данные (сумма, дата) для любого пользователя.
    """
    app.dependency_overrides[get_validated_user_data] = lambda: user_data

    # Шаг 1: Создаем категорию для этого пользователя, чтобы получить валидный ID
    cat_resp = await client.post("/api/categories", json={"name": "Generated Category"})
    assert cat_resp.status_code == 201
    category_id = cat_resp.json()["id"]

    # Шаг 2: Создаем расход с использованием этого ID и сгенерированных данных
    expense_data = {
        "category_id": category_id,
        "amount": amount,
        "expense_date": expense_date.isoformat(),
    }
    exp_resp = await client.post("/api/expenses", json=expense_data)

    # Шаг 3: Проверяем, что расход успешно создан
    assert exp_resp.status_code == 201
    assert exp_resp.json() == {"message": "Expense added successfully"}


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    user_data=user_data_strategy,
    # Генерируем либо невалидную сумму, либо заведомо несуществующий ID
    amount=st.floats(max_value=0, allow_nan=False, allow_infinity=False),
    non_existent_category_id=st.integers(min_value=9999, max_value=100000),
)
async def test_create_expense_with_invalid_data(
    client: AsyncClient,
    user_data: Dict[str, Any],
    amount: float,
    non_existent_category_id: int,
) -> None:
    """
    Тест (Hypothesis): эндпоинт создания расхода возвращает ошибки
    на невалидные данные (сумма <= 0 или несуществующая категория).
    """
    app.dependency_overrides[get_validated_user_data] = lambda: user_data
    # Сначала создаем пользователя в БД, чтобы он точно существовал
    cat_resp = await client.post("/api/categories", json={"name": "Setup Category"})
    valid_category_id = cat_resp.json()["id"]

    # Сценарий 1: Невалидная сумма
    expense_data_invalid_amount = {
        "category_id": valid_category_id,
        "amount": amount,
        "expense_date": date.today().isoformat(),
    }
    response1 = await client.post("/api/expenses", json=expense_data_invalid_amount)
    assert response1.status_code == 422

    # Сценарий 2: Несуществующая категория
    expense_data_invalid_category = {
        "category_id": non_existent_category_id,
        "amount": 100.0,
        "expense_date": date.today().isoformat(),
    }
    response2 = await client.post("/api/expenses", json=expense_data_invalid_category)
    assert response2.status_code == 404
