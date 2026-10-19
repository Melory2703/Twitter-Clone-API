from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api import users, tweets, medias
from app.core.config import UPLOAD_DIR
from app.core.exceptions import AppError

app = FastAPI(title="Twitter Clone API")


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Глобальный обработчик исключений Starlette/FastAPI.

    Перехватывает стандартные ошибки HTTP и преобразует их в унифицированный
    формат ответа, ожидаемый клиентом и автоматическими тестами.

    Args:
        request (Request): Объект текущего HTTP-запроса.
        exc (StarletteHTTPException): Объект пойманного исключения.

    Returns:
        JSONResponse: JSON-ответ с полями result, error_type и error_message.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "result": False,
            "error_type": str(exc.status_code),
            "error_message": exc.detail,
        },
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Преобразует бизнес-исключения сервисов в тот же формат ответа,
    что и обычные HTTP-ошибки: формат задаёт только custom_http_exception_handler.

    Args:
        request (Request): Объект текущего HTTP-запроса.
        exc (AppError): Бизнес-исключение с кодом статуса и текстом ошибки.

    Returns:
        JSONResponse: JSON-ответ с полями result, error_type и error_message.
    """
    http_exc = StarletteHTTPException(status_code=exc.status_code, detail=exc.detail)
    return await custom_http_exception_handler(request, http_exc)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.include_router(users.router)
app.include_router(tweets.router)
app.include_router(medias.router)

app.mount("/css", StaticFiles(directory="dist/css"), name="css")
app.mount("/js", StaticFiles(directory="dist/js"), name="js")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_index():
    """
    Эндпоинт для отдачи главной страницы приложения.

    Returns:
        FileResponse: Возвращает HTML-файл точки входа фронтенда.
    """
    return FileResponse("dist/index.html")


@app.get("/{fallback:path}")
async def statics_fallback(fallback: str):
    """
    Обработчик для корректной работы Single Page Application (SPA) маршрутизации.

    Если запрос не соответствует API-маршрутам или существующим статическим файлам,
    сервер возвращает index.html, позволяя фронтенд-роутеру обработать путь.
    Исключение: прямые запросы к /api или /static, которых нет на сервере,
    вернут ошибку 404.

    Args:
        fallback (str): Путь, запрошенный пользователем.

    Returns:
        Union[FileResponse, JSONResponse]: index.html для фронтенд-маршрутов
        или 404 ошибка для API/статических ресурсов.
    """
    if fallback.startswith("api") or fallback.startswith("static"):
        return JSONResponse(
            status_code=404, content={"result": False, "error_message": "Not Found"}
        )
    return FileResponse("dist/index.html")
