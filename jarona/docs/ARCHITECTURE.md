# Архитектура Jarona 0.1.0

## Обзор

Jarona — двухрежимный голосовой помощник:
- **Сервер** работает на Orange Pi 4 Pro (DietPi)
- **Клиент** работает на Windows ПК
- Связь через **WebSocket** (real-time) или **REST API**

## Компоненты

### Сервер (Orange Pi)

```
┌─────────────────────────────────────┐
│         FastAPI Server              │
│  (main.py, uvicorn)                 │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┬──────────┬────────┐
    │             │          │        │
┌───▼───┐  ┌─────▼─────┐  ┌─▼──┐  ┌─▼──┐
│ Vosk  │  │ OpenRouter│  │GPIO│  │TTS │
│ (STT) │  │   (LLM)   │  │    │  │    │
└───────┘  └───────────┘  └────┘  └────┘
```

**Модули:**
- `main.py` — FastAPI сервер + WebSocket + standalone режим
- `recognition.py` — распознавание речи через Vosk
- `llm.py` — понимание команд через OpenRouter
- `gpio_control.py` — управление GPIO пинами
- `local_commands.py` — простые команды без LLM
- `tts.py` — синтез речи через espeak-ng

### Клиент (Windows)

```
┌─────────────────────────────────────┐
│      WebSocket Client               │
│  (client.py)                        │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┬──────────┬────────┐
    │             │          │        │
┌───▼──────┐  ┌──▼──────┐  ┌─▼──────┐
│ WinAPI   │  │  Files  │  │ Apps   │
│ (volume) │  │         │  │        │
└──────────┘  └─────────┘  └────────┘
```

**Модули:**
- `client.py` — WebSocket клиент
- `windows_control.py` — управление Windows через WinAPI
- `config.py` — конфигурация клиента

### Shared

Общие модули для сервера и клиента:
- `protocol.py` — протокол команд (enum'ы, константы)
- `models.py` — Pydantic модели для валидации

## Поток данных

### 1. Голосовая команда на Orange Pi

```
Микрофон → Vosk → "включи пин 17"
                     ↓
              local_commands.py
                     ↓
              gpio_control.py → GPIO
                     ↓
                  espeak-ng → "Пин 17 включён"
```

### 2. Удалённая команда для Windows

```
Микрофон → Vosk → "открой браузер"
                     ↓
                  llm.py (OpenRouter)
                     ↓
              {"intent": "open_browser", "target": "windows"}
                     ↓
              WebSocket → Windows Client
                     ↓
              windows_control.py → WinAPI
                     ↓
              WebSocket ← "Браузер открыт"
                     ↓
              espeak-ng → "Браузер открыт"
```

### 3. REST API (альтернатива WebSocket)

```
HTTP POST /api/command
{
  "text": "громкость 50",
  "target": "windows"
}
    ↓
llm.py → intent
    ↓
HTTP 200 {"intent": "volume", "args": {"volume": 50}}
```

## Режимы работы

### Server mode (по умолчанию)

Orange Pi слушает на `0.0.0.0:8080`, ждёт подключения Windows клиента через WebSocket.

```bash
export JARONA_MODE=server
python server/main.py
```

### Standalone mode

Orange Pi работает автономно, без Windows клиента. Все команды выполняются локально.

```bash
export JARONA_MODE=standalone
python server/main.py
```

## Безопасность

1. **Авторизация** (опционально)
   - Токен в `JARONA_AUTH_TOKEN`
   - Клиент отправляет токен при подключении

2. **Файловые операции**
   - Ограничены `ALLOWED_FILE_ROOTS`
   - Подтверждение удаления (`CONFIRM_DELETE`)

3. **GPIO**
   - Только пины 1-40
   - Валидация значений (0/1, PWM 0-100)

4. **Сеть**
   - Белый список IP (`ALLOWED_IPS`)
   - CORS настроен для production

## Расширение

### Добавление нового intent

1. Добавить enum в `shared/protocol.py`:
```python
class IntentType(str, Enum):
    MY_ACTION = "my_action"
```

2. Обновить `SYSTEM_PROMPT` в `server/config.py`

3. Добавить обработку:
   - Для локальных: `server/local_commands.py`
   - Для Windows: `client/windows_control.py` + `client/client.py`

### Добавление GPIO устройства

```python
# server/gpio_control.py
def control_relay(state: bool):
    gpio_set(RELAY_PIN, 1 if state else 0)
```

### Новый LLM провайдер

Заменить `llm.py` на свою реализацию с тем же интерфейсом:
```python
def understand(command: str, context: list) -> dict:
    # Ваша LLM логика
    return {"intent": "...", "args": {...}, "answer": "..."}
```

## Производительность

- **Vosk**: ~100-200ms задержка распознавания (зависит от модели)
- **LLM**: ~1-3s (зависит от модели и сети)
- **GPIO**: <1ms
- **WebSocket**: <50ms задержка сети (локальная сеть)

## Отладка

### Логи сервера
```bash
journalctl -u jarona -f
tail -f /var/lib/jarona/logs/jarona.log
```

### Логи клиента
```
%USERPROFILE%\jarona-client.log
```

### Тестирование без голоса
```bash
# Сервер: текстовый режим
cd server
python main.py --text

# Клиент: отправка команды напрямую
python -c "import asyncio; from client import JaronaClient; ..."
```
