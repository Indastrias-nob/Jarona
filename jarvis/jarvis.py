#!/usr/bin/env python3
"""
Jarvis - голосовой помощник для Fedora Linux
Управление ПК, голосовой ввод текста, работа с файлами
"""

import os
import sys
import logging
from config import (
    TTS_ENGINE, TTS_LANGUAGE, WAKE_WORD_ENABLED,
    WAKE_WORD, TMP_DIR, DEFAULT_VOLUME
)
from recognition import recognize_command, listen_for_wake_word
from tts import speak
from pc_control import *
from file_ops import *
from voice_input import voice_input_text
from llm import understand
from context import append_message, clear_dialogue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Глобальное состояние
current_focus_mode = False


def print_banner():
    banner = """
╔════════════════════════════════════════╗
║        🤖  ГОЛОСОВОЙ ПОМОЩНИК JARVIS   ║
║       Управление ПК • Голосовой ввод   ║
╚════════════════════════════════════════╝
Тип:
 - 'слушай' для режима голосового ввода в окно
 - 'файлы' для работы с файлами
 - 'помощь' для списка команд
 - 'выход' для завершения
"""
    print(banner)


def process_command(cmd: str):
    """Обработка команды"""
    cmd_lower = cmd.lower().strip()

    if "выход" in cmd_lower or "закрой" in cmd_lower or "выключи" in cmd_lower:
        return False

    elif "помощь" in cmd_lower or "команды" in cmd_lower:
        list_commands()
    elif "слушай" in cmd_lower or "ввод" in cmd_lower:
        voice_input_text()
    elif "файлы" in cmd_lower or "создай" in cmd_lower or "открой" in cmd_lower:
        file_menu()
    elif "громкость" in cmd_lower:
        set_volume_from_command(cmd_lower)
    elif "открой" in cmd_lower or "запусти" in cmd_lower:
        launch_app(cmd_lower)
    elif "что открыто" in cmd_lower or "окна" in cmd_lower:
        list_open_windows()
    elif "сделай скриншот" in cmd_lower or "скриншот" in cmd_lower:
        take_screenshot()
    elif "затиши" in cmd_lower or "убавь" in cmd_lower:
        adjust_volume(cmd_lower, -10)
    elif "прибавь" in cmd_lower or "громче" in cmd_lower:
        adjust_volume(cmd_lower, 10)
    elif "поставь на паузу" in cmd_lower or "пауза" in cmd_lower:
        media_pause()
    else:
        # Передаём в распознаваемый текст активного окна
        logger.info(f"Команда не распознана: {cmd}")
        speak("Команда не распознана. Введите 'помощь' для списка.")
    return True


def list_commands():
    commands = [
        "слушай / ввод - голосовой ввод текста в активное окно",
        "файлы / создай файл / открой - управление файлами",
        "громче / тише / громкость 50 - управление звуком",
        "открой браузер / запусти firefox - запуск приложений",
        "скриншот - сделать скриншот экрана",
        "что открыто - список окон",
        "пауза - пауза медиа",
        "помощь - список команд",
        "выход - завершить работу",
    ]
    print("\n".join(commands))
    speak("Список команд:")
    for c in commands:
        speak(c)


def main():
    os.makedirs(TMP_DIR, exist_ok=True)
    print_banner()

    try:
        while True:
            if WAKE_WORD_ENABLED:
                command = listen_for_wake_word()
            else:
                command = recognize_command()

            if not command:
                continue

            print(f"👉 Вы: {command}")
            # Сохраняем сообщение в контекст диалога
            append_message("user", command)
            keep_running = process_command(command)
            if not keep_running:
                print("До свидания!")
                speak("До свидания.")
                break
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
        speak("До свидания.")


if __name__ == "__main__":
    main()
