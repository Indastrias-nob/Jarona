"""Управление ПК: громкость, приложения, окна, скриншоты, медиа."""

import logging
import os
import re
import shutil
import subprocess
from urllib.parse import quote_plus

from config import TMP_DIR, VOLUME_STEP

logger = logging.getLogger(__name__)

SINK = "@DEFAULT_SINK@"

# Приложения по ключевым словам (сначала более конкретные)
_APP_ALIASES = {
    "браузер": ["firefox", "google-chrome", "chromium"],
    "browser": ["firefox", "google-chrome", "chromium"],
    "firefox": ["firefox"],
    "фаерфокс": ["firefox"],
    "хром": ["google-chrome", "chromium"],
    "chrome": ["google-chrome"],
    "chromium": ["chromium"],
    "терминал": ["gnome-terminal", "konsole", "xterm"],
    "terminal": ["gnome-terminal", "konsole", "xterm"],
    "редактор": ["gedit", "gnome-text-editor", "kate"],
    "текстовый редактор": ["gnome-text-editor", "gedit"],
    "файлы": ["nautilus"],
    "проводник": ["nautilus"],
    "почта": ["thunderbird"],
    "телеграм": ["telegram-desktop"],
    "telegram": ["telegram-desktop"],
    "телеграмм": ["telegram-desktop"],
    "код": ["code"],
    "vs code": ["code"],
    "vscode": ["code"],
    "vlc": ["vlc"],
    "плеер": ["vlc"],
    "калькулятор": ["gnome-calculator"],
    "настройки": ["gnome-control-center"],
    "параметры": ["gnome-control-center"],
    "дискорд": ["discord"],
    "discord": ["discord"],
    "спотифай": ["spotify"],
    "spotify": ["spotify"],
}

_URL_PREFIXES = ("http://", "https://", "www.")


def _run(args, timeout=10, **kwargs):
    """Запустить команду без shell и вернуть CompletedProcess или None."""
    try:
        return subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, **kwargs
        )
    except FileNotFoundError:
        logger.debug("Команда не найдена: %s", args[0])
    except subprocess.TimeoutExpired:
        logger.error("Команда %s не завершилась за %d с", args[0], timeout)
    except (subprocess.SubprocessError, OSError) as e:
        logger.error("Ошибка выполнения %s: %s", args[0], e)
    return None


def _has(binary: str) -> bool:
    return shutil.which(binary) is not None


# --------------------------------------------------------------------------- #
# Громкость
# --------------------------------------------------------------------------- #
def get_volume():
    """Текущая громкость в % (0..100) или None, если узнать не удалось."""
    out = _run(["pactl", "get-sink-volume", SINK])
    if not out or out.returncode != 0:
        return None
    match = re.search(r"(\d+)%", out.stdout)
    return int(match.group(1)) if match else None


def set_volume(volume: int):
    """Установить громкость в %."""
    volume = max(0, min(100, int(volume)))
    out = _run(["pactl", "set-sink-volume", SINK, f"{volume}%"])
    if out is None or out.returncode != 0:
        return None
    logger.info("Громкость установлена: %d%%", volume)
    return volume


def adjust_volume(delta: int):
    """Изменить громкость на delta %."""
    current = get_volume()
    if current is None:
        return None
    return set_volume(current + delta)


def mute(muted: bool = True):
    """Включить/выключить звук."""
    out = _run(["pactl", "set-sink-mute", SINK, "1" if muted else "0"])
    ok = out is not None and out.returncode == 0
    if ok:
        logger.info("Звук %s", "выключен" if muted else "включён")
    return ok


def set_volume_from_command(cmd: str):
    """Разобрать команду вида «громкость 60», «громче», «тише», «выключи звук»."""
    lower = cmd.lower()
    if any(word in lower for word in ("выключи звук", "без звука", "mute")):
        mute(True)
        return get_volume()
    if "включи звук" in lower:
        mute(False)
        return get_volume()

    nums = re.findall(r"\d+", cmd)
    if nums:
        return set_volume(int(nums[0]))
    if any(word in lower for word in ("громче", "прибавь", "увеличь")):
        return adjust_volume(VOLUME_STEP)
    if any(word in lower for word in ("тише", "убавь", "затиши", "уменьшь")):
        return adjust_volume(-VOLUME_STEP)
    return get_volume()


