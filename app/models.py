"""
Модуль содержит описание моделей SQLAlchemy для базы данных проекта Twitter-клон.
Описаны таблицы пользователей, твитов, медиафайлов и таблицы связей для подписок и лайков.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

followers = Table(
    "followers",
    Base.metadata,
    Column(
        "follower_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "followed_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
"""
Таблица ассоциации для реализации связи многие-ко-многим между пользователями (подписки).
"""

likes = Table(
    "likes",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "tweet_id",
        Integer,
        ForeignKey("tweets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
"""
Таблица ассоциации для реализации связи многие-ко-многим между пользователями и твитами (лайки).
"""


class User(Base):
    """
    Модель пользователя системы.

    Attributes:
        id (int): Уникальный идентификатор пользователя.
        name (str): Имя или никнейм пользователя.
        api_key (str): Уникальный ключ API для аутентификации запросов.
        tweets (list[Tweet]): Список твитов, созданных этим пользователем.
        following (list[User]): Список пользователей, на которых подписан данный пользователь.
        followers (list[User]): Список пользователей, которые подписаны на данного пользователя.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    tweets: Mapped[list["Tweet"]] = relationship(
        back_populates="author", cascade="all, delete-orphan"
    )

    following: Mapped[list["User"]] = relationship(
        "User",
        secondary=followers,
        primaryjoin=(id == followers.c.follower_id),
        secondaryjoin=(id == followers.c.followed_id),
        back_populates="followers",
        lazy="selectin",
    )
    followers: Mapped[list["User"]] = relationship(
        "User",
        secondary=followers,
        primaryjoin=(id == followers.c.followed_id),
        secondaryjoin=(id == followers.c.follower_id),
        back_populates="following",
        lazy="selectin",
    )


class Tweet(Base):
    """
    Модель твита (сообщения).

    Attributes:
        id (int): Уникальный идентификатор твита.
        content (str): Текстовое содержимое твита.
        author_id (int): Идентификатор автора твита (внешний ключ).
        author (User): Объект автора твита.
        likes_users (list[User]): Список пользователей, поставивших лайк этому твиту.
        attachments (list[Media]): Список медиафайлов, прикрепленных к твиту.
    """

    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    author: Mapped["User"] = relationship(back_populates="tweets", lazy="selectin")
    likes_users: Mapped[list["User"]] = relationship(secondary=likes, lazy="selectin")
    attachments: Mapped[list["Media"]] = relationship(
        back_populates="tweet", cascade="all, delete-orphan", lazy="selectin"
    )


class Media(Base):
    """
    Модель для хранения информации о медиафайлах (изображениях), прикрепленных к твитам.

    Attributes:
        id (int): Уникальный идентификатор файла.
        file_path (str): Путь к файлу в файловой системе.
        tweet_id (int | None): Идентификатор твита, к которому прикреплен файл.
        tweet (Tweet): Объект твита, к которому относится медиафайл.
    """

    __tablename__ = "medias"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    tweet_id: Mapped[int | None] = mapped_column(
        ForeignKey("tweets.id", ondelete="CASCADE")
    )

    tweet: Mapped["Tweet"] = relationship(back_populates="attachments")
