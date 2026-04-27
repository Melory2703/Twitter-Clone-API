# 1. Базовый образ
FROM python:3.12-slim

# 2. Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Установка рабочей директории
WORKDIR /app

# 4. Копируем файлы зависимостей
COPY requirements-prod.txt requirements.in ./

# 5. Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# 6. Создаем пользователя
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser appuser

# 7. СОЗДАЕМ ПРАВИЛЬНЫЕ ПАПКИ
# создаем static/media
RUN mkdir -p /app/static/media /app/dist /app/app

# 8. Копируем проект
COPY dist /app/dist
COPY . .

# 9. НАСТРОЙКА ПРАВ
# Даем права на папку media
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app/static/media

# 10. Переключаемся на пользователя
USER appuser

# 11. Открываем порт
EXPOSE 8000

# 12. Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
