"""Windows клиент Jarona — подключается к Orange Pi серверу."""

import asyncio
import logging
import sys
from pathlib import Path

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

# Добавляем shared в путь
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

import config
from shared.protocol import IntentType
from windows_control import (
    create_file,
    delete_file,
    media_control,
    mute,
    open_app,
    open_browser,
    open_file,
    open_folder,
    open_terminal,
    read_file,
    screenshot,
    search_web,
    set_volume,
    volume_down,
    volume_up,
    write_file,
)

# Логирование
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE),
    ],
)

logger = logging.getLogger(__name__)


class JaronaClient:
    """Клиент для подключения к Jarona серверу."""

    def __init__(self):
        self.websocket = None
        self.running = False

    async def connect(self):
        """Подключиться к серверу."""
        logger.info(f"Подключение к {config.WS_URL}")

        try:
            async with websockets.connect(config.WS_URL) as websocket:
                self.websocket = websocket
                self.running = True

                # Приветствие
                welcome = await websocket.recv()
                logger.info(f"Подключено: {welcome}")

                # Основной цикл
                await self.message_loop()

        except ConnectionRefusedError:
            logger.error("Не удалось подключиться к серверу")
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")

    async def message_loop(self):
        """Обработка сообщений от сервера."""
        try:
            while self.running:
                message = await self.websocket.recv()
                await self.handle_message(message)

        except (ConnectionClosedOK, ConnectionClosedError):
            logger.info("Соединение закрыто")
            self.running = False
        except Exception as e:
            logger.error(f"Ошибка в цикле сообщений: {e}")
            self.running = False

    async def handle_message(self, message):
        """Обработать сообщение от сервера."""
        import json

        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "intent":
                # Сервер распознал намерение — выполняем
                intent_data = data.get("data", {})
                await self.execute_intent(intent_data)

            elif msg_type == "response":
                # Простой ответ
                answer = data.get("answer", "")
                logger.info(f"Ответ сервера: {answer}")

            elif msg_type == "pong":
                pass  # Keepalive

            elif msg_type == "error":
                error = data.get("error", "")
                logger.error(f"Ошибка сервера: {error}")

        except json.JSONDecodeError:
            logger.error(f"Невалидный JSON: {message}")

    async def execute_intent(self, intent_data: dict):
        """Выполнить намерение на Windows."""
        intent = intent_data.get("intent")
        args = intent_data.get("args", {})
        answer = intent_data.get("answer", "")

        logger.info(f"Выполнение: {intent} {args}")

        success = False
        result_msg = answer

        try:
            # Файловые операции
            if intent == IntentType.CREATE_FILE:
                success = create_file(args["path"], args.get("content", ""))
                result_msg = f"Файл создан: {args['path']}"

            elif intent == IntentType.WRITE_FILE:
                success = write_file(
                    args["path"],
                    args.get("content", ""),
                    args.get("append", False)
                )
                result_msg = f"Файл записан: {args['path']}"

            elif intent == IntentType.READ_FILE:
                content = read_file(args["path"])
                if content:
                    result_msg = f"Файл прочитан ({len(content)} символов)"
                    success = True

            elif intent == IntentType.OPEN_FILE:
                success = open_file(args["path"])
                result_msg = f"Файл открыт: {args['path']}"

            elif intent == IntentType.OPEN_FOLDER:
                success = open_folder(args["path"])
                result_msg = f"Папка открыта: {args['path']}"

            elif intent == IntentType.DELETE_FILE:
                if config.CONFIRM_DELETE:
                    confirm = input(f"Удалить {args['path']}? (y/n): ")
                    if confirm.lower() != 'y':
                        result_msg = "Отменено"
                        success = True
                        await self.send_result("cancelled", result_msg)
                        return

                success = delete_file(args["path"])
                result_msg = f"Файл удалён: {args['path']}"

            # Приложения
            elif intent == IntentType.OPEN_APP:
                success = open_app(args["app"])
                result_msg = f"Запущено: {args['app']}"

            elif intent == IntentType.OPEN_BROWSER:
                success = open_browser()
                result_msg = "Браузер открыт"

            elif intent == IntentType.OPEN_TERMINAL:
                success = open_terminal()
                result_msg = "Терминал открыт"

            # Громкость
            elif intent == IntentType.VOLUME:
                if "volume" in args:
                    success = set_volume(args["volume"])
                    result_msg = f"Громкость: {args['volume']}%"
                elif "delta" in args:
                    delta = args["delta"]
                    if delta > 0:
                        success = volume_up(delta)
                    else:
                        success = volume_down(-delta)
                    result_msg = f"Громкость {'увеличена' if delta > 0 else 'уменьшена'}"
                elif args.get("mute"):
                    success = mute()
                    result_msg = "Звук выключен"

            # Прочее
            elif intent == IntentType.SCREENSHOT:
                path = screenshot()
                success = path is not None
                result_msg = f"Скриншот: {path}" if success else "Ошибка скриншота"

            elif intent == IntentType.SEARCH_WEB:
                success = search_web(args["query"])
                result_msg = f"Поиск: {args['query']}"

            elif intent == IntentType.MEDIA_CONTROL:
                success = media_control(args["action"])
                result_msg = f"Медиа: {args['action']}"

            else:
                result_msg = f"Намерение {intent} не поддерживается клиентом"
                success = False

        except Exception as e:
            logger.error(f"Ошибка выполнения {intent}: {e}")
            result_msg = f"Ошибка: {e}"
            success = False

        # Отправляем результат обратно
        await self.send_result("success" if success else "error", result_msg)

    async def send_result(self, status: str, answer: str):
        """Отправить результат выполнения на сервер."""
        await self.websocket.send(json.dumps({
            "type": "result",
            "status": status,
            "answer": answer,
        }))

    async def send_command(self, text: str):
        """Отправить команду на сервер (для тестирования)."""
        await self.websocket.send(json.dumps({
            "type": "command",
            "text": text,
        }))

    def stop(self):
        """Остановить клиент."""
        self.running = False


async def main():
    """Главная функция."""
    import json

    client = JaronaClient()

    print(f"""
╔════════════════════════════════════════╗
║     JARONA WINDOWS CLIENT v0.1.0       ║
║   Подключение к Orange Pi серверу      ║
╚════════════════════════════════════════╝

Сервер: {config.SERVER_IP}:{config.SERVER_PORT}
Логи:   {config.LOG_FILE}

Подключение...
""")

    try:
        await client.connect()
    except KeyboardInterrupt:
        logger.info("Завершение по Ctrl+C")
        client.stop()


if __name__ == "__main__":
    asyncio.run(main())
