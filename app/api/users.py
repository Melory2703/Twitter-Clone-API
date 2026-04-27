"""
Модуль содержит обработчики API-запросов для управления пользователями.
Включает получение информации о профилях, а также функционал подписок и отписок.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models import User
from app.api.deps import get_current_user
from app.schemas import UserResponse, SuccessResponse

# Инициализация роутера для управления пользователями
router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Получение информации о текущем аутентифицированном пользователе.

    Args:
        current_user (User): Объект текущего пользователя, полученный из токена.

    Returns:
        dict: JSON-ответ с данными профиля текущего пользователя.
    """
    return {"result": True, "user": current_user}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(user_id: int, session: AsyncSession = Depends(get_session)):
    """
    Получение информации о профиле конкретного пользователя по его ID.

    Args:
        user_id (int): Уникальный идентификатор запрашиваемого пользователя.
        session (AsyncSession): Сессия базы данных для выполнения запроса.

    Returns:
        dict: JSON-ответ с полными данными профиля пользователя, включая подписки.
    """
    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.followers), selectinload(User.following))
    )
    res = await session.execute(query)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"result": True, "user": user}


@router.post("/{user_id}/follow", response_model=SuccessResponse)
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Оформление подписки на другого пользователя.

    Args:
        user_id (int): ID пользователя, на которого необходимо подписаться.
        current_user (User): Текущий аутентифицированный пользователь (кто подписывается).
        session (AsyncSession): Сессия базы данных.

    Returns:
        SuccessResponse: Ответ с результатом операции (True при успехе).
    """
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    query = select(User).where(User.id == user_id).options(selectinload(User.followers))
    res = await session.execute(query)
    target_user = res.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user not in current_user.following:
        current_user.following.append(target_user)
        await session.commit()

    return {"result": True}


@router.delete("/{user_id}/follow", response_model=SuccessResponse)
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Отмена подписки на пользователя.

    Args:
        user_id (int): ID пользователя, от которого необходимо отписаться.
        current_user (User): Текущий аутентифицированный пользователь (кто отписывается).
        session (AsyncSession): Сессия базы данных.

    Returns:
        SuccessResponse: Ответ с результатом операции.
    """
    # Поиск пользователя в списке подписок текущего пользователя
    target_user = next(
        (followed for followed in current_user.following if followed.id == user_id),
        None,
    )
    if target_user:
        current_user.following.remove(target_user)
        await session.commit()

    return {"result": True}
