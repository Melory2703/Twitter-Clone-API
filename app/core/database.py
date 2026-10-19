"""
Модуль настройки подключения к базе данных.
Использует SQLAlchemy с асинхронным драйвером.
"""

import os
from dotenv import load_dotenv
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

# Загрузка URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("Переменная окружения DATABASE_URL не установлена")

# Создаем асинхронный "движок" (engine) для связи с базой.
# Вывод SQL-запросов в консоль включается переменной DB_ECHO (true/1), по умолчанию выключен.
DB_ECHO = os.getenv("DB_ECHO", "false").strip().lower() in ("true", "1")
engine = create_async_engine(DATABASE_URL, echo=DB_ECHO)

# Фабрика сессий.
# expire_on_commit=False отключает автоматическое обновление объектов после коммита,
# что критически важно для корректной работы асинхронности.
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.
    От него наследуются все таблицы проекта.
    """

    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Функция-зависимость (Dependency) для FastAPI.
    Обеспечивает автоматическое открытие и закрытие сессии базы данных
    для каждого входящего HTTP-запроса.

    Yields:
        AsyncSession: Объект сессии для выполнения операций с БД.
    """
    async with async_session() as session:
        yield session
