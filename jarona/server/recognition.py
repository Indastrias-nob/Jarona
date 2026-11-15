"""Модуль распознавания речи через Vosk для Orange Pi."""

import json
import logging
import queue
import sys
from typing import Optional

try:
    import sounddevice as sd
    from vosk import KaldiRecognizer, Model
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Установите зависимости: pip install vosk sounddevice")
    sys.exit(1)

from config import (
    CALIBRATION_SECONDS,
    LISTEN_TIMEOUT,
    MIC_DEVICE,
    PHRASE_TIME_LIMIT,
    VOSK_MODEL_PATH,
    VOSK_SAMPLE_RATE,
    WAKE_WORD_ALIASES,
)

logger = logging.getLogger(__name__)

# Глобальные объекты
_model: Optional[Model] = None
_recognizer: Optional[KaldiRecognizer] = None
_mic_device: Optional[int] = None


def init_vosk_model():
    """Инициализировать модель Vosk (вызывается один раз при старте)."""
    global _model, _recognizer

    if _model is not None:
        return _model

    logger.info(f"Загрузка модели Vosk: {VOSK_MODEL_PATH}")
    try:
        _model = Model(VOSK_MODEL_PATH)
        _recognizer = KaldiRecognizer(_model, VOSK_SAMPLE_RATE)
        _recognizer.SetWords(True)
        logger.info("Модель Vosk загружена успешно")
        return _model
    except Exception as e:
        logger.error(f"Не удалось загрузить модель Vosk: {e}")
        raise


def get_mic_device() -> Optional[int]:
    """Определить индекс микрофона."""
    global _mic_device

    if _mic_device is not None:
        return _mic_device

    if not MIC_DEVICE or MIC_DEVICE == "":
        logger.info("Используется микрофон по умолчанию")
        _mic_device = None
        return None

    # Попытка разобрать как индекс
    if MIC_DEVICE.isdigit():
        _mic_device = int(MIC_DEVICE)
        logger.info(f"Выбран микрофон по индексу: {_mic_device}")
        return _mic_device

    # Поиск по части имени
    devices = sd.query_devices()
    mic_lower = MIC_DEVICE.lower()
    for idx, dev in enumerate(devices):
        if mic_lower in dev['name'].lower() and dev['max_input_channels'] > 0:
            _mic_device = idx
            logger.info(f"Микрофон найден: {dev['name']} (индекс {idx})")
            return _mic_device

    logger.warning(f"Микрофон '{MIC_DEVICE}' не найден, используется устройство по умолчанию")
    _mic_device = None
    return None


def list_microphones() -> list:
    """Список доступных микрофонов."""
    devices = sd.query_devices()
    mics = []
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            mics.append({"index": idx, "name": dev['name']})
    return mics


def recognize_from_microphone(timeout: int = LISTEN_TIMEOUT) -> Optional[str]:
    """Распознать речь с микрофона через Vosk.

    Returns:
        Распознанный текст или None при тишине/ошибке.
    """
    init_vosk_model()
    mic_device = get_mic_device()

    audio_queue = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            logger.debug(f"sounddevice status: {status}")
        audio_queue.put(bytes(indata))

    recognizer = KaldiRecognizer(_model, VOSK_SAMPLE_RATE)
    recognizer.SetWords(True)

    logger.info("Слушаю...")

    try:
        with sd.RawInputStream(
            samplerate=VOSK_SAMPLE_RATE,
            blocksize=4000,
            device=mic_device,
            dtype='int16',
            channels=1,
            callback=callback,
        ):
            import time
            start_time = time.time()

            while True:
                # Проверка таймаута
                if time.time() - start_time > timeout:
                    logger.debug("Таймаут ожидания речи")
                    break

                try:
                    data = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        logger.info(f"Распознано: {text}")
                        return text
                else:
                    # Частичный результат (для отладки)
                    partial = json.loads(recognizer.PartialResult())
                    if partial.get('partial'):
                        logger.debug(f"Частично: {partial['partial']}")

            # Финальный результат
            result = json.loads(recognizer.FinalResult())
            text = result.get('text', '').strip()
            if text:
                logger.info(f"Распознано (final): {text}")
                return text

    except Exception as e:
        logger.error(f"Ошибка распознавания: {e}")

    return None


def extract_wake_word(text: str) -> Optional[str]:
    """Найти слово пробуждения в тексте и вернуть команду после него.

    Returns:
        Команда после слова пробуждения или None, если слова нет.
    """
    if not text:
        return None

    text_lower = text.lower().strip()

    for wake_word in WAKE_WORD_ALIASES:
        # Ищем слово целиком в начале
        if text_lower.startswith(wake_word):
            # Команда — всё после слова пробуждения
            command = text[len(wake_word):].strip(" ,.!?")
            if command:
                logger.info(f"Слово пробуждения найдено: '{wake_word}', команда: '{command}'")
                return command
            # Если после слова нет команды — ждём следующую фразу
            logger.debug(f"Слово пробуждения '{wake_word}' без команды")
            return ""

    return None


def listen_with_wake_word(wake_word_enabled: bool = True) -> Optional[str]:
    """Слушать с учётом слова пробуждения.

    Returns:
        Команда пользователя или None.
    """
    if not wake_word_enabled:
        # Режим без слова пробуждения
        return recognize_from_microphone()

    # Режим со словом пробуждения
    while True:
        text = recognize_from_microphone()
        if not text:
            continue

        command = extract_wake_word(text)
        if command is not None:
            if command == "":
                # Слово найдено, но команды нет — слушаем ещё раз
                logger.info("Слушаю команду...")
                next_text = recognize_from_microphone(timeout=10)
                return next_text if next_text else None
            return command

        logger.debug(f"Слово пробуждения не найдено в: '{text}'")


if __name__ == "__main__":
    # Тест модуля
    logging.basicConfig(level=logging.DEBUG)

    print("Доступные микрофоны:")
    for mic in list_microphones():
        print(f"  [{mic['index']}] {mic['name']}")

    print("\nИнициализация модели Vosk...")
    init_vosk_model()

    print("\nГоворите после слова 'Жарона'...")
    while True:
        command = listen_with_wake_word(wake_word_enabled=True)
        if command:
            print(f"✓ Команда: {command}")
            if "выход" in command.lower():
                break
