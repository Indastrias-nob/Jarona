#!/usr/bin/env python3
"""Jarvis — голосовой помощник для Linux (Fedora).

Возможности: понимание команд через LLM, управление ПК, голосовой ввод текста,
работа с файлами.

Запуск:
    python jarvis.py            # голосовой режим (слово пробуждения)
    python jarvis.py --no-wake  # слушать команды без слова пробуждения
    python jarvis.py --text     # текстовый режим (без микрофона)
    python jarvis.py --mic 3    # выбрать микрофон по индексу
    python jarvis.py --list-mics
"""

import argparse
import os
import sys

# Позволяем запускать из любого каталога: `python path/to/jarvis.py`
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import logging  # noqa: E402

import config  # noqa: E402
from logging_setup import setup_logging  # noqa: E402

setup_logging()

import context  # noqa: E402
import file_ops  # noqa: E402
import pc_control  # noqa: E402
import recognition  # noqa: E402
import tts  # noqa: E402
import voice_input  # noqa: E402
from llm import check_llm, understand  # noqa: E402
from tts import speak  # noqa: E402

logger = logging.getLogger("jarvis")

BANNER = """
╔════════════════════════════════════════╗
║        🤖  ГОЛОСОВОЙ ПОМОЩНИК JARVIS   ║
║       Управление ПК • Голосовой ввод   ║
╚════════════════════════════════════════╝
 - «джарвис, открой браузер» — команды голосом
 - «напиши в файл ~/rt.py калькулятор» — работа с файлами
 - «слушай»            — голосовой ввод текста в окно
 - «помощь»            — список команд
 - «выход»             — завершение
"""

HELP_TEXT = """Команды Jarvis:
  громкость 50 / громче / тише / выключи звук
  открой firefox / запусти терминал
  найди в интернете <запрос>
  скриншот
  что открыто
  пауза / следующий трек
  создай файл <путь>
  допиши в файл <путь> — записать или дописать текст
  открой файл <путь>
  открой папку <путь>
  удали файл <путь>
  сделай текст заглавными <путь>
  слушай — голосовой ввод текста в активное окно
  очисти историю / помощь / выход
"""


# --------------------------------------------------------------------------- #
# Обработка команд
# --------------------------------------------------------------------------- #
def _confirm(prompt: str) -> bool:
    """Подтверждение действия (да/нет)."""
    if not config.CONFIRM_DELETE:
        return True
    speak(prompt)
    try:
        answer = input(f"{prompt} (да/нет): ").strip().lower()
    except EOFError:
        return False
    return answer in ("да", "д", "yes", "y")


def _say(text: str):
    """Озвучить ответ (speak сам печатает текст в консоль)."""
    if text:
        speak(text)


def handle_text_command(cmd: str):
    """Простые команды без LLM.

    Возвращает True — команда обработана, "exit" — завершить работу,
    False — передать в LLM.
    """
    cmd_lower = cmd.lower().strip()

    if cmd_lower in ("помощь", "команды", "help", "что ты умеешь"):
        print(HELP_TEXT)
        _say("Я умею управлять громкостью, приложениями, файлами и вводом текста.")
        return True

    if cmd_lower.startswith(("выход", "заверши работу", "до свидания")):
        return "exit"

    if cmd_lower.startswith(("слушай", "ввод", "голосовой ввод")):
        # Озвучку выключаем, чтобы микрофон не слышал сам себя
        tts.set_enabled(False)
        try:
            voice_input.voice_input_text()
        finally:
            tts.set_enabled(True)
        return True

    if cmd_lower.startswith("громкость"):
        result = pc_control.set_volume_from_command(cmd_lower)
        if result is not None:
            _say(f"Громкость {result} процентов")
        else:
            _say("Не удалось изменить громкость")
        return True

    if cmd_lower in ("громче", "прибавь", "сделай громче", "прибавь звук"):
        result = pc_control.adjust_volume(config.VOLUME_STEP)
        _say(f"Громкость {result}" if result is not None else "Не удалось изменить громкость")
        return True

    if cmd_lower in ("тише", "убавь", "затиши", "сделай тише", "убавь звук"):
        result = pc_control.adjust_volume(-config.VOLUME_STEP)
        _say(f"Громкость {result}" if result is not None else "Не удалось изменить громкость")
        return True

    if "скриншот" in cmd_lower:
        path = pc_control.take_screenshot()
        _say(f"Скриншот сохранён: {path}" if path else "Не удалось сделать скриншот")
        return True

    if "что открыто" in cmd_lower or cmd_lower in ("окна", "список окон"):
        titles = pc_control.list_open_windows()
        _say(f"Открыто окон: {len(titles)}" if titles else "Список окон недоступен")
        return True

    if cmd_lower.startswith(("пауза", "поставь на паузу", "продолжи", "включи музыку")):
        ok = pc_control.media_control("play_pause")
        _say("Готово" if ok else "Медиаплеер недоступен")
        return True

    if "следующий трек" in cmd_lower:
        ok = pc_control.media_control("next")
        _say("Готово" if ok else "Медиаплеер недоступен")
        return True

    if "предыдущий трек" in cmd_lower:
        ok = pc_control.media_control("prev")
        _say("Готово" if ok else "Медиаплеер недоступен")
        return True

    if cmd_lower in ("очисти историю", "очистить историю", "забудь диалог"):
        context.clear_dialogue()
        _say("История диалога очищена")
        return True

    return False


