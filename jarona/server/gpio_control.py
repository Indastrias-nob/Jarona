"""Управление GPIO на Orange Pi через gpiod или lgpio."""

import logging
from typing import Dict, Optional

from config import GPIO_ENABLED, GPIO_LIBRARY

logger = logging.getLogger(__name__)

_gpio_chip = None
_gpio_lines: Dict[int, any] = {}


class GPIOError(RuntimeError):
    """Ошибка работы с GPIO."""


def init_gpio():
    """Инициализировать GPIO библиотеку."""
    global _gpio_chip

    if not GPIO_ENABLED:
        logger.info("GPIO отключён в конфигурации")
        return False

    if _gpio_chip is not None:
        return True

    try:
        if GPIO_LIBRARY == "gpiod":
            import gpiod
            _gpio_chip = gpiod.Chip('gpiochip0')
            logger.info("GPIO инициализирован через gpiod")
            return True
        elif GPIO_LIBRARY == "lgpio":
            import lgpio
            _gpio_chip = lgpio.gpiochip_open(0)
            logger.info("GPIO инициализирован через lgpio")
            return True
        else:
            logger.error(f"Неизвестная GPIO библиотека: {GPIO_LIBRARY}")
            return False
    except ImportError as e:
        logger.error(f"GPIO библиотека не установлена: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка инициализации GPIO: {e}")
        return False


def gpio_set(pin: int, value: int) -> bool:
    """Установить значение пина (0 или 1).

    Args:
        pin: номер GPIO пина (1-40)
        value: 0 (LOW) или 1 (HIGH)

    Returns:
        True при успехе
    """
    if not init_gpio():
        raise GPIOError("GPIO не инициализирован")

    if not (1 <= pin <= 40):
        raise GPIOError(f"Неверный номер пина: {pin} (должен быть 1-40)")

    if value not in (0, 1):
        raise GPIOError(f"Неверное значение: {value} (должно быть 0 или 1)")

    try:
        if GPIO_LIBRARY == "gpiod":
            import gpiod

            # Освобождаем старую линию
            if pin in _gpio_lines:
                _gpio_lines[pin].release()

            line = _gpio_chip.get_line(pin)
            line.request(consumer="jarona", type=gpiod.LINE_REQ_DIR_OUT)
            line.set_value(value)

            _gpio_lines[pin] = line
            logger.info(f"GPIO {pin} установлен в {value}")
            return True

        elif GPIO_LIBRARY == "lgpio":
            import lgpio

            lgpio.gpio_claim_output(_gpio_chip, pin)
            lgpio.gpio_write(_gpio_chip, pin, value)

            logger.info(f"GPIO {pin} установлен в {value}")
            return True

    except Exception as e:
        raise GPIOError(f"Ошибка записи GPIO {pin}: {e}")


def gpio_get(pin: int) -> int:
    """Прочитать значение пина.

    Args:
        pin: номер GPIO пина (1-40)

    Returns:
        0 или 1
    """
    if not init_gpio():
        raise GPIOError("GPIO не инициализирован")

    if not (1 <= pin <= 40):
        raise GPIOError(f"Неверный номер пина: {pin}")

    try:
        if GPIO_LIBRARY == "gpiod":
            import gpiod

            if pin in _gpio_lines:
                _gpio_lines[pin].release()

            line = _gpio_chip.get_line(pin)
            line.request(consumer="jarona", type=gpiod.LINE_REQ_DIR_IN)
            value = line.get_value()

            _gpio_lines[pin] = line
            logger.info(f"GPIO {pin} прочитан: {value}")
            return value

        elif GPIO_LIBRARY == "lgpio":
            import lgpio

            lgpio.gpio_claim_input(_gpio_chip, pin)
            value = lgpio.gpio_read(_gpio_chip, pin)

            logger.info(f"GPIO {pin} прочитан: {value}")
            return value

    except Exception as e:
        raise GPIOError(f"Ошибка чтения GPIO {pin}: {e}")


def gpio_pwm(pin: int, value: int) -> bool:
    """Установить PWM на пине (0-100%).

    Args:
        pin: номер GPIO пина
        value: значение PWM 0-100

    Returns:
        True при успехе
    """
    if not init_gpio():
        raise GPIOError("GPIO не инициализирован")

    if not (1 <= pin <= 40):
        raise GPIOError(f"Неверный номер пина: {pin}")

    if not (0 <= value <= 100):
        raise GPIOError(f"Неверное значение PWM: {value} (должно быть 0-100)")

    # TODO: Реализовать PWM через sysfs или hardware PWM
    logger.warning("PWM пока не реализован, используется обычный set")
    return gpio_set(pin, 1 if value > 50 else 0)


def gpio_cleanup():
    """Освободить все GPIO линии."""
    global _gpio_lines, _gpio_chip

    if GPIO_LIBRARY == "gpiod":
        for line in _gpio_lines.values():
            try:
                line.release()
            except:
                pass
        _gpio_lines.clear()
    elif GPIO_LIBRARY == "lgpio" and _gpio_chip is not None:
        try:
            import lgpio
            lgpio.gpiochip_close(_gpio_chip)
        except:
            pass
        _gpio_chip = None

    logger.info("GPIO очищен")


def get_gpio_status() -> Dict:
    """Получить статус GPIO системы."""
    return {
        "enabled": GPIO_ENABLED,
        "library": GPIO_LIBRARY if GPIO_ENABLED else None,
        "initialized": _gpio_chip is not None,
        "active_pins": list(_gpio_lines.keys()) if GPIO_LIBRARY == "gpiod" else [],
    }


if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.DEBUG)

    print("Тест GPIO...")

    status = get_gpio_status()
    print(f"Статус: {status}")

    if not status["enabled"]:
        print("GPIO отключён в конфигурации")
        exit(0)

    # Тест мигания LED на пине 17
    TEST_PIN = 17
    print(f"\nМигание LED на пине {TEST_PIN} (3 раза)")

    try:
        for i in range(3):
            print(f"  {i+1}. Включаю...")
            gpio_set(TEST_PIN, 1)
            time.sleep(0.5)

            print(f"  {i+1}. Выключаю...")
            gpio_set(TEST_PIN, 0)
            time.sleep(0.5)

        print("✓ Тест завершён")
    except GPIOError as e:
        print(f"✗ Ошибка: {e}")
    finally:
        gpio_cleanup()
