# Миграция с Jarvis на Jarona 0.1.0

## Что изменилось

### Название проекта
**Jarvis** → **Jarona** (новое имя для избежания конфликтов с торговыми марками)

### Архитектура

#### Было (Jarvis):
- Монолитное приложение для Linux (Fedora)
- Google Speech Recognition (облачное)
- Управление только локальной системой
- Wayland/X11 специфичные зависимости

#### Стало (Jarona):
- **Клиент-серверная архитектура**
- **Сервер** на Orange Pi 4 Pro (DietPi, ARM64)
- **Клиент** на Windows ПК
- Vosk (локальное распознавание, без Google API)
- WebSocket/REST API для удалённого управления
- Кросс-платформенность

### Технологические изменения

| Компонент | Jarvis | Jarona |
|---|---|---|
| **Платформа** | Fedora Linux x86_64 | DietPi ARM64 (Orange Pi) + Windows |
| **Распознавание речи** | Google SR (облако) | Vosk (локальное) |
| **Архитектура** | Монолит | Клиент-сервер |
| **Управление** | Только локальная система | Локальная + удалённая Windows |
| **GPIO** | Нет | Да (gpiod/lgpio) |
| **Зависимости** | PyAudio, ydotool, wl-clipboard | sounddevice, FastAPI, WebSocket |
| **Слово пробуждения** | "Jarvis" | "Jarona" (+ обратная совместимость) |

## Сохранённый функционал

Весь функционал из Jarvis перенесён в Jarona:

✅ **Файловые операции**: создание, запись, чтение, удаление
✅ **Управление приложениями**: запуск, открытие браузера/терминала
✅ **Громкость**: установка, увеличение/уменьшение, mute
✅ **Скриншоты**
✅ **Поиск в интернете**
✅ **Голосовой ввод текста** (на Windows через clipboard)
✅ **Медиа контроль**: play/pause/next/prev
✅ **LLM диспетчеризация**: OpenRouter
✅ **Безопасность**: ограничение файловых операций, подтверждение удаления
✅ **Устойчивость LLM**: retry, fallback модели, терпимый парсинг JSON

## Новый функционал

🆕 **GPIO управление**: включение/выключение пинов, PWM
🆕 **Удалённое управление Windows** через WebSocket
🆕 **Автономный режим**: работа без интернета (локальные команды)
🆕 **REST API**: программный доступ к помощнику
🆕 **Кросс-платформенность**: сервер на ARM, клиент на Windows
🆕 **FastAPI**: современный веб-фреймворк с автодокументацией

## Структура файлов

### Jarvis (старая)
```
jarvis/
├── jarvis.py
├── config.py
├── recognition.py
├── llm.py
├── pc_control.py
├── file_ops.py
├── voice_input.py
├── tts.py
├── context.py
└── profile.py
```

### Jarona (новая)
```
jarona/
├── server/              # Код для Orange Pi
│   ├── main.py
│   ├── config.py
│   ├── recognition.py   # Vosk вместо Google SR
│   ├── llm.py          # сохранён из Jarvis
│   ├── gpio_control.py # новый
│   ├── local_commands.py # новый
│   └── tts.py          # адаптирован
├── client/              # Код для Windows (новый)
│   ├── client.py
│   ├── windows_control.py
│   └── config.py
├── shared/              # Общие модули (новый)
│   ├── protocol.py
│   └── models.py
└── docs/
```

## Миграция конфигурации

### Переменные окружения

| Jarvis | Jarona | Комментарий |
|---|---|---|
| `OPENROUTER_API_KEY` | `OPENROUTER_API_KEY` | Без изменений |
| `OPENROUTER_MODEL` | `OPENROUTER_MODEL` | Без изменений |
| `JARVIS_MIC` | `JARONA_MIC_DEVICE` | Переименовано |
| `JARVIS_DATA_DIR` | `JARONA_DATA_DIR` | Переименовано |
| `JARVIS_TTS` | `JARONA_TTS` | Переименовано |
| — | `JARONA_MODE` | **Новое**: server / standalone |
| — | `JARONA_HOST` | **Новое**: 0.0.0.0 |
| — | `JARONA_PORT` | **Новое**: 8080 |
| — | `JARONA_GPIO` | **Новое**: true/false |
| — | `VOSK_MODEL_PATH` | **Новое**: /opt/jarona/models/vosk-model-ru |

