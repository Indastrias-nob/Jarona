# Настройки голосового помощника Jarvis

# API ключ для распознавания речи (Google Speech Recognition - бесплатно через веб)
# Альтернатива: Whisper API
GPT_API_KEY = ""

# Голосовой ответ ( tts_engine: 'gtts' или 'espeak' )
TTS_ENGINE = "espeak"
TTS_LANGUAGE = "ru"

# Режим просыпания: True - ждать слова пробуждения, False - всегда слушает
WAKE_WORD_ENABLED = True
WAKE_WORD = "jarvis"

# Громкость по умолчанию
DEFAULT_VOLUME = 0.8

# Каталог для временных файлов (распознавание, синтез)
TMP_DIR = "/tmp/jarvis"

# Язык системы
SYSTEM_LANGUAGE = "ru-RU"
