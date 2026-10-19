"""
Сервис медиафайлов: сохранение загруженного файла на диск и запись о нём в БД.
Содержит бизнес-правила и управляет транзакцией (commit).
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import UPLOAD_DIR
from app.models import Media
from app.repositories.media_repository import MediaRepository


class MediaService:
    """Бизнес-логика загрузки медиафайлов."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.medias = MediaRepository(session)

    async def upload(self, filename: str | None, content: bytes) -> Media:
        """Сохраняет файл в static/media под именем UUID и создаёт запись Media."""
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        filename = filename or "unknow.file"
        file_ext = filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        (UPLOAD_DIR / file_name).write_bytes(content)

        media = await self.medias.create(f"/static/media/{file_name}")
        await self.session.commit()
        return media