def handle_llm_result(result: dict) -> bool:
    """Выполнить команду, распознанную LLM."""
    intent = result.get("intent", "answer")
    args = result.get("args") or {}
    answer = result.get("answer", "")

    if intent == "busy":
        _say("Сервис распознавания перегружен, попробуйте через минуту.")
        return True

    if intent == "error":
        _say("Не удалось понять команду: модель вернула неожиданный ответ.")
        logger.error("Детали: %s", answer)
        if not config.OPENROUTER_API_KEY:
            print("Подсказка: задайте OPENROUTER_API_KEY, например:")
            print("  export OPENROUTER_API_KEY=sk-or-...")
        return True

    if intent == "exit":
        return False

    if intent == "help":
        print(HELP_TEXT)
        _say(answer or "Смотрите список команд в консоли")
        return True

    if intent == "answer":
        _say(answer or "Не понял команду.")
        return True

    if intent == "volume":
        if args.get("mute"):
            pc_control.mute(True)
        elif args.get("volume") is not None:
            pc_control.set_volume(int(args["volume"]))
        elif args.get("delta") is not None:
            pc_control.adjust_volume(int(args["delta"]))
        _say(answer or "Громкость изменена")
        return True

    if intent in ("open_browser", "open_terminal", "open_app"):
        target = {
            "open_browser": "браузер",
            "open_terminal": "терминал",
        }.get(intent) or args.get("app") or args.get("name")
        if not target:
            _say("Не указано, что открыть")
            return True
        if target.startswith(("http://", "https://", "www.")):
            ok = pc_control.open_url(target)
        else:
            ok = pc_control.launch_app(target)
        _say(answer or (f"Открываю {target}" if ok else f"Не удалось найти {target}"))
        return True

    if intent == "search_web":
        query = args.get("query") or args.get("text")
        ok = pc_control.search_web(query) if query else None
        _say(answer or (f"Ищу: {query}" if ok else "Не удалось открыть поиск"))
        return True

    if intent in ("create_file", "write_file", "read_file", "open_file",
                  "open_folder", "delete_file", "format_text"):
        path = args.get("path")
        if not path:
            _say("Не указан путь к файлу")
            return True
        if intent == "create_file":
            ok = file_ops.create_file(path, args.get("content", ""))
            _say(f"Файл создан: {ok}" if ok else
                 f"Файл {path} уже существует — скажите «допиши в файл», "
                 "чтобы изменить его")
        elif intent == "write_file":
            ok = file_ops.write_file(
                path, args.get("content", ""), append=bool(args.get("append"))
            )
            _say(f"Записано в {ok}" if ok else "Не удалось записать файл")
        elif intent == "read_file":
            text = file_ops.read_file(path)
            if text is None:
                _say("Не удалось прочитать файл")
            else:
                print(f"📄 {path}:\n{text}")
                _say(answer or f"Файл содержит {len(text)} символов")
        elif intent == "open_folder":
            ok = pc_control.open_folder(path)
            _say(answer or (f"Открываю папку {ok}" if ok else "Папка не найдена"))
        elif intent == "open_file":
            ok = file_ops.open_file(path)
            _say(f"Открываю {path}" if ok else "Файл не найден")
        elif intent == "delete_file":
            if not _confirm(f"Удалить файл {path}?"):
                _say("Отменено")
                return True
            ok = file_ops.delete_file(path)
            _say(f"Файл удалён: {path}" if ok else "Не удалось удалить файл")
        else:
            ok = file_ops.format_text_file(path, args.get("action", "upper"))
            _say("Готово" if ok else "Не удалось изменить текст")
        return True

    if intent == "screenshot":
        path = pc_control.take_screenshot()
        _say(f"Скриншот сохранён: {path}" if path else "Не удалось сделать скриншот")
        return True

    if intent == "window_list":
        titles = pc_control.list_open_windows()
        _say(f"Открыто окон: {len(titles)}" if titles else "Список окон недоступен")
        return True

    if intent == "media_control":
        ok = pc_control.media_control(args.get("action", "play_pause"))
        _say("Готово" if ok else "Медиаплеер недоступен")
        return True

    if intent == "voice_input":
        tts.set_enabled(False)
        try:
            voice_input.voice_input_text()
        finally:
            tts.set_enabled(True)
        return True

    logger.info("Неизвестный intent: %s", intent)
    _say("Команда не распознана. Скажите «помощь».")
    return True


