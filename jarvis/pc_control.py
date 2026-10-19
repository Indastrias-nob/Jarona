"""
Управление ПК: громкость, приложения, окна, скриншоты, медиа.
"""

import logging
import subprocess
import re

logger = logging.getLogger(__name__)


def get_volume():
    """Текущая громкость в %"""
    try:
        out = subprocess.run(
            ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
            capture_output=True, text=True, check=True
        )
        for line in out.stdout.splitlines():
            if "%" in line:
                return int(line.split("%")[0].split()[-1])
    except Exception as e:
        logger.error(f"Ошибка получения громкости: {e}")
    return 50


def adjust_volume(cmd: str, delta: int):
    """Изменить громкость на +/- delta%"""
    try:
        current = get_volume()
        new_vol = min(100, max(0, current + delta))
        subprocess.run(
            f"pactl set-sink-volume @DEFAULT_SINK@ {new_vol}%",
            shell=True, check=True
        )
        logger.info(f"Громкость: {current}% -> {new_vol}%")
        return new_vol
    except Exception as e:
        logger.error(f"Ошибка изменения громкости: {e}")
        return None


def set_volume_from_command(cmd: str):
    """Установить громкость по числу: 'громкость 60'"""
    nums = re.findall(r"\d+", cmd)
    if nums:
        vol = min(100, max(0, int(nums[0])))
        subprocess.run(
            f"pactl set-sink-volume @DEFAULT_SINK@ {vol}%",
            shell=True, check=True
        )
        logger.info(f"Громкость установлена: {vol}%")
        return vol
    return get_volume()


def launch_app(cmd: str):
    """Запустить приложение по имени"""
    app_map = {
        "браузер": "firefox",
        "хром": "chromium-browser",
        "chrome": "google-chrome",
        "терминал": "gnome-terminal",
        "редактор": "gedit",
        "vlc": "vlc",
        "почта": "thunderbird",
    }
    matched = None
    for key in app_map:
        if key in cmd:
            matched = app_map[key]
            break
    if matched:
        subprocess.Popen([matched], shell=False)
        logger.info(f"Запущено: {matched}")
        return matched
    logger.warning(f"Приложение не найдено: {cmd}")
    return None


def list_open_windows():
    """Список открытых окон"""
    try:
        out = subprocess.run(
            ["xdotool", "search", "--name", "."],
            capture_output=True, text=True, check=True
        )
        pids = [w.strip() for w in out.stdout.strip().split("\n") if w.strip()]
        details = []
        for w in pids:
            try:
                name = subprocess.run(
                    ["xdotool", "getwindowname", w],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
                details.append(f"{w}: {name}")
            except Exception:
                details.append(w)
        result = "\n".join(details)
        print("\nОткрытые окна:\n" + result)
        return result
    except Exception as e:
        logger.error(f"Ошибка xdotool: {e}")
        return None


def take_screenshot():
    """Сделать скриншот"""
    import time
    filename = f"/tmp/jarvis/screenshot_{int(time.time())}.png"
    try:
        subprocess.run(["gnome-screenshot", "-f", filename], check=True)
    except Exception:
        subprocess.run(["import", "-window", "root", filename], shell=True)
    logger.info(f"Скриншот: {filename}")
    return filename


def media_pause():
    """Пауза/возобновить медиа"""
    try:
        subprocess.run(["playerctl", "play-pause"], check=True, timeout=5)
    except Exception:
        logger.warning("playerctl недоступен")
