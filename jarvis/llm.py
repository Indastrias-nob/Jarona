"""
Модуль для вызова LLM через OpenRouter.
Понимает намерение пользователя (intent) из распознанного текста.
"""

import os
import json
import logging
import requests
from config import (
    OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL, SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


def ask_llm(context: list) -> dict:
    """
    Отправить контекст в OpenRouter и получить ответ в формате JSON.
    Возвращает dict с intent, args, answer.
    """
    if not OPENROUTER_API_KEY:
        logger.warning("API ключ OpenRouter не задан — используем заглушку")
        return {"intent": "answer", "args": {}, "answer": "API ключ не настроен."}

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jarvis",
        "X-Title": "Jarvis Assistant",
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": context,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        # LLM может вернуть текст с markdown, пробуем извлечь JSON
        cleaned = content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"Ошибка вызова LLM: {e}")
        return {"intent": "answer", "args": {}, "answer": f"Ошибка LLM: {e}"}


def understand(text: str) -> dict:
    """
    Распознать намерение по тексту.
    Добавляет сообщение пользователя в контекст, вызывает LLM.
    """
    ctx = [{"role": "user", "content": text}]
    result = ask_llm(ctx)
    return result