# --------------------------------------------------------------------------- #
# Приложения
# --------------------------------------------------------------------------- #
def _resolve_app(name: str):
    """Найти исполняемый файл приложения по имени."""
    if not name:
        return None
    name = name.strip().lower()
    if _has(name):
        return name
    for keyword, candidates in _APP_ALIASES.items():
        if keyword in name:
            for candidate in candidates:
                if _has(candidate):
                    return candidate
    # последняя попытка: имя без пробелов
    compact = name.replace(" ", "-")
    if _has(compact):
        return compact
    return None


def launch_app(cmd: str):
    """Запустить приложение по имени из команды. Возвращает имя или None."""
    executable = _resolve_app(cmd)
    if executable:
        try:
            subprocess.Popen(
                [executable],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            logger.info("Запущено: %s", executable)
            return executable
        except OSError as e:
            logger.error("Не удалось запустить %s: %s", executable, e)
    logger.warning("Приложение не найдено: %s", cmd)
    return None


def search_web(query: str):
    """Открыть поиск в браузере."""
    if not query:
        return None
    url = "https://www.google.com/search?q=" + quote_plus(query)
    return open_url(url)


def open_url(url: str):
    """Открыть URL в браузере по умолчанию."""
    if not url.startswith(_URL_PREFIXES):
        url = "https://" + url
    try:
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        logger.info("Открыт URL: %s", url)
        return url
    except OSError as e:
        logger.error("Не удалось открыть URL %s: %s", url, e)
        return None


# --------------------------------------------------------------------------- #
# Окна и скриншоты
# --------------------------------------------------------------------------- #
def list_open_windows():
    """Список открытых окон (X11 через xdotool; на Wayland — заглушка)."""
    if not _has("xdotool"):
        logger.info("xdotool недоступен (Wayland) — список окон недоступен")
        return []
    out = _run(["xdotool", "search", "--name", "."])
    if not out or out.returncode != 0:
        return []

    titles = []
    for window_id in out.stdout.split():
        name = _run(["xdotool", "getwindowname", window_id])
        if name and name.returncode == 0 and name.stdout.strip():
            titles.append(name.stdout.strip())
    titles = list(dict.fromkeys(titles))
    if titles:
        print("\nОткрытые окна:\n" + "\n".join(titles))
    return titles


def take_screenshot(directory: str = TMP_DIR):
    """Сделать скриншот. Возвращает путь или None."""
    import time

    os.makedirs(directory, exist_ok=True)
    filename = os.path.join(directory, f"screenshot_{int(time.time())}.png")

    if os.environ.get("WAYLAND_DISPLAY") and _has("grim"):
        args = ["grim", filename]
    elif _has("gnome-screenshot"):
        args = ["gnome-screenshot", "-f", filename]
    elif _has("import"):
        args = ["import", "-window", "root", filename]
    else:
        logger.error("Не найден инструмент для скриншотов")
        return None

    out = _run(args, timeout=30)
    if out is None or out.returncode != 0 or not os.path.exists(filename):
        logger.error(
            "Не удалось сделать скриншот (%s): %s",
            args[0],
            (out.stderr or "").strip() if out else "команда не запущена",
        )
        return None
    logger.info("Скриншот: %s", filename)
    return filename


# --------------------------------------------------------------------------- #
# Медиа
# --------------------------------------------------------------------------- #
def media_control(action: str = "play_pause"):
    """Управление медиаплеером через playerctl."""
    mapping = {
        "play_pause": "play-pause",
        "play": "play",
        "pause": "pause",
        "next": "next",
        "prev": "previous",
        "stop": "stop",
    }
    if not _has("playerctl"):
        logger.warning("playerctl недоступен")
        return False
    command = mapping.get(action, "play-pause")
    out = _run(["playerctl", command])
    return out is not None and out.returncode == 0


def media_pause():
    """Пауза/возобновление медиа."""
    return media_control("play_pause")
