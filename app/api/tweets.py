"""
Модуль содержит обработчики API-запросов для работы с твитами и медиафайлами.
Включает функционал создания, удаления, лайков и получения ленты твитов.
"""

import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models import Tweet, Media, User, likes
from app.api.deps import get_current_user
from app.schemas import (
    TweetCreateSchema,
    TweetCreateResponse,
    TweetListResponse,
    SuccessResponse,
)

router = APIRouter(prefix="/api", tags=["tweets"])

# Настройка путей для сохранения медиафайлов
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "media")


@router.post("/medias")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Загрузка медиафайла (изображения) на сервер.

    Args:
        file (UploadFile): Загружаемый файл.
        current_user (User): Текущий аутентифицированный пользователь.
        session (AsyncSession): Сессия базы данных.

    Returns:
        dict: JSON-ответ, содержащий статус операции и ID созданного медиа-ресурса.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filename = file.filename or "unknow.file"
    file_ext = filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    db_path = f"/static/media/{file_name}"
    new_media = Media(file_path=db_path)
    session.add(new_media)
    await session.commit()
    await session.refresh(new_media)
    return {"result": True, "media_id": new_media.id}


@router.get("/tweets", response_model=TweetListResponse)
async def get_tweets(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Получение ленты твитов для текущего пользователя.
    В ленту попадают собственные твиты и твиты пользователей, на которых оформлена подписка.

    Args:
        session (AsyncSession): Сессия базы данных.
        current_user (User): Текущий аутентифицированный пользователь.

    Returns:
        TweetListResponse: Список объектов твитов с данными об авторе, медиа и лайках.
    """
    following_ids = [user.id for user in current_user.following]
    following_ids.append(current_user.id)

    query = (
        select(Tweet)
        .outerjoin(likes, Tweet.id == likes.c.tweet_id)
        .where(Tweet.author_id.in_(following_ids))
        .group_by(Tweet.id)
        .order_by(
            func.count(likes.c.user_id).desc(),
            Tweet.id.desc(),
        )
        .options(
            selectinload(Tweet.author),
            selectinload(Tweet.likes_users),
            selectinload(Tweet.attachments),
        )
    )

    try:
        query_result = await session.execute(query)
    except Exception as error:
        print(f"Error in GET /tweets database execution: {error}")
        raise HTTPException(status_code=500, detail="Database error")

    tweets_from_db = query_result.scalars().unique().all()

    formatted_tweets_list = []
    for tweet_item in tweets_from_db:
        formatted_tweets_list.append(
            {
                "id": tweet_item.id,
                "content": tweet_item.content,
                "attachments": [media.file_path for media in tweet_item.attachments],
                "author": {
                    "id": tweet_item.author.id,
                    "name": tweet_item.author.name,
                },
                "likes": [
                    {"user_id": user.id, "name": user.name}
                    for user in tweet_item.likes_users
                ],
            }
        )

    return {"result": True, "tweets": formatted_tweets_list}


@router.post("/tweets", response_model=TweetCreateResponse)
async def create_tweet(
    data: TweetCreateSchema,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Создание нового твита.

    Args:
        data (TweetCreateSchema): Схема с текстом твита и списком ID медиафайлов.
        current_user (User): Автор твита (текущий пользователь).
        session (AsyncSession): Сессия базы данных.

    Returns:
        TweetCreateResponse: Статус операции и ID созданного твита.
    """
    new_tweet = Tweet(content=data.tweet_data, author_id=current_user.id)
    session.add(new_tweet)
    await session.flush()

    if data.tweet_media_ids:
        query = select(Media).where(Media.id.in_(data.tweet_media_ids))
        res = await session.execute(query)
        medias = res.scalars().all()
        for media_item in medias:
            media_item.tweet_id = new_tweet.id

    await session.commit()
    return {"result": True, "tweet_id": new_tweet.id}


@router.post("/tweets/{tweet_id}/likes", response_model=SuccessResponse)
async def like_tweet(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Добавление лайка к твиту.

    Args:
        tweet_id (int): Уникальный идентификатор твита.
        current_user (User): Пользователь, ставящий лайк.
        session (AsyncSession): Сессия базы данных.

    Returns:
        SuccessResponse: Успешный статус операции.
    """
    query = (
        select(Tweet)
        .where(Tweet.id == tweet_id)
        .options(selectinload(Tweet.likes_users))
    )
    res = await session.execute(query)
    tweet = res.scalar_one_or_none()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if current_user not in tweet.likes_users:
        tweet.likes_users.append(current_user)
        await session.commit()
    return {"result": True}


@router.delete("/tweets/{tweet_id}/likes", response_model=SuccessResponse)
async def unlike_tweet(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Удаление лайка с твита.

    Args:
        tweet_id (int): Уникальный идентификатор твита.
        current_user (User): Пользователь, убирающий лайк.
        session (AsyncSession): Сессия базы данных.

    Returns:
        SuccessResponse: Успешный статус операции.
    """
    query = (
        select(Tweet)
        .where(Tweet.id == tweet_id)
        .options(selectinload(Tweet.likes_users))
    )
    res = await session.execute(query)
    tweet = res.scalar_one_or_none()

    if tweet:
        user_to_remove = next(
            (user for user in tweet.likes_users if user.id == current_user.id), None
        )
        if user_to_remove:
            tweet.likes_users.remove(user_to_remove)
            await session.commit()

    return {"result": True}


@router.delete("/tweets/{id}", response_model=SuccessResponse)
async def delete_tweet(
    id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Удаление твита. Операция разрешена только автору твита.

    Args:
        id (int): Уникальный идентификатор твита.
        current_user (User): Пользователь, пытающийся удалить твит.
        session (AsyncSession): Сессия базы данных.

    Returns:
        SuccessResponse: Успешный статус операции.
    """
    query = select(Tweet).where(Tweet.id == id, Tweet.author_id == current_user.id)
    res = await session.execute(query)
    tweet = res.scalar_one_or_none()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found or access denied")
    await session.delete(tweet)
    await session.commit()
    return {"result": True}
