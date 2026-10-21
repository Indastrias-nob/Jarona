#!/usr/bin/env python3
"""Скрипт установки зависимостей проекта Jarvis."""

import os
import shutil
import subprocess
import sys

SYSTEM_PACKAGES = {
    "espeak-ng": "синтез речи (TTS)",
    "wl-clipboard": "буфер обмена на Wayland",
    "xclip": "буфер обмена на X11",
    "ydotool": "имитация Ctrl+V на Wayland",
    "xdotool": "имитация Ctrl+V и список окон на X11",
    "playerctl": "управление медиаплеерами",
    "grim": "скриншоты на Wayland",
    "gnome-screenshot": "скриншоты в GNOME",
}


def install_requirements():
    """Устанавливает Python-зависимости из requirements.txt."""
    root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root, "requirements.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            requirements = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    except FileNotFoundError:
        print("❌ Файл requirements.txt не найден!")
        sys.exit(1)

    if not requirements:
        print("⚠️ Файл requirements.txt пуст.")
        return

    print(f"Устанавливается {len(requirements)} зависимостей...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", path],
        check=False,
    )

    if result.returncode == 0:
        print("✅ Python-зависимости установлены!")
    else:
        print("❌ Ошибка при установке зависимостей.")
        sys.exit(result.returncode)


def check_system_packages():
    """Проверяет наличие системных утилит и подсказывает, что доустановить."""
    missing = [pkg for pkg in SYSTEM_PACKAGES if not shutil.which(pkg)]
    if not missing:
        print("✅ Все системные утилиты на месте.")
        return

    print("\n⚠️ Не хватает системных утилит:")
    for pkg in missing:
        print(f"   - {pkg}: {SYSTEM_PACKAGES[pkg]}")
    print("\nУстановить:  sudo dnf install " + " ".join(missing))


if __name__ == "__main__":
    install_requirements()
    check_system_packages()
