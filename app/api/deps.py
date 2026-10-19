"""
Модуль зависимостей (dependencies) для FastAPI.
Собирает сервисы из сессии базы данных и определяет текущего пользователя по заголовку api-key.
"""

from fastapi import Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models import User
from app.services.media_service import MediaService
from app.services.tweet_service import TweetService
from app.services.user_service import UserService


async def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    """Создаёт сервис пользователей на сессии текущего запроса."""
    return UserService(session)


async def get_tweet_service(
    session: AsyncSession = Depends(get_session),
) -> TweetService:
    """Создаёт сервис твитов на сессии текущего запроса."""
    return TweetService(session)


async def get_media_service(
    session: AsyncSession = Depends(get_session),
) -> MediaService:
    """Создаёт сервис медиафайлов на сессии текущего запроса."""
    return MediaService(session)


async def get_current_user(
    api_key: str = Header(..., alias="api-key"),
    user_service: UserService = Depends(get_user_service),
) -> User:
    """
    Получает текущего пользователя на основе API-ключа, переданного в заголовке.

    Args:
        api_key (str): Уникальный ключ API для аутентификации пользователя, передаваемый в Header 'api-key'.
        user_service (UserService): Сервис пользователей.

    Returns:
        User: Объект пользователя со связанными данными подписчиков и подписок.

    Raises:
        UnauthorizedError: Ошибка 401, если ключ неверный (превращается в ответ в app/main.py).
    """
    return await user_service.authenticate(api_key)
