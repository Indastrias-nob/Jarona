#!/usr/bin/env python3
"""Операции с файлами: создание, открытие, удаление, копирование."""

import os
import logging
import subprocess
from datetime import datetime

from config import TMP_DIR

logger = logging.getLogger(__name__)


def create_file(path: str = None, content: str = ""):
    """Создать файл с контентом"""
    if path is None:
        path = os.path.join(TMP_DIR, f"jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        os.makedirs(os.path.dirname(path) or TMP_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Файл создан: {path}")
        print(f"Файл создан: {path}")
        return path
    except Exception as e:
        logger.error(f"Ошибка создания файла: {e}")
        return None


def open_file(path: str):
    """Открыть файл в текстовом редакторе"""
    if not os.path.exists(path):
        logger.error(f"Файл не найден: {path}")
        return False
    try:
        subprocess.run(["xdg-open", path])
        logger.info(f"Файл открыт: {path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка открытия файла: {e}")
        return False


def delete_file(path: str):
    """Удалить файл"""
    if not os.path.exists(path):
        logger.error(f"Файл не найден: {path}")
        return False
    try:
        os.remove(path)
        logger.info(f"Файл удалён: {path}")
        print(f"Файл удалён: {path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка удаления файла: {e}")
        return False


def file_menu():
    """Меню работы с файлами"""
    print("""
📁  РЕЖИМ РАБОТЫ С ФАЙЛАМИ
 - 'создай файл [имя]' - создать файл
 - 'открой файл [путь]' - открыть файл
 - 'удали файл [путь]' - удалить файл
""")
