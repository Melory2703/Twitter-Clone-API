# 🐦 Twitter Clone API (FastAPI)

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-bb0000?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)

Реализация бэкенда для сервиса микроблогов. Проект реализует полноценный REST API: систему подписок, создание твитов с медиафайлами и систему лайков.

---

## 🛠 Технологический стек

*   **Framework:** FastAPI (Async)
*   **Database:** PostgreSQL + SQLAlchemy 2.0 (Async mode)
*   **Validation:** Pydantic v2
*   **Infrastructure:** Docker, Docker Compose
*   **Quality Assurance:** Pytest, Flake8, Black, Mypy

---

## 📂 Управление зависимостями

В проекте используется продвинутая схема разделения пакетов:

1.  **requirements.in** — Базовые зависимости (ядро).
2.  **requirements-prod.txt** — Скомпилированные пакеты для работы в продакшене.
3.  **requirements-dev.txt** — Пакеты для разработки (тесты, линтеры).
4.  **requirements.txt** — Основной файл для синхронизации окружения.

---

## 🏗 Структура проекта

```text
.
├── app/                        # Основной пакет приложения (FastAPI)
│   ├── api/                    # Слой API: тонкие роутеры, принимают запрос и вызывают сервис
│   │   ├── deps.py             # Зависимости FastAPI: сборка сервисов, текущий пользователь по заголовку api-key
│   │   ├── users.py            # Эндпоинты пользователей: профили, подписки и отписки
│   │   ├── tweets.py           # Эндпоинты твитов: лента, создание, удаление, лайки
│   │   └── medias.py           # Эндпоинт загрузки медиафайлов (POST /api/medias)
│   ├── core/                   # Базовые настройки приложения
│   │   ├── config.py           # Пути проекта и лимиты загрузки (типы файлов, максимальный размер)
│   │   ├── database.py         # Настройка SQLAlchemy: движок, сессии, Base, get_session
│   │   └── exceptions.py       # Бизнес-исключения (400, 401, 404, 500), которые поднимают сервисы
│   ├── repositories/           # Слой данных: все запросы SQLAlchemy, без commit
│   │   ├── user_repository.py  # Запросы к пользователям и подпискам
│   │   ├── tweet_repository.py # Запросы к твитам и лайкам
│   │   └── media_repository.py # Запросы к медиафайлам
│   ├── services/               # Слой бизнес-логики: правила, вызов репозиториев, commit
│   │   ├── user_service.py     # Аутентификация, профили, подписки
│   │   ├── tweet_service.py    # Лента, создание, лайки, удаление твитов
│   │   └── media_service.py    # Сохранение файла на диск и запись о нём в БД
│   ├── scripts/                # Служебные скрипты (запуск через python -m)
│   │   ├── init_db.py          # Скрипт создания таблиц и первичной настройки БД
│   │   └── seed_db.py          # Скрипт для наполнения базы тестовыми данными
│   ├── main.py                 # Точка входа: запуск приложения, обработчики ошибок, подключение роутов
│   ├── models.py               # Описание таблиц базы данных (SQLAlchemy)
│   ├── schemas.py              # Схемы валидации данных (Pydantic / DTO)
│   └── __init__.py             # Делает папку 'app' доступным Python-пакетом
│
├── dist/                       # Собранный Frontend (Static Assets)
│   ├── css/                    # Стили интерфейса
│   ├── js/                     # Логика фронтенда (скрипты)
│   ├── favicon.ico             # Иконка сайта
│   └── index.html              # Главная страница (SPA)
│
├── static/                     # Хранилище статических файлов
│   └── media/                  # Загруженные пользователями изображения и файлы
│
├── tests/                      # Автоматизированные тесты (Pytest)
│   ├── resources/              # Вспомогательные файлы для тестов (картинки, json)
│   ├── conftest.py             # Фикстуры и глобальные настройки тестов
│   ├── test_api.py             # Интеграционные тесты API-эндпоинтов
│   └── __init__.py             # Позволяет импортировать модули внутри тестов
│
├── Dockerfile                  # Инструкции для сборки Docker-образа приложения
├── docker-compose.yml          # Описание всей инфраструктуры (App + DB)
│
├── requirements.txt            # Основной список зависимостей для работы
├── requirements-prod.txt       # Зависимости, оптимизированные для продакшена
├── requirements-dev.txt        # Зависимости для разработки (линтеры, отладка)
├── requirements.in             # Исходный список библиотек (для pip-tools)
│
├── pytest.ini                  # Конфигурация запуска тестов
├── setup.cfg                   # Настройки линтеров (Flake8) и форматирования
└── README.md                   # Документация проекта

```

