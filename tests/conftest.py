"""
Модуль конфигурации pytest.
Содержит фикстуры для настройки тестовой базы данных, переопределения зависимостей FastAPI
и предоставления тестовых данных (пользователи, твиты).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_session
from app.models import User, Tweet

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"

engine_test = create_async_engine(TEST_DATABASE_URL)
async_session_test = async_sessionmaker(engine_test, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def init_db():
    """
    Инициализирует структуру базы данных перед каждым тестом и очищает её после завершения.

    Args:
        None

    Returns:
        None: Фикстура выполняет подготовку окружения.
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """
    Создает единую асинхронную сессию для конкретного теста.

    Args:
        None

    Returns:
        AsyncSession: Сессия SQLAlchemy для работы с БД.
    """
    async with async_session_test() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def override_deps(db_session: AsyncSession):
    """
    Подменяет зависимость получения сессии базы данных в приложении на тестовую сессию.

    Args:
        db_session (AsyncSession): Тестовая сессия базы данных.

    Returns:
        None: Фикстура модифицирует поведение приложения (app.dependency_overrides).
    """

    async def _override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    """
    Создает асинхронного клиента для отправки HTTP-запросов к приложению.

    Args:
        None

    Returns:
        AsyncClient: Клиент для тестирования API эндпоинтов.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """
    Создает и возвращает тестового пользователя в базе данных.

    Args:
        db_session (AsyncSession): Сессия базы данных.

    Returns:
        User: Объект созданного пользователя.
    """
    user = User(name="Test User", api_key="test")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user(db_session: AsyncSession):
    """
    Создает и возвращает второго тестового пользователя (для тестов подписок/фолловеров).

    Args:
        db_session (AsyncSession): Сессия базы данных.

    Returns:
        User: Объект второго созданного пользователя.
    """
    user = User(name="Second User", api_key="test2")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def tweet_id(db_session: AsyncSession, test_user: User):
    """
    Создает твит от имени первого тестового пользователя и возвращает его ID.

    Args:
        db_session (AsyncSession): Сессия базы данных.
        test_user (User): Объект автора твита.

    Returns:
        int: Идентификатор созданного твита.
    """
    tweet = Tweet(content="Test Tweet Content", author_id=test_user.id)
    db_session.add(tweet)
    await db_session.commit()
    await db_session.refresh(tweet)
    return tweet.id


@pytest.fixture(autouse=True)
def media_dir(tmp_path, monkeypatch):
    """
    Подменяет каталог загрузок на временный, чтобы тесты не оставляли файлы в static/media.

    Args:
        tmp_path (Path): Временный каталог pytest.
        monkeypatch (MonkeyPatch): Инструмент подмены атрибутов.

    Returns:
        Path: Временный каталог для загруженных файлов.
    """
    monkeypatch.setattr("app.services.media_service.UPLOAD_DIR", tmp_path)
    return tmp_path
