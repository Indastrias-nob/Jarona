"""
Управление контекстом диалога.
Хранит последнее окно из N сообщений для передачи в LLM.
"""

import os
import json
import logging
from config import DIALOGUE_PATH, TMP_DIR, MAX_CONTEXT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def load_dialogue():
    """Загрузить историю диалога"""
    os.makedirs(TMP_DIR, exist_ok=True)
    if os.path.exists(DIALOGUE_PATH):
        try:
            with open(DIALOGUE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Ошибка загрузки диалога: {e}")
    return []


def save_dialogue(messages: list):
    """Сохранить историю диалога (обрезается до MAX_CONTEXT)"""
    # Обрезаем до окна контекста
    if len(messages) > MAX_CONTEXT:
        messages = messages[-MAX_CONTEXT:]
    try:
        with open(DIALOGUE_PATH, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Ошибка сохранения диалога: {e}")


def append_message(role: str, content: str):
    """Добавить сообщение в диалог"""
    messages = load_dialogue()
    messages.append({"role": role, "content": content})
    save_dialogue(messages)
    return messages


def get_context():
    """Получить системную подсказку + последние сообщения"""
    messages = load_dialogue()
    context = [{"role": "system", "content": SYSTEM_PROMPT}]
    context.extend(messages)
    return context


def clear_dialogue():
    """Очистить историю диалога"""
    save_dialogue([])
    logger.info("Диалог очищен")
