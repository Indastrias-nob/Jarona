"""Диалог с LLM через OpenRouter: определение намерения команды."""

import json
import logging
import re
import time

import requests

from config import (
    LLM_BACKOFF_BASE,
    LLM_MAX_RETRIES,
    LLM_TIMEOUT,
    OPENROUTER_API_KEY,
    OPENROUTER_FALLBACK_MODELS,
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


class LLMBusyError(LLMError):
    """Модель перегружена (429/503) — имеет смысл повторить позже."""


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


def _models() -> list:
    """Модели в порядке попыток: основная, затем резервные."""
    models = [OPENROUTER_MODEL]
    models += [m for m in OPENROUTER_FALLBACK_MODELS if m != OPENROUTER_MODEL]
    return models


def _retry_after(response, attempt: int) -> float:
    """Пауза перед повтором: из заголовка Retry-After или экспоненциальная."""
    header = response.headers.get("Retry-After") if response is not None else None
    if header:
        try:
            return min(float(header), 30.0)
        except ValueError:
            pass
    return min(LLM_BACKOFF_BASE * (2 ** attempt), 30.0)


def _ask_model(model: str, messages: list, headers: dict) -> dict:
    """Запрос к одной модели с повторами при перегрузке."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 300,
    }
    last_error = None
    for attempt in range(LLM_MAX_RETRIES + 1):
        response = None
        try:
            response = requests.post(
                OPENROUTER_URL, json=payload, headers=headers, timeout=LLM_TIMEOUT
            )
            if response.status_code in (429, 503):
                raise LLMBusyError(
                    f"{response.status_code} — модель {model} перегружена: "
                    f"{response.text[:200]}"
                )
            if response.status_code != 200:
                # Причина отказа (лимит, кредиты, неверная модель) — в теле ответа
                raise LLMError(
                    f"{response.status_code} для {model}: {response.text[:300]}"
                )
            choices = response.json().get("choices") or []
            if not choices:
                raise LLMError(f"{model} вернула ответ без поля choices")
            message = choices[0].get("message") or {}
            # reasoning-модели могут вернуть пустой content — берём reasoning
            content = message.get("content") or message.get("reasoning") or ""
            if not content.strip():
                raise LLMError(f"{model} вернула пустой ответ")
            return normalize_result(extract_json(content))
        except LLMBusyError as e:
            last_error = e
            delay = _retry_after(response, attempt)
            logger.warning(
                "Попытка %d/%d (%s): %s — повтор через %.1f с",
                attempt + 1, LLM_MAX_RETRIES + 1, model, e, delay,
            )
            if attempt < LLM_MAX_RETRIES:
                time.sleep(delay)
        except (requests.RequestException, KeyError, IndexError, LLMError) as e:
            last_error = e
            logger.warning("Попытка %d (%s) не удалась: %s", attempt + 1, model, e)
            break  # не ошибка перегрузки — повторять ту же модель смысла нет
    raise last_error


def ask_llm(messages: list) -> dict:
    """Отправить сообщения в OpenRouter, перебирая доступные модели."""
    if not OPENROUTER_API_KEY:
        raise LLMError("API-ключ OpenRouter не задан (OPENROUTER_API_KEY)")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/jarvis",
        "X-Title": "Jarvis Assistant",
    }

    errors = []
    busy_only = True
    for model in _models():
        try:
            return _ask_model(model, messages, headers)
        except LLMBusyError as e:
            errors.append(f"{model}: {e}")
            logger.warning("Модель %s перегружена, пробуем следующую", model)
        except LLMError as e:
            errors.append(f"{model}: {e}")
            busy_only = False
            logger.warning("Модель %s недоступна, пробуем следующую", model)

    message = "; ".join(errors) or "нет доступных моделей"
    # Если все модели были заняты — это временная проблема, её стоит повторить
    raise LLMBusyError(message) if busy_only else LLMError(message)


def check_llm() -> tuple[bool, str]:
    """Проверить доступность LLM (для --check-llm). Возвращает (успех, сообщение)."""
    if not OPENROUTER_API_KEY:
        return False, "OPENROUTER_API_KEY не задан"
    try:
        result = ask_llm(build_messages([], "ответь одним словом: тест"))
        return True, f"LLM отвечает: {result}"
    except LLMError as e:
        return False, str(e)


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
    except LLMBusyError:
        logger.error("Все модели перегружены (429/503)")
        return {
            "intent": "busy",
            "args": {},
            "answer": "Сервис распознавания перегружен, попробуйте через минуту.",
        }
    except LLMError as e:
        logger.error("%s", e)
        return {"intent": "error", "args": {}, "answer": str(e)}
