"""
Модуль содержит обработчики API-запросов для работы с твитами.
Включает функционал создания, удаления, лайков и получения ленты твитов.
"""

from fastapi import APIRouter, Depends
from app.models import User
from app.api.deps import get_current_user, get_tweet_service
from app.schemas import (
    TweetCreateSchema,
    TweetCreateResponse,
    TweetListResponse,
    SuccessResponse,
)
from app.services.tweet_service import TweetService

router = APIRouter(prefix="/api", tags=["tweets"])


@router.get("/tweets", response_model=TweetListResponse)
async def get_tweets(
    current_user: User = Depends(get_current_user),
    tweet_service: TweetService = Depends(get_tweet_service),
):
    """
    Получение ленты твитов для текущего пользователя.
    В ленту попадают собственные твиты и твиты пользователей, на которых оформлена подписка.

    Args:
        current_user (User): Текущий аутентифицированный пользователь.
        tweet_service (TweetService): Сервис твитов.

    Returns:
        TweetListResponse: Список объектов твитов с данными об авторе, медиа и лайках.
    """
    tweets = await tweet_service.get_feed(current_user)
    return {"result": True, "tweets": tweets}


@router.post("/tweets", response_model=TweetCreateResponse)
async def create_tweet(
    data: TweetCreateSchema,
    current_user: User = Depends(get_current_user),
    tweet_service: TweetService = Depends(get_tweet_service),
):
    """
    Создание нового твита.

    Args:
        data (TweetCreateSchema): Схема с текстом твита и списком ID медиафайлов.
        current_user (User): Автор твита (текущий пользователь).
        tweet_service (TweetService): Сервис твитов.

    Returns:
        TweetCreateResponse: Статус операции и ID созданного твита.
    """
    tweet = await tweet_service.create(
        current_user, data.tweet_data, data.tweet_media_ids or []
    )
    return {"result": True, "tweet_id": tweet.id}


@router.post("/tweets/{tweet_id}/likes", response_model=SuccessResponse)
async def like_tweet(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    tweet_service: TweetService = Depends(get_tweet_service),
):
    """
    Добавление лайка к твиту.

    Args:
        tweet_id (int): Уникальный идентификатор твита.
        current_user (User): Пользователь, ставящий лайк.
        tweet_service (TweetService): Сервис твитов.

    Returns:
        SuccessResponse: Успешный статус операции.
    """
    await tweet_service.like(current_user, tweet_id)
    return {"result": True}


@router.delete("/tweets/{tweet_id}/likes", response_model=SuccessResponse)
async def unlike_tweet(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    tweet_service: TweetService = Depends(get_tweet_service),
):
    """
    Удаление лайка с твита.

    Args:
        tweet_id (int): Уникальный идентификатор твита.
        current_user (User): Пользователь, убирающий лайк.
        tweet_service (TweetService): Сервис твитов.

    Returns:
        SuccessResponse: Успешный статус операции.
    """
    await tweet_service.unlike(current_user, tweet_id)
    return {"result": True}


@router.delete("/tweets/{id}", response_model=SuccessResponse)
async def delete_tweet(
    id: int,
    current_user: User = Depends(get_current_user),
    tweet_service: TweetService = Depends(get_tweet_service),
):
    """
    Удаление твита. Операция разрешена только автору твита.

    Args:
        id (int): Уникальный идентификатор твита.
        current_user (User): Пользователь, пытающийся удалить твит.
        tweet_service (TweetService): Сервис твитов.

    Returns:
        SuccessResponse: Успешный статус операции.
    """
    await tweet_service.delete(current_user, id)
    return {"result": True}
