"""
Тесты связки твитов и медиафайлов: проверка media id при создании, удаление файлов
вместе с твитом, логирование ошибки БД в ленте.
"""

import logging
import pytest
from httpx import AsyncClient
from sqlalchemy.exc import SQLAlchemyError
from app.models import User
from app.repositories.tweet_repository import TweetRepository

HEADERS = {"api-key": "test"}


async def _upload(client: AsyncClient) -> int:
    """Загружает валидное изображение и возвращает ID медиа."""
    res = await client.post(
        "/api/medias",
        headers=HEADERS,
        files={"file": ("pic.jpg", b"jpg-bytes", "image/jpeg")},
    )
    assert res.status_code == 200
    return res.json()["media_id"]


async def _create_tweet(client: AsyncClient, media_ids: list[int]):
    """Создаёт твит с указанными media id."""
    return await client.post(
        "/api/tweets",
        json={"tweet_data": "with media", "tweet_media_ids": media_ids},
        headers=HEADERS,
    )


async def _feed(client: AsyncClient) -> list[dict]:
    """Возвращает ленту текущего пользователя."""
    res = await client.get("/api/tweets", headers=HEADERS)
    assert res.status_code == 200
    return res.json()["tweets"]


@pytest.mark.asyncio
async def test_create_tweet_unknown_media_id(
    client: AsyncClient, test_user: User, media_dir
):
    """Несуществующий media id даёт 400 с перечнем ID, твит не создаётся."""
    res = await _create_tweet(client, [9999])
    assert res.status_code == 400
    body = res.json()
    assert body["result"] is False
    assert body["error_message"] == "Media not found: 9999"
    assert await _feed(client) == []


@pytest.mark.asyncio
async def test_create_tweet_partially_unknown_media_ids(
    client: AsyncClient, test_user: User, media_dir
):
    """Если не найден хотя бы один id, твит не создаётся и существующее медиа не привязывается."""
    media_id = await _upload(client)
    res = await _create_tweet(client, [media_id, 9999, 8888])
    assert res.status_code == 400
    assert res.json()["error_message"] == "Media not found: 8888, 9999"
    assert await _feed(client) == []


@pytest.mark.asyncio
async def test_create_tweet_with_valid_and_duplicate_media_ids(
    client: AsyncClient, test_user: User, media_dir
):
    """Корректные id (в том числе повторяющиеся) работают как раньше."""
    media_id = await _upload(client)
    res = await _create_tweet(client, [media_id, media_id])
    assert res.status_code == 200
    tweets = await _feed(client)
    assert len(tweets) == 1
    assert len(tweets[0]["attachments"]) == 1


@pytest.mark.asyncio
async def test_delete_tweet_removes_media_files(
    client: AsyncClient, test_user: User, media_dir
):
    """При удалении твита файлы его вложений удаляются с диска."""
    first, second = await _upload(client), await _upload(client)
    assert len(list(media_dir.iterdir())) == 2
    tweet_id = (await _create_tweet(client, [first, second])).json()["tweet_id"]

    res = await client.delete(f"/api/tweets/{tweet_id}", headers=HEADERS)
    assert res.status_code == 200
    assert list(media_dir.iterdir()) == []


@pytest.mark.asyncio
async def test_delete_tweet_with_missing_media_file(
    client: AsyncClient, test_user: User, media_dir
):
    """Если файла вложения уже нет на диске, удаление твита проходит без ошибки."""
    media_id = await _upload(client)
    tweet_id = (await _create_tweet(client, [media_id])).json()["tweet_id"]
    for saved in media_dir.iterdir():
        saved.unlink()

    res = await client.delete(f"/api/tweets/{tweet_id}", headers=HEADERS)
    assert res.status_code == 200
    assert res.json() == {"result": True}
    assert await _feed(client) == []


@pytest.mark.asyncio
async def test_delete_foreign_tweet_keeps_media_files(
    client: AsyncClient, test_user: User, second_user: User, media_dir
):
    """Попытка удалить чужой твит не трогает файлы его вложений."""
    media_id = await _upload(client)
    tweet_id = (await _create_tweet(client, [media_id])).json()["tweet_id"]

    res = await client.delete(f"/api/tweets/{tweet_id}", headers={"api-key": "test2"})
    assert res.status_code == 404
    assert len(list(media_dir.iterdir())) == 1


@pytest.mark.asyncio
async def test_get_feed_logs_database_error(
    client: AsyncClient, test_user: User, monkeypatch, caplog
):
    """Ошибка БД в ленте логируется со стеком, клиент получает прежний 500 Database error."""

    async def _broken_feed(self, author_ids):
        raise SQLAlchemyError("boom")

    monkeypatch.setattr(TweetRepository, "get_feed", _broken_feed)
    with caplog.at_level(logging.ERROR):
        res = await client.get("/api/tweets", headers=HEADERS)

    assert res.status_code == 500
    assert res.json() == {
        "result": False,
        "error_type": "500",
        "error_message": "Database error",
    }
    assert any(
        record.exc_info and "GET /tweets" in record.getMessage()
        for record in caplog.records
    )
