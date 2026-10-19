"""
Модуль интеграционного тестирования API.
Содержит тесты для проверки механизмов авторизации, управления профилями пользователей,
логики подписок, работы с твитами (создание, удаление, лайки) и загрузки медиафайлов.
"""

import os
import pytest
from httpx import AsyncClient
from app.models import User

# --- 1. ТЕСТЫ АВТОРИЗАЦИИ И ДОСТУПА (deps.py) ---


@pytest.mark.asyncio
async def test_invalid_token(client: AsyncClient):
    """
    Проверка ошибки доступа при использовании неверного API-ключа.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
    """
    response = await client.get("/api/users/me", headers={"api-key": "wrong_key"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_token(client: AsyncClient):
    """
    Проверка ошибки доступа при отсутствии API-ключа в заголовках.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
    """
    response = await client.get("/api/users/me")
    assert response.status_code in [401, 422]


# --- 2. ТЕСТЫ ПОЛЬЗОВАТЕЛЕЙ И СВЯЗЕЙ (users.py) ---


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient, test_user: User):
    """
    Проверка получения данных профиля текущего авторизованного пользователя.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Фикстура созданного пользователя.
    """
    response = await client.get("/api/users/me", headers={"api-key": "test"})
    assert response.status_code == 200
    assert response.json()["result"] is True
    assert response.json()["user"]["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, test_user: User, second_user: User):
    """
    Проверка получения информации о другом пользователе по его ID.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Текущий пользователь (авторизация).
        second_user (User): Запрашиваемый пользователь.
    """
    response = await client.get(
        f"/api/users/{second_user.id}", headers={"api-key": "test"}
    )
    assert response.status_code == 200
    assert response.json()["user"]["id"] == second_user.id


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, test_user: User):
    """
    Проверка обработки ситуации, когда запрашиваемый пользователь не существует (404).

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Текущий пользователь.
    """
    response = await client.get("/api/users/99999", headers={"api-key": "test"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_follow_unfollow_logic(
    client: AsyncClient, test_user: User, second_user: User
):
    """
    Проверка логики подписки на пользователя и последующей отписки.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Пользователь, который подписывается.
        second_user (User): Пользователь, на которого подписываются.
    """
    # Подписка
    res_f = await client.post(
        f"/api/users/{second_user.id}/follow", headers={"api-key": "test"}
    )
    assert res_f.status_code in [200, 201]

    # Отписка
    res_un = await client.delete(
        f"/api/users/{second_user.id}/follow", headers={"api-key": "test"}
    )
    assert res_un.status_code == 200


@pytest.mark.asyncio
async def test_unfollow_not_following(
    client: AsyncClient, test_user: User, second_user: User
):
    """
    Проверка удаления подписки в случае, если пользователь не был подписан (краевой случай).

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Инициатор запроса.
        second_user (User): Пользователь, на которого нет подписки.
    """
    res = await client.delete(
        f"/api/users/{second_user.id}/follow", headers={"api-key": "test"}
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_follow_errors(client: AsyncClient, test_user: User):
    """
    Проверка ограничений подписки: на самого себя или на несуществующего пользователя.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Текущий пользователь.
    """
    # На самого себя
    res_self = await client.post(
        f"/api/users/{test_user.id}/follow", headers={"api-key": "test"}
    )
    assert res_self.status_code in [400, 404]

    # На несуществующего
    res_404 = await client.post("/api/users/99999/follow", headers={"api-key": "test"})
    assert res_404.status_code == 404


# --- 3. ТЕСТЫ ТВИТОВ И МЕДИАФАЙЛОВ (tweets.py) ---


@pytest.mark.asyncio
async def test_create_tweet_with_real_jpg(client: AsyncClient, test_user: User):
    """
    Проверка полной цепочки создания контента: загрузка файла и создание твита.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Автор твита.
    """
    path = "tests/resources/test.jpg"
    if not os.path.exists(path):
        os.makedirs("tests/resources", exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"fake_jpg_content_for_test")

    with open(path, "rb") as f:
        res_m = await client.post(
            "/api/medias",
            headers={"api-key": "test"},
            files={"file": ("test.jpg", f, "image/jpeg")},
        )
    assert res_m.status_code in [200, 201]
    media_id = res_m.json()["media_id"]

    payload = {"tweet_data": "Tweet with real jpg", "tweet_media_ids": [media_id]}
    res_t = await client.post("/api/tweets", json=payload, headers={"api-key": "test"})
    assert res_t.status_code in [200, 201]
    assert res_t.json()["result"] is True


@pytest.mark.asyncio
async def test_get_tweets_list_full_coverage(
    client: AsyncClient, test_user: User, tweet_id: int
):
    """
    Проверка получения ленты твитов и корректности структуры ответа.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Авторизованный пользователь.
        tweet_id (int): ID существующего твита в базе.
    """
    response = await client.get("/api/tweets", headers={"api-key": "test"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["tweets"]) > 0
    assert "attachments" in data["tweets"][0]
    assert "author" in data["tweets"][0]


@pytest.mark.asyncio
async def test_delete_tweet_success(
    client: AsyncClient, test_user: User, tweet_id: int
):
    """
    Проверка успешного удаления собственного твита.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Автор твита.
        tweet_id (int): Идентификатор твита для удаления.
    """
    response = await client.delete(
        f"/api/tweets/{tweet_id}", headers={"api-key": "test"}
    )
    assert response.status_code == 200
    assert response.json()["result"] is True


@pytest.mark.asyncio
async def test_delete_tweet_permissions(
    client: AsyncClient, test_user: User, second_user: User
):
    """
    Проверка защиты: пользователь не может удалить чужой твит.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Пользователь, пытающийся удалить чужой контент.
        second_user (User): Автор твита.
    """
    res_t = await client.post(
        "/api/tweets",
        json={"tweet_data": "Stranger's tweet", "tweet_media_ids": []},
        headers={"api-key": "test2"},
    )
    t_id = res_t.json()["tweet_id"]

    res_del = await client.delete(f"/api/tweets/{t_id}", headers={"api-key": "test"})
    assert res_del.status_code in [403, 404, 400]


@pytest.mark.asyncio
async def test_delete_tweet_not_found_edge_case(client: AsyncClient, test_user: User):
    """
    Проверка удаления несуществующего твита (404).

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Текущий пользователь.
    """
    res = await client.delete("/api/tweets/999999", headers={"api-key": "test"})
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_like_logic_full(
    client: AsyncClient, test_user: User, second_user: User, tweet_id: int
):
    """
    Проверка установки лайка на твит и его последующего удаления.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Автор твита.
        second_user (User): Пользователь, ставящий лайк.
        tweet_id (int): Идентификатор твита.
    """
    await client.post(f"/api/tweets/{tweet_id}/likes", headers={"api-key": "test2"})

    res_un = await client.delete(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": "test2"}
    )
    assert res_un.status_code == 200

    res_404 = await client.post("/api/tweets/99999/likes", headers={"api-key": "test"})
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_unlike_tweet_not_liked(
    client: AsyncClient, test_user: User, tweet_id: int
):
    """
    Проверка удаления лайка, который не был поставлен.

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
        test_user (User): Пользователь, инициирующий запрос.
        tweet_id (int): Идентификатор твита.
    """
    res = await client.delete(
        f"/api/tweets/{tweet_id}/likes", headers={"api-key": "test"}
    )
    assert res.status_code == 200


# --- 4. СТАТИЧЕСКИЕ ФАЙЛЫ ---


@pytest.mark.asyncio
async def test_index_page(client: AsyncClient):
    """
    Проверка доступности главной страницы (index.html).

    Args:
        client (AsyncClient): Тестовый клиент для отправки HTTP-запросов.
    """
    res = await client.get("/")
    assert res.status_code == 200
