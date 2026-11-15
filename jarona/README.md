# Jarona 0.1.0

**Голосовой помощник для Orange Pi 4 Pro на DietPi с удалённым управлением Windows ПК**

Jarona — двухрежимный голосовой ассистент на русском языке:
- **Автономный режим**: работа на Orange Pi без интернета (локальное распознавание речи, управление GPIO, датчиками)
- **Удалённый режим**: управление Windows ПК через сеть (файлы, приложения, системные функции)

## Возможности

### Автономный режим (Orange Pi)
- Локальное распознавание речи через Vosk (без Google API)
- Управление GPIO пинами
- Управление подключёнными устройствами
- Простые команды без интернета
- Синтез речи через espeak-ng

### Удалённый режим (Windows ПК)
- Управление файлами и папками
- Запуск приложений
- Управление громкостью и медиа
- Скриншоты
- Голосовой ввод текста
- Поиск в интернете

## Архитектура

```
Orange Pi (DietPi)           Windows ПК
┌─────────────────┐          ┌──────────────┐
│  FastAPI Server │◄────────►│    Client    │
│  • Vosk (STT)   │ WebSocket│  • Контроль  │
│  • espeak (TTS) │   или    │  • Действия  │
│  • GPIO         │   REST   │  • Ответы    │
│  • LLM Router   │          │              │
└─────────────────┘          └──────────────┘
```

## Быстрый старт

### Orange Pi (сервер)
```bash
# Установка зависимостей DietPi
cd jarona/server
bash setup-dietpi.sh

# Настройка
export OPENROUTER_API_KEY=sk-or-...
export JARONA_MODE=server  # server | standalone

# Запуск
python3 main.py
```

### Windows (клиент)
```bash
# Установка
cd jarona/client
pip install -r requirements.txt

# Настройка
# Укажите IP Orange Pi в config.py
JARONA_SERVER_IP = "192.168.1.100"

# Запуск
python client.py
```

## Структура проекта

```
jarona/
├── server/              # Код для Orange Pi
│   ├── main.py         # FastAPI сервер
│   ├── config.py       # Конфигурация сервера
│   ├── recognition.py  # Vosk распознавание
│   ├── tts.py         # Синтез речи
│   ├── llm.py         # OpenRouter клиент
│   ├── gpio_control.py # GPIO управление
│   ├── local_commands.py # Автономные команды
│   ├── api/           # REST/WebSocket API
│   │   ├── routes.py
│   │   └── websocket.py
│   └── models/        # Pydantic модели
├── client/            # Код для Windows
│   ├── client.py     # Главный клиент
│   ├── windows_control.py # Windows API
│   └── config.py     # Конфигурация клиента
├── shared/           # Общий код
│   ├── protocol.py   # Протокол команд
│   └── models.py     # Общие модели данных
├── requirements-server.txt  # Зависимости Pi
├── requirements-client.txt  # Зависимости Windows
└── setup-dietpi.sh   # Скрипт установки
```

## Требования

### Orange Pi 4 Pro
- DietPi (Debian-based)
- Python 3.9+
- Микрофон USB или I2S
- Динамик/наушники

### Windows ПК
- Windows 10/11
- Python 3.9+
- Сетевое подключение к Orange Pi

## Конфигурация

### Переменные окружения

```bash
# Общие
OPENROUTER_API_KEY=sk-or-...      # API ключ OpenRouter
JARONA_MODE=server                # server | standalone | client

# Сервер (Orange Pi)
JARONA_HOST=0.0.0.0              # IP для прослушивания
JARONA_PORT=8080                  # Порт сервера
JARONA_MIC_DEVICE=0               # Индекс микрофона

# Клиент (Windows)
JARONA_SERVER_IP=192.168.1.100    # IP Orange Pi
JARONA_SERVER_PORT=8080
```

## API Протокол

### WebSocket (real-time)
```
ws://orangepi:8080/ws
```

### REST API
```
POST /api/command
{
  "text": "открой браузер",
  "target": "windows",
  "mode": "voice"
}
```

## Команды

### Автономные (без интернета)
- `громкость 50` / `громче` / `тише`
- `включи пин 17` / `выключи пин 17`
- `статус gpio`

### Удалённые (Windows ПК)
- `открой браузер` / `запусти <приложение>`
- `создай файл <путь>`
- `напиши в файл <путь> <содержимое>`
- `скриншот`
- `найди в интернете <запрос>`
- `слушай` — голосовой ввод текста

## Безопасность

- Аутентификация по токену
- Шифрование трафика (TLS опционально)
- Ограничение файловых операций
- Подтверждение удаления файлов

## Разработка

### Запуск тестов
```bash
# Сервер
cd jarona/server
python -m pytest tests/

# Клиент
cd jarona/client
python -m pytest tests/
```

## История версий

- **0.1.0** — первый релиз, базовая функциональность

## Лицензия

MIT

## Автор

Проект основан на Jarvis voice assistant, переработанный для Orange Pi 4 Pro.
