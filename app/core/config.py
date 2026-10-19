"""
Модуль с путями проекта.
Единственное место, где определяется каталог для хранения загруженных медиафайлов.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "static" / "media"
ALLOWED_MEDIA_TYPES = frozenset(("image/jpeg", "image/png", "image/gif", "image/webp"))
MAX_UPLOAD_SIZE = 5 * 1024 * 1024
