"""
Репозиторий твитов: все запросы SQLAlchemy к таблицам tweets и likes.
Транзакцией (commit) управляет сервис.
"""

from collections.abc import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Tweet, likes


class TweetRepository:
    """Доступ к данным твитов и лайков."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_feed(self, author_ids: list[int]) -> Sequence[Tweet]:
        """Возвращает твиты указанных авторов: сначала с наибольшим числом лайков, затем новые."""
        query = (
            select(Tweet)
            .outerjoin(likes, Tweet.id == likes.c.tweet_id)
            .where(Tweet.author_id.in_(author_ids))
            .group_by(Tweet.id)
            .order_by(
                func.count(likes.c.user_id).desc(),
                Tweet.id.desc(),
            )
            .options(
                selectinload(Tweet.author),
                selectinload(Tweet.likes_users),
                selectinload(Tweet.attachments),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().unique().all()

    async def create(self, content: str, author_id: int) -> Tweet:
        """Добавляет твит и делает flush, чтобы получить его ID."""
        tweet = Tweet(content=content, author_id=author_id)
        self.session.add(tweet)
        await self.session.flush()
        return tweet

    async def get_with_likes(self, tweet_id: int) -> Tweet | None:
        """Возвращает твит по ID вместе со списком лайкнувших."""
        query = (
            select(Tweet)
            .where(Tweet.id == tweet_id)
            .options(selectinload(Tweet.likes_users))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_and_author(self, tweet_id: int, author_id: int) -> Tweet | None:
        """Возвращает твит, только если он принадлежит указанному автору."""
        query = select(Tweet).where(Tweet.id == tweet_id, Tweet.author_id == author_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def delete(self, tweet: Tweet) -> None:
        """Удаляет твит (вместе с его медиа каскадом)."""
        await self.session.delete(tweet)
