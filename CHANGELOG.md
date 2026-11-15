# Jarona 0.1.0 — Changelog

## [0.1.0] - 2024-11-15

### Added — Новая функциональность

#### Архитектура
- 🏗️ **Клиент-серверная архитектура** — сервер на Orange Pi, клиент на Windows
- 🌐 **FastAPI сервер** с REST API и WebSocket
- 🔌 **WebSocket** для real-time связи между Orange Pi и Windows
- 🤖 **Автономный режим** (standalone) — работа без Windows клиента

#### Распознавание речи
- 🎤 **Vosk** — локальное распознавание без интернета (замена Google SR)
- 🔊 **Новое слово пробуждения**: "Жарона" (+ обратная совместимость с "Jarvis")
- 📦 **sounddevice** вместо PyAudio (лучшая совместимость с ARM)

#### GPIO управление (новое)
- ⚡ **GPIO control** через gpiod/lgpio
- 📌 **Команды GPIO**: включи/выключи пин, чтение пина
- 🔧 **PWM поддержка** (базовая реализация)

#### Windows клиент (новое)
- 💻 **Удалённое управление Windows** — все команды Jarvis теперь работают с Windows ПК
- 🎮 **WinAPI интеграция** — громкость через pycaw
- 📸 **Скриншоты** через Pillow
- 📁 **Файловые операции** на Windows

#### Документация
- 📖 **Полная документация** — README, ARCHITECTURE, MIGRATION, QUICKSTART
- 🤝 **CONTRIBUTING.md** — руководство для контрибьюторов
- 📜 **LICENSE** — MIT лицензия
- 🚀 **setup-dietpi.sh** — автоматическая установка на DietPi

### Changed — Изменения

#### Платформа
- **Fedora Linux x86_64** → **DietPi ARM64** (Orange Pi 4 Pro)
- **Монолитное приложение** → **Клиент-сервер**
- **Wayland/X11** → **Универсальное решение**

#### Зависимости
- **PyAudio** → **sounddevice**
- **Google Speech Recognition** → **Vosk**
- Добавлено: **FastAPI**, **uvicorn**, **websockets**, **pycaw**, **lgpio**
- Удалено: **ydotool**, **wl-clipboard**, **xdotool** (специфично для Linux desktop)

#### Конфигурация
- Переменные окружения: `JARVIS_*` → `JARONA_*`
- Новые параметры: `JARONA_MODE`, `JARONA_HOST`, `JARONA_PORT`, `VOSK_MODEL_PATH`
- Пути данных: `~/.local/share/jarvis` → `/var/lib/jarona`

### Preserved — Сохранённая функциональность

Весь функционал из Jarvis 0.x.x сохранён:

- ✅ **Файловые операции**: создание, запись, чтение, удаление, форматирование
- ✅ **Управление приложениями**: запуск, открытие браузера/терминала
- ✅ **Громкость**: установка, увеличение/уменьшение, mute
- ✅ **Скриншоты**
- ✅ **Поиск в интернете**
- ✅ **Медиа контроль**: play/pause/next/prev
- ✅ **LLM диспетчеризация**: OpenRouter с fallback моделями
- ✅ **Безопасность**: ограничение файловых операций, подтверждение удаления
- ✅ **Устойчивость LLM**: retry, backoff, терпимый парсинг JSON

### Removed — Удалено

- ❌ **Google Speech Recognition** (заменён на Vosk)
- ❌ **PyAudio** (заменён на sounddevice)
- ❌ **voice_input.py** (голосовой ввод текста — планируется в 0.2.0)
- ❌ **context.py** и **profile.py** (упрощено, планируется вернуть в 0.2.0)

### Technical Details

**Языки и фреймворки:**
- Python 3.9+
- FastAPI 0.104+
- Vosk 0.3.45+
- Pydantic 2.5+ для валидации

**Архитектура:**
```
Server (Orange Pi):
  - FastAPI + uvicorn
  - Vosk (STT)
  - OpenRouter (LLM)
  - gpiod/lgpio (GPIO)
  - espeak-ng (TTS)

Client (Windows):
  - WebSocket client
  - pycaw (volume)
  - pywin32 (WinAPI)
  - Pillow (screenshots)
```

**Строки кода:**
- Python: ~1500 строк
- Документация: ~1500 строк
- Всего файлов: 25

### Breaking Changes — Несовместимые изменения

1. **Название проекта**: Jarvis → Jarona
2. **Платформа**: требуется Orange Pi 4 Pro (или совместимая ARM плата)
3. **Конфигурация**: все переменные окружения переименованы
4. **Пути данных**: изменено расположение файлов
5. **API**: новый протокол команд (JSON over WebSocket/REST)

### Migration — Миграция

См. полную инструкцию: `jarona/docs/MIGRATION.md`

Кратко:
```bash
# 1. Сохранить данные Jarvis
cp -r ~/.local/share/jarvis ~/jarvis-backup

# 2. Установить Jarona на Orange Pi
git clone https://github.com/ВАШЕ_ИМЯ/Jarona.git
cd Jarona/jarona
sudo bash setup-dietpi.sh

# 3. Настроить
sudo nano /opt/jarona/.env
# Добавить OPENROUTER_API_KEY

# 4. Запустить
sudo systemctl start jarona
```

### Known Issues — Известные проблемы

- PWM реализован частично (используется обычный GPIO set)
- Голосовой ввод текста пока не работает на Windows клиенте
- Media control на Windows требует доработки
- Нет автотестов (планируется в 0.2.0)

### Coming in 0.2.0

- 🧪 Автотесты (pytest)
- 🎤 Голосовой ввод текста для Windows
- ⚙️ PWM полная реализация
- 🏠 Интеграция с Home Assistant
- 🌐 Web UI для управления
- 📱 Mobile app (Android)
- 🇬🇧 Поддержка английского языка

---

**Полный список изменений:** https://github.com/ВАШЕ_ИМЯ/Jarona/compare/master...jarona-v0.1.0
