"""Клиент OpenRouter для Jarona с устойчивостью к сбоям."""

import json
import logging
import re
import time
from typing import Dict, Optional

import requests

from config import (
    LLM_BACKOFF_BASE,
    LLM_MAX_RETRIES,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT,
    OPENROUTER_API_KEY,
    OPENROUTER_FALLBACK_MODELS,
    OPENROUTER_MODEL,
    OPENROUTER_URL,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """LLM недоступна или вернула невалидный ответ."""


class LLMBusyError(LLMError):
    """Модель перегружена (429/503)."""


def _loads_lenient(text: str) -> dict:
    """Разобрать JSON, прощая True/False/None."""
    for candidate in (
        text,
        re.sub(
            r"\b(True|False|None)\b",
            lambda m: {"True": "true", "False": "false", "None": "null"}[m.group(1)],
            text,
        ),
    ):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Попытка разобрать как Python литерал
    try:
        import ast
        value = ast.literal_eval(text)
        if isinstance(value, dict):
            return value
    except (ValueError, SyntaxError):
        pass

    raise LLMError(f"Не удалось разобрать JSON: {text[:200]}")


def extract_json(content: str) -> dict:
    """Извлечь JSON из ответа (в т.ч. из markdown блока)."""
    if not content:
        raise LLMError("Пустой ответ LLM")

    text = content.strip()

    # Markdown блок
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        try:
            return _loads_lenient(fence.group(1).strip())
        except LLMError:
            pass

    # Поиск { ... }
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escape = False

        for i in range(start, len(text)):
            char = text[i]

            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return _loads_lenient(candidate)
                    except LLMError:
                        break

        start = text.find("{", start + 1)

    raise LLMError(f"JSON не найден в ответе: {text[:200]}")


def understand(command: str, context: Optional[list] = None) -> dict:
    """Понять намерение пользователя через LLM.

    Args:
        command: текст команды
        context: история диалога [{"role": "user/assistant", "content": "..."}]

    Returns:
        {"intent": "...", "args": {...}, "answer": "...", "target": "..."}

    Raises:
        LLMError: не удалось получить валидный ответ
        LLMBusyError: модель перегружена, попробовать позже
    """
    if not OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY не установлен")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        messages.extend(context)

    messages.append({"role": "user", "content": command})

    models_to_try = [OPENROUTER_MODEL] + OPENROUTER_FALLBACK_MODELS

    for model in models_to_try:
        logger.info(f"Запрос к модели: {model}")

        for attempt in range(LLM_MAX_RETRIES):
            try:
                response = _query_model(model, messages)
                intent = extract_json(response)

                # Валидация
                if "intent" not in intent:
                    raise LLMError("Поле 'intent' отсутствует в ответе")

                logger.info(f"Распознано намерение: {intent.get('intent')}")
                return intent

            except LLMBusyError as e:
                if attempt < LLM_MAX_RETRIES - 1:
                    wait = LLM_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(f"Модель перегружена, повтор через {wait:.1f}с")
                    time.sleep(wait)
                else:
                    logger.warning(f"Модель {model} недоступна, пробуем следующую")
                    break
            except LLMError as e:
                logger.error(f"Ошибка модели {model}: {e}")
                break

    raise LLMBusyError("Все модели недоступны. Попробуйте позже.")


def _query_model(model: str, messages: list) -> str:
    """Выполнить запрос к OpenRouter."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jarona-assistant",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": LLM_MAX_TOKENS,
        "temperature": 0.7,
    }

    # Пробуем с response_format
    try:
        payload["response_format"] = {"type": "json_object"}
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=LLM_TIMEOUT,
        )

        # Если модель не поддерживает JSON mode — повторяем без него
        if response.status_code == 400:
            logger.debug("Модель не поддерживает response_format, повтор без него")
            del payload["response_format"]
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=LLM_TIMEOUT,
            )
    except requests.RequestException as e:
        raise LLMError(f"Ошибка сети: {e}")

    # Обработка ответа
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", 60)
        raise LLMBusyError(f"Rate limit, повтор через {retry_after}с")

    if response.status_code == 503:
        raise LLMBusyError("Сервис временно недоступен")

    if response.status_code != 200:
        raise LLMError(f"HTTP {response.status_code}: {response.text[:200]}")

    try:
        data = response.json()
    except json.JSONDecodeError:
        raise LLMError(f"Невалидный JSON: {response.text[:200]}")

    choices = data.get("choices", [])
    if not choices:
        raise LLMError("Пустой массив choices")

    message = choices[0].get("message", {})
    content = message.get("content", "").strip()

    # Reasoning-модели могут вернуть пустой content
    if not content:
        reasoning = message.get("reasoning", "")
        if reasoning:
            logger.debug(f"content пустой, используем reasoning: {reasoning[:100]}")
            content = reasoning
        else:
            raise LLMError("Пустой content и reasoning")

    return content


def check_llm() -> bool:
    """Проверить доступность LLM."""
    try:
        result = understand("привет", context=[])
        logger.info(f"LLM доступна: {result}")
        return True
    except Exception as e:
        logger.error(f"LLM недоступна: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    if not OPENROUTER_API_KEY:
        print("Установите OPENROUTER_API_KEY")
        exit(1)

    print("Проверка LLM...")
    if check_llm():
        print("✓ LLM работает")

        # Тестовые команды
        tests = [
            "открой браузер",
            "включи пин 17",
            "создай файл test.txt",
            "громкость 50",
        ]

        for cmd in tests:
            print(f"\n→ {cmd}")
            try:
                result = understand(cmd)
                print(f"✓ {result}")
            except Exception as e:
                print(f"✗ {e}")
    else:
        print("✗ LLM недоступна")
