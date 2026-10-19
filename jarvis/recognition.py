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


def recognize_microphone(language: str = SYSTEM_LANGUAGE, use_whisper: bool = False):
    """Распознать команду с микрофона (google или whisper)"""
    audio = listen_microphone()
    if audio is None:
        return None

    if use_whisper:
        return recognize_whisper(audio)
    return recognize_google(audio, language)


def recognize_google(audio, language: str = SYSTEM_LANGUAGE):
    """Google Speech Recognition"""
    try:
        command = recognizer.recognize_google(audio, language=language)
        logger.info(f"Распознано (google): {command}")
        return command
    except sr.UnknownValueError:
        logger.warning("Речь не распознана (google)")
        return None
    except sr.RequestError as e:
        logger.error(f"Ошибка Google Speech Recognition: {e}")
        return None


def recognize_whisper(audio, model: str = "base"):
    """Распознавание через whisper (локально)"""
    try:
        import whisper
        audio_path = os.path.join(TMP_DIR, "recorded.wav")
        with open(audio_path, "wb") as f:
            f.write(audio.get_wav_data())
        result = whisper.load_model(model).transcribe(audio_path, language="ru")
        command = result["text"].strip()
        logger.info(f"Распознано (whisper): {command}")
        return command
    except ImportError:
        logger.warning("whisper не установлен, используем google")
        return None
    except Exception as e:
        logger.error(f"Ошибка whisper: {e}")
        return None


def listen_for_wake_word(timeout=5, use_whisper: bool = False):
    """Слушать слово пробуждения"""
    setup_audio()
    try:
        audio = recognizer.listen(microphone, timeout=timeout)
        word = recognizer.recognize_google(audio, language="ru")
        if word and "jarvis" in word.lower():
            logger.info("Слово пробуждения обнаружено")
            return None
        return None
    except sr.WaitTimeoutError:
        return None
    except Exception as e:
        logger.error(f"Ошибка проверки пробуждения: {e}")
        return None


def set_wake_word(word: str):
    global WAKE_WORD
    WAKE_WORD = word


def recognize_command(language: str = SYSTEM_LANGUAGE, use_whisper: bool = False):
    """Распознать команду с микрофона (google или whisper)"""
    return recognize_microphone(language, use_whisper)


def set_microphone(device_index):
    """Выбрать микрофон по индексу"""
    global microphone
    microphone = sr.Microphone(device_index=device_index)
