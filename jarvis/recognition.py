import os
import time
import logging
import speech_recognition as sr
from config import TMP_DIR, SYSTEM_LANGUAGE

logger = logging.getLogger(__name__)

# Глобальный распознаватель (один экземпляр)
recognizer = sr.Recognizer()
microphone = sr.Microphone()


def setup_audio():
    """Настройка микрофона"""
    with microphone as source:
        logger.info("Настройка уровней аудио...")
        recognizer.adjust_for_ambient_noise(source, duration=1)


def listen_microphone(timeout=5, phrase_time_limit=10):
    """Слушать микрофон один раз"""
    setup_audio()
    try:
        logger.info("Слушаю...")
        audio = recognizer.listen(
            microphone,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit
        )
        return audio
    except sr.WaitTimeoutError:
        logger.debug("Время прослушивания истекло")
        return None
    except sr.UnknownValueError:
        logger.warning("Речь не распознана")
        return None
    except sr.RequestError as e:
        logger.error(f"Ошибка сервиса распознавания: {e}")
        return None


def recognize_command(language: str = SYSTEM_LANGUAGE):
    """Распознать команду с микрофона"""
    audio = listen_microphone()
    if audio is None:
        return None

    try:
        command = recognizer.recognize_google(
            audio,
            language=language
        )
        logger.info(f"Распознано: {command}")
        return command
    except sr.UnknownValueError:
        logger.warning("Речь не распознана (google)")
        return None
    except sr.RequestError as e:
        logger.error(f"Ошибка Google Speech Recognition: {e}")
        return None


def listen_for_wake_word(timeout=5):
    """Слушать слово пробуждения"""
    setup_audio()
    try:
        audio = recognizer.listen(microphone, timeout=timeout)
        word = recognizer.recognize_google(audio, language="ru")
        if WAKE_WORD.lower() in word.lower():
            logger.info(f"Слово пробуждения обнаружено: {WAKE_WORD}")
            return None  # Следующий вызов распознает команду
        return None
    except sr.WaitTimeoutError:
        return None
    except Exception as e:
        logger.error(f"Ошибка проверки пробуждения: {e}")
        return None


def set_wake_word(word: str):
    global WAKE_WORD
    WAKE_WORD = word
