"""Логирование Jarvis: консоль + файл в DATA_DIR."""

import logging
import os
import sys

from config import DATA_DIR, LOG_PATH


def setup_logging(level: int = logging.INFO):
    """Настроить корневой логгер один раз."""
    root = logging.getLogger()
    if getattr(root, "_jarvis_configured", False):
        return root

    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError as e:  # каталог недоступен — работаем без файла
        root.warning("Не удалось открыть лог-файл %s: %s", LOG_PATH, e)

    root._jarvis_configured = True
    return root
