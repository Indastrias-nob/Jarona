#!/usr/bin/env python3
"""Голосовой ввод текста в активное окно."""

import logging
import subprocess

from recognition import recognize_command, listen_for_wake_word
from config import WAKE_WORD_ENABLED, TMP_DIR

logger = logging.getLogger(__name__)


def voice_input_text(max_attempts: int = 3):
    """Голосовой ввод текста в активное окно. Повторять max_attempts раз."""
    collected = []
    for i in range(max_attempts):
        logger.info(f"Попытка {i + 1}/{max_attempts}")
        if WAKE_WORD_ENABLED:
            command = listen_for_wake_word()
        else:
            command = recognize_command()

        if command:
            collected.append(command)
            print(f"🗣 Голос: {command}")
        else:
            print("⚠️ Голос не распознан, попробуйте ещё раз.")

    text = " ".join(collected).strip()
    if text:
        _send_to_active_window(text)
    return text


def _send_to_active_window(text: str):
    """Отправить текст в активное окно (Ctrl+V)"""
    try:
        # Копировать текст в буфер обмена
        subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
        # Вставить: имитация нажатия Ctrl+V
        subprocess.run(["xdotool", "key", "ctrl+v"])
        logger.info(f"Текст отправлен в активное окно: {text}")
    except FileNotFoundError:
        logger.warning("xclip/xdotool не установлены. Установите: dnf install xclip xdotool")
        print(f"[JARVIS] Текст для вставки: {text}")
    except Exception as e:
        logger.error(f"Ошибка отправки текста: {e}")
