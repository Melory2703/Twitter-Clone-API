"""
Модуль содержит обработчик API-запроса для загрузки медиафайлов.
"""

from fastapi import APIRouter, Depends, UploadFile, File
from app.core.config import MAX_UPLOAD_SIZE
from app.models import User
from app.api.deps import get_current_user, get_media_service
from app.services.media_service import MediaService

router = APIRouter(prefix="/api", tags=["tweets"])


@router.post("/medias")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    media_service: MediaService = Depends(get_media_service),
):
    """
    Загрузка медиафайла (изображения) на сервер.

    Args:
        file (UploadFile): Загружаемый файл.
        current_user (User): Текущий аутентифицированный пользователь.
        media_service (MediaService): Сервис медиафайлов.

    Returns:
        dict: JSON-ответ, содержащий статус операции и ID созданного медиа-ресурса.
    """
    # Читаем на один байт больше лимита: этого достаточно, чтобы сервис отклонил большой файл
    content = await file.read(MAX_UPLOAD_SIZE + 1)
    media = await media_service.upload(file.filename, content, file.content_type)
    return {"result": True, "media_id": media.id}