def process_command(cmd: str) -> bool:
    """Обработать команду. Возвращает False, если пора завершить работу."""
    cmd = (cmd or "").strip()
    if not cmd:
        return True

    context.append_message("user", cmd)

    handled = handle_text_command(cmd)
    if handled == "exit":
        return False
    if handled:
        return True

    if not config.USE_LLM:
        _say("Команда не распознана. Скажите «помощь».")
        return True

    result = understand(cmd, context.get_context())
    keep_running = handle_llm_result(result)
    answer = result.get("answer") or result.get("intent", "")
    context.append_message("assistant", answer)
    return keep_running


# --------------------------------------------------------------------------- #
# Основной цикл
# --------------------------------------------------------------------------- #
def get_command(wake_mode: bool):
    """Получить следующую команду (голосом)."""
    if not wake_mode:
        return recognition.recognize_command()

    remainder = recognition.listen_for_wake_word()
    if remainder is None:
        return None
    if remainder:
        return remainder

    # Сказали только «Джарвис» — слушаем саму команду
    _say("Слушаю")
    return recognition.recognize_command()


def main(argv=None, tts_enabled=True) -> int:
    parser = argparse.ArgumentParser(description="Голосовой помощник Jarvis")
    parser.add_argument("--text", action="store_true", help="текстовый режим ввода")
    parser.add_argument("--no-wake", action="store_true",
                        help="не требовать слово пробуждения")
    parser.add_argument("--no-tts", action="store_true", help="не озвучивать ответы")
    parser.add_argument("--mic", help="микрофон: индекс или часть имени")
    parser.add_argument("--list-mics", action="store_true",
                        help="показать доступные микрофоны и выйти")
    parser.add_argument("--check-llm", action="store_true",
                        help="проверить доступность OpenRouter и выйти")
    parser.add_argument("--verbose", "-v", action="store_true", help="подробный лог")
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.list_mics:
        for i, name in enumerate(recognition.list_microphones()):
            print(f"{i}: {name}")
        return 0

    if args.check_llm:
        ok, message = check_llm()
        print(("✅ " if ok else "❌ ") + message)
        return 0 if ok else 1

    if args.no_tts:
        tts_enabled = False
    if not tts_enabled:
        tts.set_enabled(False)

    if args.mic:
        recognition.set_microphone(args.mic)

    os.makedirs(config.TMP_DIR, exist_ok=True)
    os.makedirs(config.DATA_DIR, exist_ok=True)
    print(BANNER)

    if not config.OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY не задан — сложные команды работать не будут.\n")

    wake_mode = config.WAKE_WORD_ENABLED and not args.no_wake and not args.text

    try:
        while True:
            if args.text:
                try:
                    command = input("👉 Вы: ")
                except EOFError:
                    break
            else:
                command = get_command(wake_mode)

            if not command:
                continue

            if not args.text:  # в текстовом режиме строку уже напечатал input()
                print(f"👉 Вы: {command}")
            if not process_command(command):
                break
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    except Exception:
        logger.exception("Непредвиденная ошибка")
        _say("Произошла ошибка. Подробности в логе.")
        return 1

    _say("До свидания.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
