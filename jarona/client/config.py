"""Конфигурация Windows клиента Jarona."""

import os

# --- Сервер ---
SERVER_IP = os.environ.get("JARONA_SERVER_IP", "192.168.1.100")
SERVER_PORT = int(os.environ.get("JARONA_SERVER_PORT", "8080"))
SERVER_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
WS_URL = f"ws://{SERVER_IP}:{SERVER_PORT}/ws"

# --- Авторизация ---
AUTH_TOKEN = os.environ.get("JARONA_AUTH_TOKEN", "")

# --- Безопасность файловых операций ---
# Разрешённые каталоги для файловых операций
ALLOWED_FILE_ROOTS = [
    os.path.expanduser("~"),  # Домашний каталог
    "C:\\Users",              # Все пользователи
]

# Подтверждение удаления
CONFIRM_DELETE = True

# --- Громкость ---
VOLUME_STEP = 10

# --- Логирование ---
LOG_LEVEL = os.environ.get("JARONA_LOG_LEVEL", "INFO")
LOG_FILE = os.path.expanduser("~/jarona-client.log")
