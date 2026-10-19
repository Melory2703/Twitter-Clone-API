"""
Сервис твитов: лента, создание, лайки и удаление.
Содержит бизнес-правила и управляет транзакцией (commit).
"""

import logging
from collections.abc import Sequence
from typing import Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadRequestError, DatabaseError, NotFoundError
from app.models import Media, Tweet, User
from app.repositories.media_repository import MediaRepository
from app.repositories.tweet_repository import TweetRepository
from app.services.media_service import delete_media_files

logger = logging.getLogger(__name__)


def format_tweet(tweet: Tweet) -> dict[str, Any]:
    """Преобразует твит в словарь формата TweetSchema (у модели лайки лежат в likes_users)."""
    return {
        "id": tweet.id,
        "content": tweet.content,
        "attachments": [media.file_path for media in tweet.attachments],
        "author": {
            "id": tweet.author.id,
            "name": tweet.author.name,
        },
        "likes": [
            {"user_id": user.id, "name": user.name} for user in tweet.likes_users
        ],
    }


class TweetService:
    """Бизнес-логика работы с твитами."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tweets = TweetRepository(session)
        self.medias = MediaRepository(session)

    async def get_feed(self, current_user: User) -> list[dict[str, Any]]:
        """Лента: собственные твиты и твиты тех, на кого подписан current_user."""
        author_ids = [user.id for user in current_user.following]
        author_ids.append(current_user.id)

        try:
            tweets = await self.tweets.get_feed(author_ids)
        except SQLAlchemyError as error:
            logger.exception("Error in GET /tweets database execution")
            raise DatabaseError("Database error") from error

        return [format_tweet(tweet) for tweet in tweets]

    async def create(
        self, current_user: User, content: str, media_ids: list[int]
    ) -> Tweet:
        """Создаёт твит и привязывает к нему загруженные ранее медиа; неизвестный ID медиа - BadRequestError."""
        medias = await self._get_medias_or_fail(media_ids)
        tweet = await self.tweets.create(content, current_user.id)
        await self.medias.attach_to_tweet(medias, tweet.id)
        await self.session.commit()
        return tweet

    async def like(self, current_user: User, tweet_id: int) -> None:
        """Ставит лайк (повторный лайк ничего не меняет); нет твита - NotFoundError."""
        tweet = await self.tweets.get_with_likes(tweet_id)
        if not tweet:
            raise NotFoundError("Tweet not found")

        if current_user not in tweet.likes_users:
            tweet.likes_users.append(current_user)
            await self.session.commit()

    async def unlike(self, current_user: User, tweet_id: int) -> None:
        """Убирает лайк; если твита или лайка нет, ничего не делает и ошибку не поднимает."""
        tweet = await self.tweets.get_with_likes(tweet_id)
        if not tweet:
            return

        user_to_remove = next(
            (user for user in tweet.likes_users if user.id == current_user.id), None
        )
        if user_to_remove:
            tweet.likes_users.remove(user_to_remove)
            await self.session.commit()

    async def delete(self, current_user: User, tweet_id: int) -> None:
        """Удаляет твит. Разрешено только автору, иначе (или если твита нет) - NotFoundError."""
        tweet = await self.tweets.get_by_id_and_author(tweet_id, current_user.id)
        if not tweet:
            raise NotFoundError("Tweet not found or access denied")

        file_paths = [media.file_path for media in tweet.attachments]
        await self.tweets.delete(tweet)
        await self.session.commit()
        await delete_media_files(file_paths)

    async def _get_medias_or_fail(self, media_ids: list[int]) -> Sequence[Media]:
        """Возвращает медиа по ID; если какого-то нет в БД, поднимает BadRequestError со списком ID."""
        if not media_ids:
            return []
        medias = await self.medias.get_by_ids(media_ids)
        missing = set(media_ids) - {media.id for media in medias}
        if missing:
            missing_ids = ", ".join(str(media_id) for media_id in sorted(missing))
            raise BadRequestError(f"Media not found: {missing_ids}")
        return medias
