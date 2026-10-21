"""Управление контекстом диалога: последние N сообщений для LLM."""

import json
import logging
import os

from config import DATA_DIR, DIALOGUE_PATH, MAX_CONTEXT

logger = logging.getLogger(__name__)


def load_dialogue() -> list:
    """Загрузить историю диалога."""
    if not os.path.exists(DIALOGUE_PATH):
        return []
    try:
        with open(DIALOGUE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Ошибка загрузки диалога: %s", e)
        return []


def save_dialogue(messages: list):
    """Сохранить историю диалога (не более MAX_CONTEXT сообщений)."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DIALOGUE_PATH, "w", encoding="utf-8") as f:
            json.dump(messages[-MAX_CONTEXT:], f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error("Ошибка сохранения диалога: %s", e)


def append_message(role: str, content: str) -> list:
    """Добавить сообщение в историю."""
    messages = load_dialogue()
    messages.append({"role": role, "content": content})
    messages = messages[-MAX_CONTEXT:]
    save_dialogue(messages)
    return messages


def get_context() -> list:
    """Последние сообщения диалога (без системной подсказки)."""
    return load_dialogue()


def clear_dialogue():
    """Очистить историю диалога."""
    save_dialogue([])
    logger.info("Диалог очищен")
