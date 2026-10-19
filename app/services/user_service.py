"""
Сервис пользователей: аутентификация по API-ключу, профили, подписки и отписки.
Содержит бизнес-правила и управляет транзакцией (commit).
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestError, NotFoundError, UnauthorizedError
from app.models import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Бизнес-логика работы с пользователями."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def authenticate(self, api_key: str) -> User:
        """Возвращает пользователя по API-ключу или поднимает UnauthorizedError."""
        user = await self.users.get_by_api_key(api_key)
        if not user:
            raise UnauthorizedError("Invalid API Key")
        return user

    async def get_profile(self, user_id: int) -> User:
        """Возвращает профиль пользователя или поднимает NotFoundError."""
        user = await self.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def follow(self, current_user: User, user_id: int) -> None:
        """Подписывает current_user на пользователя user_id (повторная подписка ничего не меняет)."""
        if current_user.id == user_id:
            raise BadRequestError("You cannot follow yourself")

        target_user = await self.users.get_by_id(user_id)
        if not target_user:
            raise NotFoundError("User not found")

        if target_user not in current_user.following:
            current_user.following.append(target_user)
            await self.session.commit()

    async def unfollow(self, current_user: User, user_id: int) -> None:
        """Отписывает current_user от пользователя user_id (если подписки не было, ничего не делает)."""
        target_user = next(
            (followed for followed in current_user.following if followed.id == user_id),
            None,
        )
        if target_user:
            current_user.following.remove(target_user)
            await self.session.commit()
