import os
import logging
import subprocess
import sys
from config import TTS_ENGINE, TTS_LANGUAGE, TMP_DIR

logger = logging.getLogger(__name__)


def speak(text: str):
    """Произнести текст голосом"""
    if not text:
        return

    text = text.strip()
    if not text:
        return

    logger.debug(f"🔊 Говорю: {text}")

    try:
        if TTS_ENGINE == "gtts":
            tts_google(text)
        elif TTS_ENGINE == "espeak":
            tts_espeak(text)
        else:
            tts_espeak(text)
    except Exception as e:
        logger.error(f"Ошибка синтеза речи: {e}")
        print(f"[JARVIS] Ошибка озвучки: {e}")


def tts_google(text: str):
    """Google TTS через gTTS"""
    try:
        from gtts import gTTS
        filename = os.path.join(TMP_DIR, "response.mp3")
        tts = gTTS(text=text, lang=TTS_LANGUAGE, slow=False)
        tts.save(filename)
        subprocess.run(["paplay", filename], check=True)
    except ImportError:
        logger.warning("gTTS не установлен, переключаемся на espeak")
        tts_espeak(text)
    except Exception as e:
        logger.error(f"Ошибка gTTS: {e}")


def tts_espeak(text: str):
    """espeak (предустановлен на Fedora)"""
    import shutil

    espeak = shutil.which("espeak")
    if not espeak:
        logger.warning("espeak не найден, используем fallback")
        print(f"[JARVIS] {text}")
        return

    # Экранирование кавычек и спецсимволов
    safe_text = text.replace('"', '\\"')
    cmd = f'espeak -v ru -p 10 -s 150 "{safe_text}"'
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка espeak: {e}")
        print(f"[JARVIS] {text}")
