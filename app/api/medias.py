"""
Модуль содержит обработчик API-запроса для загрузки медиафайлов.
"""

from fastapi import APIRouter, Depends, UploadFile, File
from app.models import User
from app.api.deps import get_current_user, get_media_service
from app.services.media_service import MediaService

# Теги те же, что у твитов, чтобы описание в /docs не изменилось
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
    media = await media_service.upload(file.filename, await file.read())
    return {"result": True, "media_id": media.id}
