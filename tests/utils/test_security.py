import hashlib
import hmac
import json
from urllib.parse import quote

import pytest

from budget_bot.utils.security import parse_init_data, validate_init_data


def test_parse_init_data_success() -> None:
    """Тест: успешный парсинг корректной строки initData."""
    user_data = {
        "id": 12345,
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe",
        "language_code": "en",
    }
    user_data_json = json.dumps(user_data)
    user_data_quoted = quote(user_data_json)

    init_data_str = f"auth_date=1672531200&hash=somehash&user={user_data_quoted}"

    parsed_data = parse_init_data(init_data_str)
    assert parsed_data is not None
    assert parsed_data["id"] == 12345
    assert parsed_data["username"] == "johndoe"


@pytest.mark.parametrize(
    "malformed_init_data",
    [
        "auth_date=123&hash=abc",  # Нет ключа 'user'
        "user=&auth_date=123",  # Пустое значение 'user'
        "user=not_a_json",  # Некорректный JSON
        "invalid_string",  # Просто некорректная строка
    ],
)
def test_parse_init_data_malformed(malformed_init_data: str) -> None:
    """Тест: обработка некорректных строк initData."""
    assert parse_init_data(malformed_init_data) is None


def test_validate_init_data_success() -> None:
    """Тест: успешная валидация корректной подписи."""
    bot_token = "6910699622:AAHl_s_jUnqD0obO23423423423423423_o"
    user_json = (
        '{"id":12345,"first_name":"Test","last_name":"User","username":"testuser"}'
    )
    data_pairs = [
        ("auth_date", "1724315752"),
        ("user", user_json),
    ]

    # Воспроизводим алгоритм подписи, чтобы сгенерировать правильный хэш
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data_pairs, key=lambda x: x[0])
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=bot_token.encode(), digestmod=hashlib.sha256
    ).digest()
    correct_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    init_data_str = f"{data_check_string.replace('\n', '&')}&hash={correct_hash}"

    assert validate_init_data(init_data_str, bot_token) is True


def test_validate_init_data_tampered() -> None:
    """Тест: валидация проваливается, если данные были подделаны."""
    bot_token = "6910699622:AAHl_s_jUnqD0obO23423423423423423_o"
    # Данные, для которых был сгенерирован хэш
    original_user_data = (
        '{"id":12345,"first_name":"Test","last_name":"User","username":"testuser"}'
    )
    data_pairs = [
        ("auth_date", "1724315752"),
        ("user", original_user_data),
    ]
    # ... генерируем правильный хэш для ОРИГИНАЛЬНЫХ данных ...
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data_pairs, key=lambda x: x[0])
    )
    secret_key = hmac.new(
        key=b"WebAppData", msg=bot_token.encode(), digestmod=hashlib.sha256
    ).digest()
    correct_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # А теперь имитируем атаку: кто-то перехватил данные и изменил ID
    tampered_user_data = (
        '{"id":99999,"first_name":"Test","last_name":"User","username":"testuser"}'
    )
    tampered_init_data_str = (
        f"auth_date=1724315752&user={quote(tampered_user_data)}&hash={correct_hash}"
    )

    assert validate_init_data(tampered_init_data_str, bot_token) is False
