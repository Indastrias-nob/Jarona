#!/usr/bin/env python3
"""Скрипт установки зависимостей проекта Jarvis."""

import subprocess
import sys


def install_requirements():
    """Устанавливает зависимости из requirements.txt."""
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            requirements = f.read().splitlines()
    except FileNotFoundError:
        print("❌ Файл requirements.txt не найден!")
        sys.exit(1)

    if not requirements:
        print("⚠️ Файл requirements.txt пуст.")
        return

    print(f"Устанавливается {len(requirements)} зависимостей...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        check=False,
    )

    if result.returncode == 0:
        print("✅ Зависимости успешно установлены!")
    else:
        print("❌ Ошибка при установке зависимостей.")
        sys.exit(result.returncode)


if __name__ == "__main__":
    install_requirements()
