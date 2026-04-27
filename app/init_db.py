"""
Модуль для инициализации структуры базы данных.
Создает все таблицы, определенные в моделях приложения, на основе метаданных SQLAlchemy.
"""

import asyncio
from app.database import engine, Base

from app.models import User, Tweet, Media  # noqa: F401


async def init_models():
    """
    Инициализирует таблицы в базе данных.
    Использует асинхронное соединение для выполнения синхронного метода create_all.

    Args:
        None

    Returns:
        None: Функция выполняет создание таблиц в БД и не возвращает значение.
    """
    async with engine.begin() as conn:
        # Полная очистка базы перед созданием (при необходимости):
        # await conn.run_sync(Base.metadata.drop_all)

        print("Создание таблиц...")
        # Создание всех таблиц, зарегистрированных в Base.metadata
        await conn.run_sync(Base.metadata.create_all)
        print("Готово!")


if __name__ == "__main__":
    # Запуск асинхронного цикла событий для выполнения инициализации моделей
    asyncio.run(init_models())
