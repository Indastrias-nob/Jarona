"""Синтез речи: espeak-ng/espeak, Google TTS (gTTS) с деградацией до консоли."""

import logging
import os
import shutil
import subprocess

from config import TMP_DIR, TTS_ENGINE, TTS_LANGUAGE, TTS_PITCH, TTS_RATE

logger = logging.getLogger(__name__)

_enabled = True


def set_enabled(enabled: bool):
    """Включить/выключить озвучку (ответы будут печататься в консоль)."""
    global _enabled
    _enabled = enabled


def _find_binary(*names: str):
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def speak(text: str):
    """Озвучить и продублировать текст в консоль (не бросает исключений)."""
    if not text or not text.strip():
        return
    text = text.strip()
    print(f"🤖 {text}")
    if not _enabled:
        return
    logger.debug("Говорю: %s", text)

    try:
        if TTS_ENGINE == "gtts":
            tts_google(text)
        elif TTS_ENGINE == "espeak":
            tts_espeak(text)
        else:  # auto
            tts_espeak(text) or tts_google(text)
    except Exception as e:  # озвучка не должна ронять ассистента
        logger.error("Ошибка синтеза речи: %s", e)


def tts_espeak(text: str) -> bool:
    """espeak-ng или espeak. Возвращает True при успехе."""
    binary = _find_binary("espeak-ng", "espeak")
    if not binary:
        logger.debug("espeak-ng/espeak не найден")
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
        logger.error("Ошибка espeak: %s", e)
        return False


def tts_google(text: str) -> bool:
    """Google TTS через gTTS, воспроизведение через paplay/ffplay."""
    try:
        from gtts import gTTS
    except ImportError:
        logger.debug("gTTS не установлен")
        return False

    player = _find_binary("paplay", "ffplay", "mpv", "aplay")
    if not player:
        logger.debug("Не найден аудиоплеер для gTTS")
        return False

    filename = os.path.join(TMP_DIR, "response.mp3")
    try:
        os.makedirs(TMP_DIR, exist_ok=True)
        gTTS(text=text, lang=TTS_LANGUAGE, slow=False).save(filename)
        cmd = [player]
        if player.endswith("ffplay"):
            cmd += ["-nodisp", "-autoexit", "-loglevel", "quiet"]
        subprocess.run(
            cmd + [filename],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
        )
        return True
    except Exception as e:
        logger.error("Ошибка gTTS: %s", e)
        return False
