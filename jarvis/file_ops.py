"""Операции с файлами: создание, открытие, удаление, копирование.

Удаление и запись ограничены каталогами из ALLOWED_FILE_ROOTS.
"""

import logging
import os
import shutil
import subprocess
from datetime import datetime

from config import ALLOWED_FILE_ROOTS, TMP_DIR  # noqa: F401

logger = logging.getLogger(__name__)


class UnsafePathError(ValueError):
    """Путь вне разрешённых каталогов."""


def resolve_path(path: str) -> str:
    """Развернуть ~ и привести путь к абсолютному виду."""
    if not path:
        raise ValueError("Пустой путь")
    return os.path.abspath(os.path.expanduser(path.strip().strip('"').strip("'")))


def is_path_allowed(path: str, roots=None) -> bool:
    """Проверить, что путь находится внутри разрешённых каталогов."""
    if roots is None:
        # Читаем из config динамически, чтобы настройку можно было менять в рантайме
        import config

        roots = config.ALLOWED_FILE_ROOTS
    if not roots:
        return True
    real = os.path.realpath(resolve_path(path))
    for root in roots:
        real_root = os.path.realpath(os.path.expanduser(root))
        if real == real_root or real.startswith(real_root + os.sep):
            return True
    return False


def _require_allowed(path: str) -> str:
    resolved = resolve_path(path)
    if not is_path_allowed(resolved):
        raise UnsafePathError(f"Путь вне разрешённой области: {resolved}")
    return resolved


def default_output_dir() -> str:
    """Каталог для файлов, созданных без явного пути."""
    import config

    directory = os.path.join(config.DATA_DIR, "files")
    os.makedirs(directory, exist_ok=True)
    return directory


def create_file(path: str = None, content: str = "", overwrite: bool = False):
    """Создать файл с содержимым. Возвращает путь или None."""
    if not path:
        path = os.path.join(
            default_output_dir(),
            f"jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
    try:
        path = _require_allowed(path)
        if os.path.exists(path) and not overwrite:
            logger.warning("Файл уже существует: %s", path)
            return None
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Файл создан: %s", path)
        return path
    except (UnsafePathError, OSError, ValueError) as e:
        logger.error("Ошибка создания файла: %s", e)
        return None


def open_file(path: str):
    """Открыть файл приложением по умолчанию."""
    try:
        path = resolve_path(path)
    except ValueError as e:
        logger.error("Ошибка открытия файла: %s", e)
        return False
    if not os.path.exists(path):
        logger.error("Файл не найден: %s", path)
        return False
    try:
        subprocess.Popen(
            ["xdg-open", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except OSError as e:
        logger.error("Ошибка открытия файла: %s", e)
        return False


def write_file(path: str, content: str = "", append: bool = False):
    """Записать или дописать текст в файл. Возвращает путь или None."""
    try:
        path = _require_allowed(path)
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        existed = os.path.exists(path)
        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            prefix = "\n" if append and existed and os.path.getsize(path) else ""
            f.write(prefix + content)
        action = "дописан" if append else "записан"
        logger.info("Файл %s: %s", action, path)
        return path
    except (UnsafePathError, OSError, ValueError) as e:
        logger.error("Ошибка записи файла: %s", e)
        return None


def read_file(path: str, max_chars: int = 4000):
    """Прочитать текстовый файл (для LLM)."""
    try:
        path = resolve_path(path)
        if not is_path_allowed(path):
            return None
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except (OSError, ValueError) as e:
        logger.error("Ошибка чтения файла: %s", e)
        return None


def delete_file(path: str):
    """Удалить файл (только внутри разрешённых каталогов)."""
    try:
        path = _require_allowed(path)
    except (UnsafePathError, ValueError) as e:
        logger.error("Отказ в удалении: %s", e)
        return False
    if not os.path.isfile(path):
        logger.error("Файл не найден: %s", path)
        return False
    try:
        os.remove(path)
        logger.info("Файл удалён: %s", path)
        return True
    except OSError as e:
        logger.error("Ошибка удаления файла: %s", e)
        return False


def copy_file(src: str, dst_dir: str):
    """Скопировать файл в каталог."""
    try:
        src = resolve_path(src)
        dst_dir = _require_allowed(dst_dir)
    except (UnsafePathError, ValueError) as e:
        logger.error("Ошибка копирования: %s", e)
        return None
    if not os.path.isfile(src):
        logger.error("Исходный файл не найден: %s", src)
        return None
    try:
        os.makedirs(dst_dir, exist_ok=True)
        result = shutil.copy2(src, dst_dir)
        logger.info("Файл скопирован: %s", result)
        return result
    except OSError as e:
        logger.error("Ошибка копирования: %s", e)
        return None


def list_directory(path: str, limit: int = 100):
    """Содержимое каталога (имена)."""
    try:
        path = resolve_path(path)
        if not is_path_allowed(path):
            return []
        with os.scandir(path) as entries:
            names = sorted(e.name for e in entries)
        return names[:limit]
    except (OSError, ValueError) as e:
        logger.error("Ошибка чтения каталога: %s", e)
        return []


def format_text_file(path: str, action: str = "upper"):
    """Изменить регистр текста в файле: upper | lower | title."""
    try:
        path = _require_allowed(path)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except (UnsafePathError, OSError, ValueError) as e:
        logger.error("Ошибка форматирования: %s", e)
        return False

    if action == "upper":
        text = text.upper()
    elif action == "lower":
        text = text.lower()
    elif action == "title":
        text = text.title()
    else:
        logger.error("Неизвестное действие форматирования: %s", action)
        return False

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("Файл отформатирован (%s): %s", action, path)
        return True
    except OSError as e:
        logger.error("Ошибка записи после форматирования: %s", e)
        return False
