"""
Тесты загрузки медиафайлов: проверка типа и размера, формирование имени файла на диске.
"""

import pytest
from httpx import AsyncClient
from app.core.config import MAX_UPLOAD_SIZE
from app.models import User

HEADERS = {"api-key": "test"}


async def _upload(client: AsyncClient, name: str, content: bytes, content_type: str):
    """Отправляет файл на /api/medias от имени тестового пользователя."""
    return await client.post(
        "/api/medias",
        headers=HEADERS,
        files={"file": (name, content, content_type)},
    )


@pytest.mark.asyncio
async def test_upload_rejects_wrong_content_type(
    client: AsyncClient, test_user: User, media_dir
):
    """Файл неразрешённого типа отклоняется с 400 и не попадает на диск."""
    res = await _upload(client, "script.txt", b"hello", "text/plain")
    assert res.status_code == 400
    body = res.json()
    assert body["result"] is False
    assert "Unsupported file type" in body["error_message"]
    assert list(media_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_upload_rejects_too_large_file(
    client: AsyncClient, test_user: User, media_dir
):
    """Файл больше лимита отклоняется с 400 и не попадает на диск."""
    res = await _upload(client, "big.jpg", b"0" * (MAX_UPLOAD_SIZE + 1), "image/jpeg")
    assert res.status_code == 400
    assert "File is too large" in res.json()["error_message"]
    assert list(media_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_upload_accepts_file_of_max_size(
    client: AsyncClient, test_user: User, media_dir
):
    """Файл ровно максимального размера принимается."""
    res = await _upload(client, "edge.png", b"0" * MAX_UPLOAD_SIZE, "image/png")
    assert res.status_code == 200
    assert len(list(media_dir.iterdir())) == 1


@pytest.mark.asyncio
async def test_upload_filename_without_extension(
    client: AsyncClient, test_user: User, media_dir
):
    """Имя без расширения не попадает в имя файла целиком: используется безопасное расширение."""
    res = await _upload(client, "photo", b"data", "image/jpeg")
    assert res.status_code == 200
    saved = list(media_dir.iterdir())
    assert len(saved) == 1
    assert saved[0].suffix == ".bin"
    assert "photo" not in saved[0].name


@pytest.mark.asyncio
async def test_upload_keeps_extension(client: AsyncClient, test_user: User, media_dir):
    """Расширение из имени сохраняется (в нижнем регистре)."""
    res = await _upload(client, "My.Photo.PNG", b"data", "image/png")
    assert res.status_code == 200
    saved = list(media_dir.iterdir())
    assert len(saved) == 1
    assert saved[0].suffix == ".png"
