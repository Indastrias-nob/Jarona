"""Синтез речи через espeak-ng для Orange Pi."""

import logging
import os
import shutil
import subprocess
from typing import Optional

from config import TMP_DIR, TTS_ENGINE, TTS_LANGUAGE, TTS_PITCH, TTS_RATE

logger = logging.getLogger(__name__)

_enabled = True


def set_enabled(enabled: bool):
    """Включить/выключить TTS."""
    global _enabled
    _enabled = enabled


def speak(text: str):
    """Озвучить текст."""
    if not text or not text.strip():
        return

    text = text.strip()
    print(f"🤖 {text}")

    if not _enabled or TTS_ENGINE == "disabled":
        return

    logger.debug(f"TTS: {text}")

    try:
        if TTS_ENGINE == "gtts":
            tts_google(text)
        elif TTS_ENGINE == "espeak":
            tts_espeak(text)
        else:
            logger.warning(f"Неизвестный TTS движок: {TTS_ENGINE}")
    except Exception as e:
        logger.error(f"Ошибка TTS: {e}")


def tts_espeak(text: str) -> bool:
    """Синтез через espeak-ng."""
    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    if not binary:
        logger.debug("espeak не найден")
        return False

    try:
        subprocess.run(
            [
                binary,
                "-v", TTS_LANGUAGE,
                "-p", str(TTS_PITCH),
                "-s", str(TTS_RATE),
                text,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error(f"Ошибка espeak: {e}")
        return False


def tts_google(text: str) -> bool:
    """Синтез через Google TTS (gTTS)."""
    try:
        from gtts import gTTS
    except ImportError:
        logger.debug("gTTS не установлен")
        return False

    player = shutil.which("paplay") or shutil.which("aplay") or shutil.which("mpv")
    if not player:
        logger.debug("Аудиоплеер не найден")
        return False

    filename = TMP_DIR / "tts.mp3"
    try:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        gTTS(text=text, lang=TTS_LANGUAGE, slow=False).save(str(filename))

        subprocess.run(
            [player, str(filename)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка gTTS: {e}")
        return False
    finally:
        if filename.exists():
            filename.unlink()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    speak("Привет! Я Жарона, голосовой помощник для Ориндж Пай.")
    speak("Тестирование синтеза речи.")
