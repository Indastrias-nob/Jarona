"""Главный сервер Jarona — FastAPI + WebSocket для удалённого управления."""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

# Добавляем shared в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import config
from gpio_control import gpio_cleanup, gpio_get, gpio_set, init_gpio
from llm import understand
from local_commands import handle_local_command
from recognition import init_vosk_model, listen_with_wake_word
from shared.models import CommandRequest, CommandResponse, SystemStatus
from shared.protocol import CommandStatus as CmdStatus
from shared.protocol import CommandTarget, IntentType
from tts import set_enabled as set_tts_enabled
from tts import speak

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_PATH),
    ],
)

logger = logging.getLogger(__name__)


# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и очистка при старте/остановке."""
    logger.info(f"Запуск {config.APP_NAME} {config.VERSION}")

    # Инициализация
    init_vosk_model()
    init_gpio()

    yield

    # Очистка
    gpio_cleanup()
    logger.info("Сервер остановлен")


app = FastAPI(
    title="Jarona Server",
    description="Голосовой помощник для Orange Pi с управлением Windows ПК",
    version=config.VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: ограничить в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Хранилище подключённых клиентов
connected_clients = {}


# --- REST API ---

@app.get("/")
async def root():
    """Информация о сервере."""
    return {
        "name": config.APP_NAME,
        "version": config.VERSION,
        "mode": config.MODE,
        "status": "running",
    }


@app.get("/status")
async def get_status():
    """Статус системы."""
    import psutil

    return SystemStatus(
        hostname=config.APP_NAME,
        uptime=psutil.boot_time(),
        cpu_percent=psutil.cpu_percent(interval=1),
        memory_percent=psutil.virtual_memory().percent,
        temperature=None,  # TODO: читать температуру SoC
        gpio_available=config.GPIO_ENABLED,
        connected_clients=len(connected_clients),
    )


@app.post("/api/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """Выполнить команду."""
    logger.info(f"Команда: {request.text} (target={request.target})")

    try:
        # Проверяем локальные команды
        handled, response = handle_local_command(request.text)
        if handled:
            if response == "exit":
                return CommandResponse(
                    status=CmdStatus.SUCCESS,
                    intent=IntentType.EXIT,
                    answer="До свидания!",
                )
            return CommandResponse(
                status=CmdStatus.SUCCESS,
                answer=response or "Готово",
            )

        # Обращаемся к LLM
        intent_data = understand(request.text)
        intent = intent_data.get("intent")
        args = intent_data.get("args", {})
        answer = intent_data.get("answer", "")
        target = intent_data.get("target", "auto")

        # Выполняем локальные действия
        if target == "local" or intent.startswith("gpio_"):
            result = await execute_local_intent(intent, args)
            return CommandResponse(
                status=CmdStatus.SUCCESS,
                intent=intent,
                answer=answer or result,
                result={"local": True},
            )

        # Команды для Windows — отправляем клиенту через WebSocket
        # (в REST API просто возвращаем намерение)
        return CommandResponse(
            status=CmdStatus.SUCCESS,
            intent=intent,
            answer=answer,
            result={"args": args, "target": target},
        )

    except Exception as e:
        logger.error(f"Ошибка выполнения команды: {e}")
        return CommandResponse(
            status=CmdStatus.ERROR,
            answer="Не удалось выполнить команду",
            error=str(e),
        )


async def execute_local_intent(intent: str, args: dict) -> str:
    """Выполнить локальное действие."""
    if intent == "gpio_set":
        pin = args.get("pin")
        value = args.get("value")
        gpio_set(pin, value)
        return f"Пин {pin} установлен в {value}"

    elif intent == "gpio_get":
        pin = args.get("pin")
        value = gpio_get(pin)
        return f"Пин {pin} = {value}"

    elif intent == "gpio_pwm":
        # TODO: реализовать PWM
        return "PWM пока не поддерживается"

    else:
        return "Действие не поддерживается локально"


# --- WebSocket ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket для real-time связи с Windows клиентом."""
    await websocket.accept()
    client_id = f"client_{len(connected_clients)}"
    connected_clients[client_id] = {
        "websocket": websocket,
        "connected_at": datetime.now(),
    }

    logger.info(f"Клиент подключён: {client_id}")

    try:
        await websocket.send_json({
            "type": "connected",
            "client_id": client_id,
            "server_version": config.VERSION,
        })

        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "command":
                # Клиент отправил команду
                text = data.get("text", "")
                logger.info(f"Команда от {client_id}: {text}")

                # Обрабатываем
                handled, response = handle_local_command(text)
                if handled:
                    await websocket.send_json({
                        "type": "response",
                        "status": "success",
                        "answer": response,
                    })
                else:
                    # LLM
                    try:
                        intent_data = understand(text)
                        await websocket.send_json({
                            "type": "intent",
                            "data": intent_data,
                        })
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "error": str(e),
                        })

            elif msg_type == "result":
                # Результат выполнения на клиенте
                logger.info(f"Результат от {client_id}: {data.get('status')}")
                # Озвучиваем ответ
                answer = data.get("answer", "")
                if answer:
                    speak(answer)

    except WebSocketDisconnect:
        logger.info(f"Клиент отключён: {client_id}")
    finally:
        del connected_clients[client_id]


# --- Standalone режим ---

async def standalone_mode():
    """Автономный режим — работа без Windows клиента."""
    logger.info("Режим standalone — голосовое управление Orange Pi")
    speak("Жарона запущена в автономном режиме")

    while True:
        try:
            # Слушаем команду
            command = listen_with_wake_word(wake_word_enabled=config.WAKE_WORD_ENABLED)
            if not command:
                continue

            logger.info(f"Команда: {command}")

            # Обрабатываем локально
            handled, response = handle_local_command(command)
            if handled:
                if response == "exit":
                    speak("До свидания!")
                    break
                speak(response)
                continue

            # LLM
            try:
                intent_data = understand(command)
                answer = intent_data.get("answer", "")
                intent = intent_data.get("intent")
                args = intent_data.get("args", {})

                # Выполняем локальные действия
                if intent.startswith("gpio_"):
                    result = await execute_local_intent(intent, args)
                    speak(answer or result)
                else:
                    speak(answer or "Эта команда доступна только с подключённым Windows ПК")

            except Exception as e:
                logger.error(f"Ошибка: {e}")
                speak("Не удалось выполнить команду")

        except KeyboardInterrupt:
            logger.info("Завершение по Ctrl+C")
            break
        except Exception as e:
            logger.error(f"Ошибка: {e}")


# --- Entry point ---

if __name__ == "__main__":
    import uvicorn

    if config.MODE == "standalone":
        # Автономный режим
        import asyncio
        asyncio.run(standalone_mode())
    else:
        # Серверный режим
        logger.info(f"Запуск сервера на {config.HOST}:{config.PORT}")
        uvicorn.run(
            app,
            host=config.HOST,
            port=config.PORT,
            log_level=config.LOG_LEVEL.lower(),
        )
