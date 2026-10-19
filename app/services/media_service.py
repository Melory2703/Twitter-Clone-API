"""
Сервис медиафайлов: сохранение загруженного файла на диск и запись о нём в БД.
Содержит бизнес-правила и управляет транзакцией (commit).
"""

import asyncio
import logging
import uuid
from collections.abc import Sequence
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import ALLOWED_MEDIA_TYPES, MAX_UPLOAD_SIZE, UPLOAD_DIR
from app.core.exceptions import BadRequestError
from app.models import Media
from app.repositories.media_repository import MediaRepository

logger = logging.getLogger(__name__)

# Расширение, если у загруженного файла его нет или оно выглядит подозрительно
DEFAULT_EXTENSION = ".bin"
MAX_EXTENSION_LENGTH = 10


def _get_extension(filename: str | None) -> str:
    """Возвращает расширение имени файла вместе с точкой или безопасное значение по умолчанию."""
    suffix = Path(filename or "").suffix.lower()
    if len(suffix) > MAX_EXTENSION_LENGTH or not suffix[1:].isalnum():
        return DEFAULT_EXTENSION
    return suffix


def _unlink_files(file_paths: Sequence[str]) -> None:
    """Удаляет файлы из UPLOAD_DIR по путям вида /static/media/<имя>; отсутствующие пропускает."""
    for file_path in file_paths:
        # Берём только имя файла, чтобы путь из БД не мог выйти за пределы UPLOAD_DIR
        target = UPLOAD_DIR / Path(file_path).name
        try:
            target.unlink(missing_ok=True)
        except OSError:
            logger.exception("Failed to delete media file %s", target)


async def delete_media_files(file_paths: Sequence[str]) -> None:
    """
    Удаляет файлы медиа с диска, не блокируя event loop.
    Отсутствующий файл не считается ошибкой; прочие ошибки ФС только логируются,
    так как к этому моменту изменения в БД уже зафиксированы.
    """
    await asyncio.to_thread(_unlink_files, file_paths)


class MediaService:
    """Бизнес-логика загрузки медиафайлов."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.medias = MediaRepository(session)

    async def upload(
        self, filename: str | None, content: bytes, content_type: str | None
    ) -> Media:
        """Проверяет тип и размер, сохраняет файл в static/media под именем UUID и создаёт запись Media."""
        mime_type = (content_type or "").split(";")[0].strip().lower()
        if mime_type not in ALLOWED_MEDIA_TYPES:
            allowed = ", ".join(sorted(ALLOWED_MEDIA_TYPES))
            raise BadRequestError(f"Unsupported file type. Allowed types: {allowed}")
        if len(content) > MAX_UPLOAD_SIZE:
            limit_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
            raise BadRequestError(f"File is too large. Maximum size is {limit_mb} MB")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        file_name = f"{uuid.uuid4()}{_get_extension(filename)}"
        await asyncio.to_thread((UPLOAD_DIR / file_name).write_bytes, content)

        media = await self.medias.create(f"/static/media/{file_name}")
        await self.session.commit()
        return media
