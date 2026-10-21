"""Распознавание речи: микрофон, Google Speech Recognition, локальный Whisper."""

import logging
import os
import re
from difflib import SequenceMatcher

import speech_recognition as sr

from config import (
    CALIBRATION_SECONDS,
    LISTEN_TIMEOUT,
    MIC_DEVICE,
    PHRASE_TIME_LIMIT,
    SYSTEM_LANGUAGE,
    TMP_DIR,
    WAKE_WORD,
    WAKE_WORD_ALIASES,
)

logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True

_microphone = None
_calibrated = False
_whisper_model = None
_whisper_model_name = "base"


# --------------------------------------------------------------------------- #
# Микрофон
# --------------------------------------------------------------------------- #
def _device_index_from_spec(spec) -> int | None:
    """Найти индекс устройства по номеру или части имени."""
    if spec is None or spec == "":
        return None
    if isinstance(spec, int):
        return spec
    text = str(spec).strip()
    if text.isdigit():
        return int(text)
    names = sr.Microphone.list_microphone_names()
    lowered = text.lower()
    for index, name in enumerate(names):
        if lowered in name.lower():
            logger.info("Микрофон выбран по имени: %s (индекс %d)", name, index)
            return index
    logger.warning("Микрофон «%s» не найден, используется устройство по умолчанию", text)
    return None


def get_microphone():
    """Текущий источник звука (создаётся один раз)."""
    global _microphone
    if _microphone is None:
        index = _device_index_from_spec(MIC_DEVICE)
        _microphone = sr.Microphone(device_index=index)
    return _microphone


def set_microphone(device_spec):
    """Выбрать микрофон по индексу или части имени."""
    global _microphone, _calibrated
    _microphone = sr.Microphone(device_index=_device_index_from_spec(device_spec))
    _calibrated = False
    return _microphone


def list_microphones() -> list[str]:
    """Список доступных устройств записи."""
    return sr.Microphone.list_microphone_names()


def calibrate(source, force: bool = False):
    """Один раз откалибровать порог шума для устройства."""
    global _calibrated
    if _calibrated and not force:
        return
    logger.info("Калибровка уровня шума...")
    recognizer.adjust_for_ambient_noise(source, duration=CALIBRATION_SECONDS)
    _calibrated = True
    logger.info("Порог энергии: %.0f", recognizer.energy_threshold)


# --------------------------------------------------------------------------- #
# Запись
# --------------------------------------------------------------------------- #
def listen_microphone(
    timeout: float = LISTEN_TIMEOUT, phrase_time_limit: float = PHRASE_TIME_LIMIT
):
    """Записать одну фразу. Возвращает AudioData или None."""
    source = get_microphone()
    try:
        with source as audio_source:
            calibrate(audio_source)
            logger.debug("Слушаю...")
            return recognizer.listen(
                audio_source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
    except sr.WaitTimeoutError:
        logger.debug("Фраза не началась за %.1f с", timeout)
        return None
    except (OSError, sr.RequestError) as e:
        logger.error("Ошибка микрофона: %s", e)
        return None


# --------------------------------------------------------------------------- #
# Распознавание
# --------------------------------------------------------------------------- #
def recognize_google(audio, language: str = SYSTEM_LANGUAGE):
    """Google Speech Recognition (требуется интернет)."""
    try:
        command = recognizer.recognize_google(audio, language=language)
        logger.info("Распознано (google): %s", command)
        return command
    except sr.UnknownValueError:
        logger.debug("Речь не распознана (google)")
        return None
    except sr.RequestError as e:
        logger.error("Ошибка Google Speech Recognition: %s", e)
        return None


def _get_whisper_model(name: str = _whisper_model_name):
    """Загрузить и закэшировать модель Whisper."""
    global _whisper_model, _whisper_model_name
    if _whisper_model is None or name != _whisper_model_name:
        import whisper

        _whisper_model = whisper.load_model(name)
        _whisper_model_name = name
        logger.info("Модель Whisper загружена: %s", name)
    return _whisper_model


def recognize_whisper(audio, model: str = _whisper_model_name):
    """Распознавание локально через Whisper (если установлен)."""
    try:
        import whisper  # noqa: F401  # проверка наличия
    except ImportError:
        logger.warning("whisper не установлен — используем Google")
        return None

    audio_path = os.path.join(TMP_DIR, "recorded.wav")
    try:
        os.makedirs(TMP_DIR, exist_ok=True)
        with open(audio_path, "wb") as f:
            f.write(audio.get_wav_data())
        result = _get_whisper_model(model).transcribe(audio_path, language="ru")
        command = result.get("text", "").strip()
        logger.info("Распознано (whisper): %s", command)
        return command or None
    except Exception as e:
        logger.error("Ошибка whisper: %s", e)
        return None


def recognize_audio(audio, language: str = SYSTEM_LANGUAGE, use_whisper: bool = False):
    """Распознать записанный фрагмент."""
    if audio is None:
        return None
    if use_whisper:
        text = recognize_whisper(audio)
        if text:
            return text
    return recognize_google(audio, language)


def listen_once(language: str = SYSTEM_LANGUAGE, use_whisper: bool = False):
    """Записать и распознать одну фразу."""
    return recognize_audio(listen_microphone(), language, use_whisper)


def recognize_command(language: str = SYSTEM_LANGUAGE, use_whisper: bool = False):
    """Распознать команду с микрофона."""
    return listen_once(language, use_whisper)


# --------------------------------------------------------------------------- #
# Слово пробуждения
# --------------------------------------------------------------------------- #
def _normalize(text: str) -> str:
    """Привести текст к виду для сравнения: нижний регистр, без пунктуации."""
    return re.sub(r"[^\wёЁа-яА-Я]+", " ", text.lower()).strip()


def _words_match(a: str, b: str, threshold: float = 0.78) -> bool:
    return SequenceMatcher(None, a, b).ratio() >= threshold


def find_wake_word(text: str) -> tuple[bool, str]:
    """Найти слово пробуждения в тексте.

    Возвращает (найдено, остаток текста после слова).
    """
    if not text:
        return False, ""
    aliases = {WAKE_WORD.lower(), *[a.lower() for a in WAKE_WORD_ALIASES]}
    words = _normalize(text).split()
    for i, word in enumerate(words):
        if word in aliases or any(_words_match(word, alias) for alias in aliases):
            return True, " ".join(words[i + 1 :]).strip()
    return False, ""


def listen_for_wake_word(use_whisper: bool = False):
    """Ждать слово пробуждения.

    Возвращает:
      None — слово не найдено (или фраза не распознана);
      ""   — слово найдено, но команды после него не было;
      str  — текст команды, сказанной сразу после слова.
    """
    text = listen_once(use_whisper=use_whisper)
    if not text:
        return None
    found, remainder = find_wake_word(text)
    if not found:
        logger.debug("Слово пробуждения не найдено в: %s", text)
        return None
    logger.info("Слово пробуждения обнаружено")
    return remainder


def set_wake_word(word: str):
    global WAKE_WORD
    WAKE_WORD = word
