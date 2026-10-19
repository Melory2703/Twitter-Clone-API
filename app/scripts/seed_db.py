"""
Модуль для первоначального наполнения базы данных.
Используется для создания тестовых пользователей, твитов, связей подписок и лайков.
"""

import asyncio
from sqlalchemy import text, insert
from app.core.database import async_session
from app.models import User, Tweet, followers, likes


async def seed_data():
    """
    Выполняет процесс наполнения базы данных начальными данными.
    Очищает существующие таблицы и создает демонстрационный набор записей.

    Args:
        None

    Returns:
        None: Функция выполняет операции записи в БД и не возвращает значение.
    """
    print("Начинаем процесс наполнения базы...")
    async with async_session() as session:
        try:
            await session.execute(
                text(
                    "TRUNCATE users, tweets, followers, likes, medias RESTART IDENTITY CASCADE;"
                )
            )

            user_ivan = User(name="Ivan", api_key="test")
            user_maria = User(name="Maria", api_key="dev")
            user_petr = User(name="Petr", api_key="petr_key")
            user_elena = User(name="Elena", api_key="elena_key")

            session.add_all([user_ivan, user_maria, user_petr, user_elena])

            await session.flush()

            tweet_ivan = Tweet(
                content="Привет, это первый твит Ивана!", author_id=user_ivan.id
            )
            tweet_maria = Tweet(content="Мария пишет о погоде", author_id=user_maria.id)
            tweet_petr = Tweet(content="Петр постит мем", author_id=user_petr.id)
            tweet_elena = Tweet(content="Секретный твит Елены", author_id=user_elena.id)

            session.add_all([tweet_ivan, tweet_maria, tweet_petr, tweet_elena])

            await session.flush()

            await session.execute(
                insert(followers).values(
                    [
                        {"follower_id": user_ivan.id, "followed_id": user_maria.id},
                        {"follower_id": user_ivan.id, "followed_id": user_petr.id},
                        {"follower_id": user_maria.id, "followed_id": user_ivan.id},
                    ]
                )
            )

            await session.execute(
                insert(likes).values(
                    [
                        {"user_id": user_ivan.id, "tweet_id": tweet_maria.id},
                        {"user_id": user_petr.id, "tweet_id": tweet_maria.id},
                        {"user_id": user_ivan.id, "tweet_id": tweet_petr.id},
                    ]
                )
            )

            await session.commit()
            print("Данные успешно записаны! 4 юзера, твиты, подписки и лайки на месте.")

        except Exception as e:
            print(f"Ошибка при заполнении: {e}")
            await session.rollback()


if __name__ == "__main__":
    asyncio.run(seed_data())
