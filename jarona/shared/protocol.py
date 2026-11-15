"""Протокол команд Jarona — общий формат обмена между сервером и клиентом."""

from enum import Enum
from typing import Any, Optional


class CommandTarget(str, Enum):
    """Где выполняется команда."""
    LOCAL = "local"      # На Orange Pi (GPIO, локальные команды)
    WINDOWS = "windows"  # На Windows ПК
    AUTO = "auto"        # Автоматически определить


class CommandStatus(str, Enum):
    """Статус выполнения команды."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class IntentType(str, Enum):
    """Типы намерений (действий)."""
    # Файловые операции
    CREATE_FILE = "create_file"
    WRITE_FILE = "write_file"
    READ_FILE = "read_file"
    OPEN_FILE = "open_file"
    DELETE_FILE = "delete_file"
    OPEN_FOLDER = "open_folder"
    FORMAT_TEXT = "format_text"

    # Управление приложениями
    OPEN_APP = "open_app"
    OPEN_BROWSER = "open_browser"
    OPEN_TERMINAL = "open_terminal"
    CLOSE_APP = "close_app"

    # Система
    VOLUME = "volume"
    SCREENSHOT = "screenshot"
    WINDOW_LIST = "window_list"
    MEDIA_CONTROL = "media_control"

    # GPIO (только Orange Pi)
    GPIO_SET = "gpio_set"
    GPIO_GET = "gpio_get"
    GPIO_PWM = "gpio_pwm"

    # Прочее
    SEARCH_WEB = "search_web"
    VOICE_INPUT = "voice_input"
    ANSWER = "answer"
    HELP = "help"
    EXIT = "exit"


# Версия протокола
PROTOCOL_VERSION = "0.1.0"
