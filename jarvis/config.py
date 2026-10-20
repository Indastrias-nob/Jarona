# Настройки голосового помощника Jarvis

# API ключ для распознавания речи (Google Speech Recognition - бесплатно через веб)
# Альтернатива: Whisper API
GPT_API_KEY = ""

# --- OpenRouter настройки ---
OPENROUTER_API_KEY = ""  # ключ get started на https://openrouter.ai
OPENROUTER_MODEL = "google/gemma-4-31b-it:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# --- Голосовой ответ ---
TTS_ENGINE = "espeak"
TTS_LANGUAGE = "ru"

# --- Режим просыпания ---
WAKE_WORD_ENABLED = True
WAKE_WORD = "jarvis"

# --- Громкость ---
DEFAULT_VOLUME = 0.8

# --- Пути ---
TMP_DIR = "/tmp/jarvis"
PROFILE_PATH = "/tmp/jarvis/user_profile.json"
DIALOGUE_PATH = "/tmp/jarvis/dialogue.json"
MAX_CONTEXT = 10  # макс. число сообщений в контексте

# --- Язык ---
SYSTEM_LANGUAGE = "ru-RU"

# --- Системная подсказка для LLM ---
SYSTEM_PROMPT = (
    "Ты — голосовой помощник Jarvis, работающий на Linux (Fedora). "
    "Пользователь говорит с тобой голосом на русском языке. "
    "Твоя задача — понять намерение пользователя и вернуть краткий JSON-объект "
    "с ключом 'intent' (одна из команд: open_browser, open_terminal, open_app, "
    "create_file, edit_file, format_text, delete_file, volume, screenshot, "
    "window_list, media_control, search_web, answer, voice_input, exit, help), "
    "ключом 'args' (объект с параметрами, либо пустой объект) и ключом 'answer' "
    "(текст ответа, если нужно что-то объяснить). Будь краток. Если команда не ясна, "
    "верни intent 'answer' с вопросом уточнения. "
    "Ответь ТОЛЬКО на русском языке, даже если пользователь говорит по-английски."
)
