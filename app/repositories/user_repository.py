"""
Репозиторий пользователей: все запросы SQLAlchemy к таблице users и связи подписок.
Транзакцией (commit) управляет сервис.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import User


class UserRepository:
    """Доступ к данным пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_api_key(self, api_key: str) -> User | None:
        """Возвращает пользователя по API-ключу вместе с подписчиками и подписками."""
        query = (
            select(User)
            .where(User.api_key == api_key)
            .options(selectinload(User.followers), selectinload(User.following))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает пользователя по ID вместе с подписчиками и подписками."""
        query = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.followers), selectinload(User.following))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