---

## 🧱 Архитектура

Приложение разделено на слои: **api → services → repositories → БД**.
*   **api** принимает HTTP-запрос и возвращает ответ; SQL и бизнес-правил здесь нет.
*   **services** содержат бизнес-правила (нельзя подписаться на себя, удалять твит может только автор) и поднимают исключения из `core/exceptions.py`; `main.py` превращает их в JSON-ответ с нужным статусом.
*   **repositories** выполняют запросы SQLAlchemy к БД и больше ничего не делают.
*   **Транзакции:** репозиторий не делает `commit`; `commit` вызывает сервис, одна бизнес-операция = одна транзакция.

---

## 🚀 Инструкция по запуску

### 1. Подготовка окружения
Создайте файл `.env` в корне проекта:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=twitter_db
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/twitter_db
DB_ECHO=false
```

`DB_ECHO` — необязательная переменная: при значении `true` или `1` SQLAlchemy выводит все SQL-запросы в консоль (для отладки). По умолчанию (`false`, любое другое значение или переменная не задана) вывод выключен.

### 2. Запуск через Docker
```bash
docker compose up --build
```
> **Note:** Приложение доступно по адресу: **http://localhost:8000**  
> Интерактивная документация: **http://localhost:8000/docs**

### 3. Наполнение базы тестовыми данными (по желанию)
```bash
docker compose exec web python -m app.scripts.seed_db
```

---

## 📡 API Эндпоинты

| Метод | Эндпоинт | Описание |
| :--- | :--- | :--- |
| `GET` | `/api/users/me` | Получить информацию о своем профиле |
| `GET` | `/api/users/{id}` | Получить информацию о пользователе по ID |
| `POST` | `/api/users/{id}/follow` | Подписаться на пользователя |
| `DELETE` | `/api/users/{id}/follow` | Отписаться от пользователя |
| `GET` | `/api/tweets` | Получить ленту твитов |
| `POST` | `/api/tweets` | Создать новый твит |
| `DELETE` | `/api/tweets/{id}` | Удалить твит |
| `POST` | `/api/medias` | Загрузить медиафайл (картинку) |
| `POST` | `/api/tweets/{id}/likes` | Поставить лайк твиту |
| `DELETE` | `/api/tweets/{id}/likes` | Убрать лайк |

### Лимиты загрузки медиафайлов
`POST /api/medias` принимает только изображения следующих типов (проверяется `Content-Type`): `image/jpeg`, `image/png`, `image/gif`, `image/webp`. Максимальный размер файла — **5 МБ**. При нарушении возвращается `400` с описанием ошибки. Если у имени файла нет расширения, файл сохраняется с расширением `.bin`. Лимиты заданы в `app/core/config.py` (`ALLOWED_MEDIA_TYPES`, `MAX_UPLOAD_SIZE`).

---

## 🧪 Тестирование и Качество

### Запуск тестов
Для запуска автоматических тестов внутри контейнера или локально:
```bash
pytest --cov=app tests/
```

### Проверка стиля (Linters)
```bash
black .          # Форматирование
flake8 app       # Проверка стандартов PEP8
mypy app         # Проверка типов
```

---

## 💎 Ключевые особенности

*   **Async/Await:** Полностью асинхронный стек.
*   **Media Handling:** Автоматическая генерация уникальных имен (UUID4) для загружаемых файлов для защиты от перезаписи.
*   **Upload Validation:** Проверка типа (jpeg, png, gif, webp) и размера (до 5 МБ) загружаемых файлов, проверка существования вложений при создании твита.
*   **Data Integrity:** Использование внешних ключей и индексов в PostgreSQL для связей «подписчики» и «лайки».
*   **Scalability:** Готовность к деплою через Docker-контейнеры.
