"""
Репозиторий медиафайлов: все запросы SQLAlchemy к таблице medias.
Транзакцией (commit) управляет сервис.
"""

from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Media


class MediaRepository:
    """Доступ к данным медиафайлов."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, file_path: str) -> Media:
        """Добавляет запись о файле и делает flush, чтобы получить её ID."""
        media = Media(file_path=file_path)
        self.session.add(media)
        await self.session.flush()
        return media

    async def get_by_ids(self, media_ids: Sequence[int]) -> Sequence[Media]:
        """Возвращает существующие медиа с указанными ID (несуществующие в результат не попадают)."""
        query = select(Media).where(Media.id.in_(media_ids))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def attach_to_tweet(self, medias: Sequence[Media], tweet_id: int) -> None:
        """Привязывает переданные медиа к твиту."""
        for media in medias:
            media.tweet_id = tweet_id
