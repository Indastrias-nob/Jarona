"""Диалог с LLM через OpenRouter: определение намерения команды."""

import json
import logging
import re
import time

import requests

from config import (
    LLM_MAX_RETRIES,
    LLM_TIMEOUT,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_URL,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "open_app", "open_browser", "open_terminal", "create_file", "open_file",
    "delete_file", "format_text", "volume", "screenshot", "window_list",
    "media_control", "search_web", "voice_input", "answer", "exit", "help",
}


class LLMError(RuntimeError):
    """LLM недоступна или вернула невалидный ответ."""


def extract_json(content: str) -> dict:
    """Извлечь JSON-объект из ответа модели (в т.ч. из markdown-блока)."""
    if not content:
        raise LLMError("Пустой ответ LLM")
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    # Найти первый { ... } с корректным JSON
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            elif ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise LLMError(f"Не удалось разобрать JSON из ответа LLM: {content[:200]}")


def normalize_result(data: dict) -> dict:
    """Привести ответ LLM к предсказуемому виду."""
    if not isinstance(data, dict):
        return {"intent": "answer", "args": {}, "answer": str(data)}
    intent = str(data.get("intent", "answer")).strip().lower()
    if intent not in VALID_INTENTS:
        logger.warning("LLM вернула неизвестный intent: %s", intent)
        intent = "answer"
    args = data.get("args") or {}
    if not isinstance(args, dict):
        args = {}
    answer = data.get("answer") or ""
    return {"intent": intent, "args": args, "answer": str(answer)}


def ask_llm(messages: list) -> dict:
    """Отправить сообщения в OpenRouter и вернуть нормализованный ответ."""
    if not OPENROUTER_API_KEY:
        raise LLMError("API-ключ OpenRouter не задан (OPENROUTER_API_KEY)")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jarvis",
        "X-Title": "Jarvis Assistant",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 300,
    }

    last_error = None
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            resp = requests.post(
                OPENROUTER_URL, json=payload, headers=headers, timeout=LLM_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return normalize_result(extract_json(content))
        except (requests.RequestException, KeyError, IndexError, LLMError) as e:
            last_error = e
            logger.warning("Попытка LLM %d не удалась: %s", attempt + 1, e)
            if attempt < LLM_MAX_RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise LLMError(f"LLM недоступна: {last_error}")


def build_messages(history: list, text: str) -> list:
    """Собрать сообщения: системная подсказка + история (без дубля текущей фразы)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    history = list(history or [])
    if history and history[-1].get("role") == "user" and history[-1].get("content") == text:
        history = history[:-1]
    messages.extend(history)
    messages.append({"role": "user", "content": text})
    return messages


def understand(text: str, history: list | None = None) -> dict:
    """Определить намерение по тексту. Возвращает dict с intent/args/answer."""
    try:
        return ask_llm(build_messages(history, text))
    except LLMError as e:
        logger.error("%s", e)
        return {"intent": "error", "args": {}, "answer": str(e)}
