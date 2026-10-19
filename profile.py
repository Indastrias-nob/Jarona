"""
Менеджер профиля пользователя.
Сохраняет и загружает информацию о пользователе (имя, предпочтения, история).
"""

import os
import json
import logging
from config import PROFILE_PATH, TMP_DIR

logger = logging.getLogger(__name__)


def load_profile():
    """Загрузить профиль из файла или создать новый"""
    os.makedirs(TMP_DIR, exist_ok=True)
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                profile = json.load(f)
            logger.info(f"Профиль загружен: {profile.get('name', 'неизвестный')}")
            return profile
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Ошибка загрузки профиля, создаётся новый: {e}")

    profile = {
        "name": "Пользователь",
        "language": "ru",
        "tts_engine": "espeak",
        "wake_word": "jarvis",
        "history_count": 0,
        "last_active": None,
    }
    save_profile(profile)
    return profile


def save_profile(profile: dict):
    """Сохранить профиль в файл"""
    profile["last_active"] = __import__("datetime").datetime.now().isoformat()
    profile["history_count"] = profile.get("history_count", 0) + 1
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        logger.info("Профиль сохранён")
    except IOError as e:
        logger.error(f"Ошибка сохранения профиля: {e}")


def update_profile_name(name: str):
    """Обновить имя пользователя"""
    profile = load_profile()
    profile["name"] = name
    save_profile(profile)
    return profile


def get_user_name():
    """Получить имя пользователя"""
    profile = load_profile()
    return profile.get("name", "пользователь")
