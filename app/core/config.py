"""
Модуль с путями проекта.
Единственное место, где определяется каталог для хранения загруженных медиафайлов.
"""

from pathlib import Path

# Корень проекта: app/core/config.py -> app/core -> app -> <корень>
BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "static" / "media"

# Допустимые типы загружаемых медиафайлов (проверяются по Content-Type)
ALLOWED_MEDIA_TYPES = frozenset(("image/jpeg", "image/png", "image/gif", "image/webp"))
# Максимальный размер загружаемого файла, байт (5 МБ)
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
