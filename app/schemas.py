"""
Модуль содержит схемы Pydantic для валидации данных и сериализации ответов API.
Обеспечивает корректное преобразование SQLAlchemy моделей в JSON-ответы.
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UserShortSchema(BaseModel):
    """
    Упрощенная схема пользователя для кратких списков и упоминаний.

    Attributes:
        id (int): Идентификатор пользователя.
        name (str): Имя пользователя.
    """

    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class LikeSchema(BaseModel):
    """
    Специальная схема для отображения информации о лайке.

    Attributes:
        user_id (int): Идентификатор пользователя, поставившего лайк.
        name (str): Имя пользователя.
    """

    user_id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserProfileSchema(UserShortSchema):
    """
    Расширенная схема профиля пользователя, включая списки подписок.

    Attributes:
        followers (List[UserShortSchema]): Список подписчиков пользователя.
        following (List[UserShortSchema]): Список пользователей, на которых он подписан.
    """

    followers: List[UserShortSchema] = []
    following: List[UserShortSchema] = []
    model_config = ConfigDict(from_attributes=True)


class TweetSchema(BaseModel):
    """
    Схема для полного представления твита в ленте.

    Attributes:
        id (int): Идентификатор твита.
        content (str): Текст твита.
        attachments (List[str]): Список ссылок на прикрепленные медиафайлы.
        author (UserShortSchema): Информация об авторе.
        likes (List[LikeSchema]): Список пользователей, лайкнувших твит.
    """

    id: int
    content: str
    attachments: List[str] = []
    author: UserShortSchema
    likes: List[LikeSchema] = []
    model_config = ConfigDict(from_attributes=True)


class TweetCreateSchema(BaseModel):
    """
    Схема для валидации данных при создании нового твита.

    Attributes:
        tweet_data (str): Текстовое содержание твита.
        tweet_media_ids (Optional[List[int]]): Список ID предварительно загруженных медиафайлов.
    """

    tweet_data: str
    tweet_media_ids: Optional[List[int]] = Field(default_factory=list)


class SuccessResponse(BaseModel):
    """
    Базовая схема успешного ответа API.

    Attributes:
        result (bool): Статус выполнения операции (по умолчанию True).
    """

    result: bool = True


class UserResponse(SuccessResponse):
    """
    Схема ответа, содержащая информацию о профиле пользователя.
    """

    user: UserProfileSchema


class TweetListResponse(SuccessResponse):
    """
    Схема ответа, содержащая список твитов.
    """

    tweets: List[TweetSchema]


class TweetCreateResponse(SuccessResponse):
    """
    Схема ответа после успешного создания твита.

    Attributes:
        tweet_id (int): Идентификатор созданного твита.
    """

    tweet_id: int
