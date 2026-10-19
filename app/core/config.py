"""
Модуль с путями проекта.
Единственное место, где определяется каталог для хранения загруженных медиафайлов.
"""

from pathlib import Path

# Корень проекта: app/core/config.py -> app/core -> app -> <корень>
BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "static" / "media"
