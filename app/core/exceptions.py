"""
Бизнес-исключения приложения.
Сервисы поднимают их, не зная про HTTP-фреймворк; в ответ API они превращаются
обработчиком в app/main.py.
"""


class AppError(Exception):
    """Базовое бизнес-исключение: статус-код ответа и текст ошибки."""

    status_code = 500

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class BadRequestError(AppError):
    """Нарушено бизнес-правило (400)."""

    status_code = 400


class UnauthorizedError(AppError):
    """Пользователь не аутентифицирован (401)."""

    status_code = 401


class NotFoundError(AppError):
    """Запрошенный объект не найден (404)."""

    status_code = 404


class DatabaseError(AppError):
    """Ошибка при работе с базой данных (500)."""

    status_code = 500
