import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional, cast
from urllib.parse import unquote

from fastapi import Header, HTTPException, status

logger = logging.getLogger(__name__)


def parse_init_data(init_data: str) -> Optional[Dict[str, Any]]:
    """
    Парсит строку initData и возвращает данные пользователя в виде словаря.
    Возвращает None, если 'user' ключ отсутствует.
    """
    for item in init_data.split("&"):
        try:
            key, value = item.split("=", 1)
            if key == "user":
                user_data_str = unquote(value)
                return cast(Dict[str, Any], json.loads(user_data_str))
        except ValueError:
            continue
    return None


def validate_init_data(init_data: str, bot_token: str) -> bool:
    """
    Валидирует initData, проверяя HMAC подпись.
    """
    try:
        pairs = [
            (key, unquote(value))
            for key, value in (item.split("=", 1) for item in init_data.split("&"))
        ]

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(pairs, key=lambda x: x[0])
            if key != "hash"
        )

        received_hash = next(
            item.split("=", 1)[1]
            for item in init_data.split("&")
            if item.startswith("hash=")
        )

        secret_key = hmac.new(
            key=b"WebAppData", msg=bot_token.encode(), digestmod=hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256
        ).hexdigest()

        is_valid = calculated_hash == received_hash
        if not is_valid:
            logger.warning("Signature validation FAILED!")
        return is_valid
    except (ValueError, StopIteration, IndexError):
        logger.error("Error during initData validation", exc_info=True)
        return False


def get_validated_user_data(
    x_init_data: str = Header(..., alias="X-Init-Data"),
) -> Dict[str, Any]:
    """
    FastAPI зависимость для валидации initData и извлечения данных пользователя.
    """
    import os

    bot_token = os.getenv("BOT_TOKEN", "")

    if not validate_init_data(x_init_data, bot_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid initData signature",
        )

    user_data = parse_init_data(x_init_data)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User data not found in initData",
        )

    return user_data
