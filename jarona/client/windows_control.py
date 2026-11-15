"""Управление Windows через WinAPI и системные утилиты."""

import logging
import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# Проверка платформы
if sys.platform != "win32":
    logger.warning("windows_control работает только на Windows")


# --- Громкость ---

def get_volume() -> Optional[int]:
    """Получить текущую громкость (0-100)."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)

        return int(volume.GetMasterVolumeLevelScalar() * 100)
    except Exception as e:
        logger.error(f"Ошибка чтения громкости: {e}")
        return None


def set_volume(level: int) -> bool:
    """Установить громкость (0-100)."""
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL

        level = max(0, min(100, level))

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)

        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        logger.info(f"Громкость установлена: {level}%")
        return True
    except Exception as e:
        logger.error(f"Ошибка установки громкости: {e}")
        return False


def volume_up(step: int = 10) -> bool:
    """Увеличить громкость."""
    current = get_volume()
    if current is not None:
        return set_volume(current + step)
    return False


def volume_down(step: int = 10) -> bool:
    """Уменьшить громкость."""
    current = get_volume()
    if current is not None:
        return set_volume(current - step)
    return False


def mute() -> bool:
    """Выключить звук."""
    return set_volume(0)


# --- Приложения ---

APP_ALIASES = {
    "браузер": "explorer https://google.com",
    "browser": "explorer https://google.com",
    "firefox": "firefox",
    "chrome": "chrome",
    "хром": "chrome",
    "edge": "msedge",
    "терминал": "cmd",
    "terminal": "cmd",
    "powershell": "powershell",
    "блокнот": "notepad",
    "notepad": "notepad",
    "калькулятор": "calc",
    "calculator": "calc",
    "проводник": "explorer",
    "explorer": "explorer",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "outlook": "outlook",
}


def open_app(app_name: str) -> bool:
    """Запустить приложение."""
    app_lower = app_name.lower().strip()

    # Алиасы
    if app_lower in APP_ALIASES:
        cmd = APP_ALIASES[app_lower]
    else:
        cmd = app_name

    # URL
    if cmd.startswith(("http://", "https://", "www.")):
        webbrowser.open(cmd)
        logger.info(f"Открыт URL: {cmd}")
        return True

    # Программа
    try:
        subprocess.Popen(cmd, shell=True)
        logger.info(f"Запущено: {cmd}")
        return True
    except Exception as e:
        logger.error(f"Ошибка запуска {app_name}: {e}")
        return False


def open_browser() -> bool:
    """Открыть браузер по умолчанию."""
    webbrowser.open("https://google.com")
    return True


def open_terminal() -> bool:
    """Открыть терминал."""
    return open_app("cmd")


# --- Файлы ---

def resolve_path(path: str) -> Path:
    """Развернуть путь."""
    return Path(path).expanduser().resolve()


def create_file(path: str, content: str = "") -> bool:
    """Создать файл."""
    try:
        file_path = resolve_path(path)

        if file_path.exists():
            logger.warning(f"Файл уже существует: {file_path}")
            return False

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        logger.info(f"Файл создан: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка создания файла: {e}")
        return False


def write_file(path: str, content: str, append: bool = False) -> bool:
    """Записать в файл."""
    try:
        file_path = resolve_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if append else "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)

        action = "дописан" if append else "записан"
        logger.info(f"Файл {action}: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка записи файла: {e}")
        return False


def read_file(path: str) -> Optional[str]:
    """Прочитать файл."""
    try:
        file_path = resolve_path(path)
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Ошибка чтения файла: {e}")
        return None


def open_file(path: str) -> bool:
    """Открыть файл в приложении по умолчанию."""
    try:
        file_path = resolve_path(path)
        os.startfile(str(file_path))
        logger.info(f"Файл открыт: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка открытия файла: {e}")
        return False


def open_folder(path: str) -> bool:
    """Открыть папку в проводнике."""
    try:
        folder_path = resolve_path(path)
        os.startfile(str(folder_path))
        logger.info(f"Папка открыта: {folder_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка открытия папки: {e}")
        return False


def delete_file(path: str) -> bool:
    """Удалить файл."""
    try:
        file_path = resolve_path(path)
        file_path.unlink()
        logger.info(f"Файл удалён: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка удаления файла: {e}")
        return False


# --- Скриншот ---

def screenshot(output_path: Optional[str] = None) -> Optional[str]:
    """Сделать скриншот."""
    try:
        from PIL import ImageGrab

        if not output_path:
            from datetime import datetime
            output_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        img = ImageGrab.grab()
        img.save(output_path)

        logger.info(f"Скриншот сохранён: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Ошибка скриншота: {e}")
        return None


# --- Поиск в интернете ---

def search_web(query: str) -> bool:
    """Поиск в Google."""
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    webbrowser.open(url)
    logger.info(f"Поиск: {query}")
    return True


# --- Медиа ---

def media_control(action: str) -> bool:
    """Управление медиа (play/pause/next/prev)."""
    # Эмуляция media keys через nircmd или другие утилиты
    # TODO: реализовать через pyautogui или win32api
    logger.warning("media_control пока не реализован")
    return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("Тест Windows control...")

    # Громкость
    vol = get_volume()
    print(f"Текущая громкость: {vol}%")

    # Браузер
    # open_browser()

    # Файл
    # create_file("test.txt", "Hello from Jarona!")
