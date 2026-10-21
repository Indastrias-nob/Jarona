# Настройки голосового помощника Jarvis
"""Конфигурация Jarvis.

Значения можно переопределять переменными окружения:
  OPENROUTER_API_KEY, OPENROUTER_MODEL, JARVIS_MIC, JARVIS_DATA_DIR
"""

import os
from pathlib import Path

# --- OpenRouter (понимание команд через LLM) ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get(
    "OPENROUTER_MODEL", "google/gemma-4-31b-it:free"
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_TIMEOUT = 30
LLM_MAX_RETRIES = 1
# Если LLM недоступна, команда считается нераспознанной
USE_LLM = True

# --- Голосовой ответ ---
# auto: espeak-ng -> espeak -> gTTS -> вывод в консоль
TTS_ENGINE = os.environ.get("JARVIS_TTS", "auto")  # auto | espeak | gtts
TTS_LANGUAGE = "ru"
TTS_RATE = 150
TTS_PITCH = 40

# --- Распознавание речи ---
SYSTEM_LANGUAGE = "ru-RU"
LISTEN_TIMEOUT = 5          # сколько ждать начала фразы, сек
PHRASE_TIME_LIMIT = 10      # максимум длительность фразы, сек
CALIBRATION_SECONDS = 0.8   # калибровка шума при старте/смене устройства
MIC_DEVICE = os.environ.get("JARVIS_MIC", "")  # индекс или часть имени

# --- Слово пробуждения ---
WAKE_WORD_ENABLED = True
WAKE_WORD = "jarvis"
# Варианты распознавания (Google часто пишет кириллицей)
WAKE_WORD_ALIASES = (
    "jarvis", "jervis", "jarves",
    "джарвис", "жарвис", "джервис", "джарвіс",
)

# --- Громкость ---
DEFAULT_VOLUME = 0.8
VOLUME_STEP = 10

# --- Пути ---
DATA_DIR = os.path.expanduser(
    os.environ.get("JARVIS_DATA_DIR", "~/.local/share/jarvis")
)
TMP_DIR = os.environ.get("JARVIS_TMP", "/tmp/jarvis")
PROFILE_PATH = os.path.join(DATA_DIR, "user_profile.json")
DIALOGUE_PATH = os.path.join(DATA_DIR, "dialogue.json")
LOG_PATH = os.path.join(DATA_DIR, "jarvis.log")
MAX_CONTEXT = 10  # макс. число сообщений в контексте

# --- Безопасность ---
# Файловые операции (создание/удаление) разрешены только внутри этих каталогов.
# Пустой список = разрешён весь домашний каталог.
ALLOWED_FILE_ROOTS = [os.path.expanduser("~")]
# Удаление подтверждается голосом/вводом, если включено
CONFIRM_DELETE = True

# --- Системная подсказка для LLM ---
SYSTEM_PROMPT = (
    "Ты — голосовой помощник Jarvis на Linux (Fedora) и говоришь по-русски. "
    "Пользователь даёт команду голосом. Определи намерение и верни ТОЛЬКО "
    "JSON-объект без пояснений и markdown в формате:\n"
    '{"intent": "<команда>", "args": {...}, "answer": "<краткий ответ>"}\n'
    "Допустимые intent и args:\n"
    '  open_app       args: {"app": "<имя программы или сайта>"}\n'
    "  open_browser   args: {}\n"
    "  open_terminal  args: {}\n"
    '  create_file    args: {"path": "<путь>", "content": "<содержимое>"}\n'
    '  open_file      args: {"path": "<путь>"}\n'
    '  delete_file    args: {"path": "<путь>"}\n'
    '  format_text    args: {"action": "<upper|lower|title>"}\n'
    '  volume         args: {"volume": <0-100>} или {"delta": <число>} '
    'или {"mute": true}\n'
    "  screenshot     args: {}\n"
    "  window_list    args: {}\n"
    '  media_control  args: {"action": "<play_pause|next|prev|stop>"}\n'
    '  search_web     args: {"query": "<запрос>"}\n'
    "  voice_input    args: {}\n"
    "  help           args: {}\n"
    "  exit           args: {}\n"
    '  answer         args: {} — вопрос или реплика, ответь полем "answer"\n'
    "Все пути — абсолютные, начинающиеся с ~ или /home. "
    "Если намерение неясно — intent answer с уточняющим вопросом. "
    "Ответ всегда на русском языке."
)
