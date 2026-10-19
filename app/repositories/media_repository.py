"""
Репозиторий медиафайлов: все запросы SQLAlchemy к таблице medias.
Транзакцией (commit) управляет сервис.
"""

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

    async def attach_to_tweet(self, media_ids: list[int], tweet_id: int) -> None:
        """Привязывает существующие медиа с указанными ID к твиту (несуществующие ID пропускаются)."""
        query = select(Media).where(Media.id.in_(media_ids))
        result = await self.session.execute(query)
        for media in result.scalars().all():
            media.tweet_id = tweet_id
