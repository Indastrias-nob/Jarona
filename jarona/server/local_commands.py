"""Автономные команды Jarona — работают без интернета и LLM."""

import logging
import re
from typing import Optional, Tuple

from gpio_control import gpio_get, gpio_set, get_gpio_status

logger = logging.getLogger(__name__)


def handle_local_command(text: str) -> Tuple[bool, Optional[str]]:
    """Обработать простую команду без LLM.

    Returns:
        (handled, response) — True если команда обработана
    """
    text_lower = text.lower().strip()

    # GPIO команды
    if match := re.match(r"включи пин (\d+)", text_lower):
        pin = int(match.group(1))
        try:
            gpio_set(pin, 1)
            return True, f"Пин {pin} включён"
        except Exception as e:
            return True, f"Ошибка: {e}"

    if match := re.match(r"выключи пин (\d+)", text_lower):
        pin = int(match.group(1))
        try:
            gpio_set(pin, 0)
            return True, f"Пин {pin} выключен"
        except Exception as e:
            return True, f"Ошибка: {e}"

    if match := re.match(r"прочитай пин (\d+)", text_lower):
        pin = int(match.group(1))
        try:
            value = gpio_get(pin)
            return True, f"Пин {pin} = {value}"
        except Exception as e:
            return True, f"Ошибка: {e}"

    if text_lower in ("статус gpio", "gpio статус"):
        status = get_gpio_status()
        if status["enabled"]:
            msg = f"GPIO активен ({status['library']})"
            if status["active_pins"]:
                msg += f", пины: {status['active_pins']}"
        else:
            msg = "GPIO отключён"
        return True, msg

    # Служебные команды
    if text_lower in ("помощь", "help", "справка"):
        return True, HELP_TEXT

    if text_lower in ("выход", "exit", "стоп"):
        return True, "exit"

    # Команда не распознана
    return False, None


HELP_TEXT = """Команды Jarona:

Локальные (Orange Pi):
  включи пин 17 / выключи пин 17
  прочитай пин 17
  статус gpio

Удалённые (Windows ПК):
  открой <приложение> / запусти <программу>
  громкость 50 / громче / тише
  создай файл <путь>
  напиши в файл <путь> <текст>
  скриншот
  найди в интернете <запрос>
  слушай — голосовой ввод

Общие:
  помощь / выход
"""
