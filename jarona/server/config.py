"""Конфигурация сервера Jarona для Orange Pi 4 Pro на DietPi."""

import os
from pathlib import Path

# --- Основные настройки ---
VERSION = "0.1.0"
APP_NAME = "Jarona"

# Режим работы: server | standalone
MODE = os.environ.get("JARONA_MODE", "server")

# --- Сеть ---
HOST = os.environ.get("JARONA_HOST", "0.0.0.0")
PORT = int(os.environ.get("JARONA_PORT", "8080"))

# --- Безопасность ---
# Токен авторизации для клиентов (пустой = без авторизации)
AUTH_TOKEN = os.environ.get("JARONA_AUTH_TOKEN", "")
# Разрешённые IP адреса клиентов (пусто = все разрешены)
ALLOWED_IPS = os.environ.get("JARONA_ALLOWED_IPS", "").split(",") if os.environ.get("JARONA_ALLOWED_IPS") else []

# --- OpenRouter (LLM) ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-haiku-5.5")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_TIMEOUT = 30
LLM_MAX_TOKENS = 1200
LLM_MAX_RETRIES = 2
LLM_BACKOFF_BASE = 1.5

# Резервные модели при недоступности основной
OPENROUTER_FALLBACK_MODELS = [
    "minimax/minimax-m3.1-flash:free",
    "poolside/laguna-s-2.1:free",
]

# --- Распознавание речи ---
# Vosk модель для русского языка
VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "/opt/jarona/models/vosk-model-ru")
# Скачать: https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
VOSK_SAMPLE_RATE = 16000
SYSTEM_LANGUAGE = "ru-RU"

# Микрофон
MIC_DEVICE = os.environ.get("JARONA_MIC_DEVICE", "")  # индекс или часть имени
LISTEN_TIMEOUT = 5
PHRASE_TIME_LIMIT = 10
CALIBRATION_SECONDS = 0.8

# --- Синтез речи ---
TTS_ENGINE = os.environ.get("JARONA_TTS", "espeak")  # espeak | gtts | disabled
TTS_LANGUAGE = "ru"
TTS_RATE = 150
TTS_PITCH = 40

# --- Слово пробуждения ---
WAKE_WORD_ENABLED = True
WAKE_WORD = "jarona"
WAKE_WORD_ALIASES = (
    "jarona", "жарона", "джарона", "жаронa",
    "джарвис", "jarvis",  # обратная совместимость
)

# --- GPIO ---
GPIO_ENABLED = os.environ.get("JARONA_GPIO", "true").lower() == "true"
# Библиотека: gpiod (современная) или lgpio (fallback)
GPIO_LIBRARY = os.environ.get("JARONA_GPIO_LIB", "gpiod")

# --- Пути ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("JARONA_DATA_DIR", "/var/lib/jarona"))
LOG_DIR = DATA_DIR / "logs"
TMP_DIR = Path(os.environ.get("JARONA_TMP", "/tmp/jarona"))

# Создаём каталоги
for directory in [DATA_DIR, LOG_DIR, TMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

LOG_PATH = LOG_DIR / "jarona.log"
PROFILE_PATH = DATA_DIR / "user_profile.json"
DIALOGUE_PATH = DATA_DIR / "dialogue.json"
MAX_CONTEXT = 10  # макс. сообщений в контексте LLM

# --- Безопасность файловых операций ---
# Файловые операции разрешены только в этих каталогах
ALLOWED_FILE_ROOTS = [
    str(DATA_DIR / "files"),
    "/home",  # для удалённого управления Windows
]
CONFIRM_DELETE = True

# --- Системная подсказка LLM ---
SYSTEM_PROMPT = """Ты — голосовой помощник Jarona, работающий на Orange Pi.
Ты управляешь как локальной системой (Orange Pi, GPIO), так и удалённым Windows ПК.

Пользователь даёт команду голосом на русском языке. Определи намерение и верни JSON:
{"intent": "<команда>", "args": {...}, "answer": "<краткий ответ>", "target": "<local|windows|auto>"}

Доступные intent:
  LOCAL (Orange Pi):
    gpio_set       args: {"pin": <1-40>, "value": <0|1>}
    gpio_get       args: {"pin": <1-40>}
    gpio_pwm       args: {"pin": <1-40>, "value": <0-100>}

  WINDOWS (удалённый ПК):
    open_app       args: {"app": "<имя>"}
    open_browser   args: {}
    open_terminal  args: {}
    create_file    args: {"path": "<путь>", "content": "<содержимое>"}
    write_file     args: {"path": "<путь>", "content": "<содержимое>", "append": <bool>}
    read_file      args: {"path": "<путь>"}
    open_file      args: {"path": "<путь>"}
    open_folder    args: {"path": "<путь>"}
    delete_file    args: {"path": "<путь>"}
    format_text    args: {"action": "<upper|lower|title>", "path": "<путь>"}
    volume         args: {"volume": <0-100>} или {"delta": <число>} или {"mute": true}
    screenshot     args: {}
    window_list    args: {}
    media_control  args: {"action": "<play_pause|next|prev|stop>"}
    search_web     args: {"query": "<запрос>"}
    voice_input    args: {}

  ОБЩИЕ:
    answer         args: {} — просто ответь на вопрос
    help           args: {}
    exit           args: {}

Поле target: "local" (Orange Pi), "windows" (Windows ПК), "auto" (определи сам).
Ответ — ТОЛЬКО JSON, без markdown и пояснений.
"""

# --- Логирование ---
LOG_LEVEL = os.environ.get("JARONA_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
