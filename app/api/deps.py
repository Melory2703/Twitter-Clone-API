"""
Модуль зависимостей (dependencies) для FastAPI.
Содержит функции для извлечения данных из запросов, аутентификации пользователей
и обеспечения доступа к сессии базы данных.
"""

from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models import User


async def get_current_user(
    api_key: str = Header(..., alias="api-key"),
    session: AsyncSession = Depends(get_session),
):
    """
    Получает текущего пользователя из базы данных на основе API-ключа, переданного в заголовке.

    Args:
        api_key (str): Уникальный ключ API для аутентификации пользователя, передаваемый в Header 'api-key'.
        session (AsyncSession): Сессия базы данных для выполнения асинхронных запросов.

    Returns:
        User: Объект пользователя со связанными данными подписчиков и подписок.

    Raises:
        HTTPException: Ошибка 401, если ключ отсутствует или неверный.
    """
    # Формирование запроса к БД с предварительной загрузкой связей (followers и following)
    query = (
        select(User)
        .where(User.api_key == api_key)
        .options(selectinload(User.followers), selectinload(User.following))
    )

    # Выполнение запроса
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    # Проверка, найден ли пользователь
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    return user
