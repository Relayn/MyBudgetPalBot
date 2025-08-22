# Dockerfile

# --- Этап 1: Сборщик зависимостей ---
FROM python:3.11-slim as builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем Poetry
RUN pip install poetry

# Копируем файлы для установки зависимостей
COPY poetry.lock pyproject.toml ./

# Устанавливаем зависимости в виртуальное окружение внутри /app/.venv
# --no-root: не устанавливать сам проект, только зависимости
# --no-dev: не устанавливать dev-зависимости (pytest, ruff и т.д.)
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-dev


# --- Этап 2: Финальный образ ---
FROM python:3.11-slim

WORKDIR /app

# Копируем созданное виртуальное окружение с зависимостями из сборщика
COPY --from=builder /app/.venv ./.venv

# Устанавливаем PATH, чтобы можно было запускать команды из .venv/bin
ENV PATH="/app/.venv/bin:$PATH"

# Копируем исходный код нашего приложения
COPY src/ ./src/
COPY tma_frontend/ ./tma_frontend/

# Копируем файл .env.example, чтобы показать, какие переменные нужны
# В реальном проде .env будет монтироваться или передаваться через оркестратор
COPY .env.example .

# Открываем порт, на котором работает FastAPI
EXPOSE 8000

# Команда для запуска приложения
CMD ["poetry", "run", "start"]
