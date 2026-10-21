"""Голосовой ввод текста в активное окно."""

import logging
import os
import shutil
import subprocess

from config import LISTEN_TIMEOUT, PHRASE_TIME_LIMIT
from recognition import listen_microphone, recognize_audio

logger = logging.getLogger(__name__)

_STOP_WORDS = ("стоп", "хватит", "закончи ввод", "готово", "конец ввода")


def collect_text(max_phrases: int = 10) -> str:
    """Записывать фразы подряд, пока не сказано «стоп» или не истёк лимит."""
    parts = []
    for attempt in range(1, max_phrases + 1):
        logger.info("Фраза %d/%d", attempt, max_phrases)
        audio = listen_microphone(timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
        text = recognize_audio(audio)
        if not text:
            if attempt >= 3:
                break  # несколько пустых попыток подряд — выходим
            continue
        lower = text.lower().strip(" .!?")
        if lower in _STOP_WORDS or lower.startswith(("стоп", "хватит")):
            logger.info("Голосовой ввод завершён словом: %s", text)
            break
        parts.append(text)
        print(f"🗣 {text}")
    return " ".join(parts).strip()


def _copy_to_clipboard(text: str) -> bool:
    """Скопировать текст в буфер обмена (Wayland или X11)."""
    candidates = []
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
        candidates.append(["wl-copy"])
    if shutil.which("xclip"):
        candidates.append(["xclip", "-selection", "clipboard"])
    if shutil.which("xsel"):
        candidates.append(["xsel", "--clipboard", "--input"])

    for cmd in candidates:
        try:
            subprocess.run(cmd, input=text, text=True, check=True, timeout=5)
            return True
        except (subprocess.SubprocessError, OSError) as e:
            logger.debug("Не удалось скопировать через %s: %s", cmd[0], e)
    return False


def _paste_hotkey() -> bool:
    """Имитировать Ctrl+V (ydotool на Wayland, xdotool на X11)."""
    attempts = []
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("ydotool"):
        # 29 = KEY_LEFTCTRL, 47 = KEY_V
        attempts.append(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"])
    if shutil.which("xdotool"):
        attempts.append(["xdotool", "key", "ctrl+v"])

    for cmd in attempts:
        try:
            subprocess.run(cmd, check=True, timeout=5,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.SubprocessError, OSError) as e:
            logger.debug("Не удалось отправить %s: %s", cmd[0], e)
    return False


def send_text_to_active_window(text: str) -> bool:
    """Вставить текст в активное окно. Fallback — буфер обмена или консоль."""
    if not text.strip():
        return False

    if _copy_to_clipboard(text) and _paste_hotkey():
        logger.info("Текст вставлен в активное окно")
        return True

    if _copy_to_clipboard(text):
        logger.warning(
            "Текст скопирован в буфер обмена, но вставка не сработала. "
            "Нажмите Ctrl+V вручную (для Wayland: dnf install ydotool)"
        )
    else:
        logger.warning("Буфер обмена недоступен. Установите wl-clipboard или xclip")
    print(f"[JARVIS] Текст для вставки: {text}")
    return False


def voice_input_text(max_attempts: int = 10) -> str:
    """Голосовой ввод текста в активное окно."""
    print("🎙 Говорите. Скажите «стоп» для завершения.")
    text = collect_text(max_attempts)
    if text:
        send_text_to_active_window(text)
    else:
        print("⚠️ Ничего не распознано.")
    return text
