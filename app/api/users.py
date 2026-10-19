"""
Модуль содержит обработчики API-запросов для управления пользователями.
Включает получение информации о профилях, а также функционал подписок и отписок.
"""

from fastapi import APIRouter, Depends
from app.models import User
from app.api.deps import get_current_user, get_user_service
from app.schemas import UserResponse, SuccessResponse
from app.services.user_service import UserService

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
async def get_user_profile(
    user_id: int, user_service: UserService = Depends(get_user_service)
):
    """
    Получение информации о профиле конкретного пользователя по его ID.

    Args:
        user_id (int): Уникальный идентификатор запрашиваемого пользователя.
        user_service (UserService): Сервис пользователей.

    Returns:
        dict: JSON-ответ с полными данными профиля пользователя, включая подписки.
    """
    user = await user_service.get_profile(user_id)
    return {"result": True, "user": user}


@router.post("/{user_id}/follow", response_model=SuccessResponse)
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Оформление подписки на другого пользователя.

    Args:
        user_id (int): ID пользователя, на которого необходимо подписаться.
        current_user (User): Текущий аутентифицированный пользователь (кто подписывается).
        user_service (UserService): Сервис пользователей.

    Returns:
        SuccessResponse: Ответ с результатом операции (True при успехе).
    """
    await user_service.follow(current_user, user_id)
    return {"result": True}


@router.delete("/{user_id}/follow", response_model=SuccessResponse)
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Отмена подписки на пользователя.

    Args:
        user_id (int): ID пользователя, от которого необходимо отписаться.
        current_user (User): Текущий аутентифицированный пользователь (кто отписывается).
        user_service (UserService): Сервис пользователей.

    Returns:
        SuccessResponse: Ответ с результатом операции.
    """
    await user_service.unfollow(current_user, user_id)
    return {"result": True}