### Пример .env

**Jarvis:**
```bash
OPENROUTER_API_KEY=sk-or-...
JARVIS_MIC=0
JARVIS_TTS=espeak
```

**Jarona (сервер):**
```bash
OPENROUTER_API_KEY=sk-or-...
JARONA_MODE=server
JARONA_MIC_DEVICE=0
JARONA_TTS=espeak
VOSK_MODEL_PATH=/opt/jarona/models/vosk-model-ru
JARONA_GPIO=true
```

**Jarona (клиент):**
```bash
JARONA_SERVER_IP=192.168.1.100
JARONA_SERVER_PORT=8080
```

## Миграция данных

### Пути

| Jarvis | Jarona |
|---|---|
| `~/.local/share/jarvis/` | `/var/lib/jarona/` (сервер) |
| `~/.local/share/jarvis/jarvis.log` | `/var/lib/jarona/logs/jarona.log` |
| `~/.local/share/jarvis/dialogue.json` | `/var/lib/jarona/dialogue.json` |
| `~/.local/share/jarvis/user_profile.json` | `/var/lib/jarona/user_profile.json` |

### Перенос истории диалога

```bash
# На старой системе
cp ~/.local/share/jarvis/dialogue.json ~/jarvis_backup_dialogue.json

# На Orange Pi
scp jarvis_backup_dialogue.json orangepi:/var/lib/jarona/dialogue.json
```

## Удаление Jarvis

После успешной миграции на Jarona:

```bash
# Удалить код
rm -rf ~/new11/jarvis

# Удалить данные (опционально, сделайте резервную копию!)
# rm -rf ~/.local/share/jarvis

# Удалить зависимости (если больше не нужны)
pip uninstall SpeechRecognition pyaudio
```

## Обратная совместимость

### Слово пробуждения

Jarona поддерживает оба варианта:
- "Jarona" / "Жарона" (новое)
- "Jarvis" / "Джарвис" (старое)

### LLM System Prompt

Промпт обновлён с учётом новых возможностей (GPIO, target: local/windows), но старые intent сохранены.

## Тестирование после миграции

### 1. Проверка сервера
```bash
cd /opt/jarona
source venv/bin/activate
python server/main.py
```

### 2. Проверка LLM
```bash
python server/llm.py
```

### 3. Проверка GPIO
```bash
python server/gpio_control.py
```

### 4. Проверка клиента
```powershell
# На Windows
python client/client.py
```

### 5. Интеграционный тест

**На Orange Pi (через микрофон):**
```
"Жарона, включи пин 17"  → GPIO должен сработать
```

**На Orange Pi (для Windows):**
```
"Жарона, открой браузер"  → Должен открыться на Windows ПК
```

## Откат

Если миграция не удалась:

1. Jarvis остался в ветке `master`
2. Jarona находится в ветке `jarona-v0.1.0`

```bash
git checkout master
cd jarvis
python jarvis.py
```

## Проблемы и решения

### Vosk не распознаёт речь
- Проверьте микрофон: `arecord -l`
- Проверьте модель: `/opt/jarona/models/vosk-model-ru` должна существовать
- Увеличьте громкость: `alsamixer`

### WebSocket не подключается
- Проверьте firewall: `sudo ufw allow 8080`
- Проверьте IP: `ip addr show`
- Проверьте сервер: `systemctl status jarona`

### GPIO не работает
- Проверьте права: `ls -l /dev/gpiochip0`
- Установите lgpio: `pip install lgpio`
- Запускайте с sudo (или настройте udev rules)

## Дополнительная информация

- Архитектура: `docs/ARCHITECTURE.md`
- README: `jarona/README.md`
- Настройка: `/opt/jarona/.env`
