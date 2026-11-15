#!/bin/bash
# Установка Jarona на Orange Pi 4 Pro с DietPi

set -e

echo "╔════════════════════════════════════════╗"
echo "║  Установка Jarona 0.1.0 на DietPi      ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Запустите скрипт с sudo"
  exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get upgrade -y

# Системные зависимости
echo "📦 Установка системных пакетов..."
apt-get install -y \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev \
  git \
  espeak-ng \
  portaudio19-dev \
  libgpiod-dev \
  libgpiod2 \
  alsa-utils \
  pulseaudio \
  wget \
  unzip

# Создание каталогов
echo "📁 Создание каталогов..."
mkdir -p /opt/jarona
mkdir -p /opt/jarona/models
mkdir -p /var/lib/jarona
mkdir -p /var/log/jarona

# Скачивание модели Vosk
echo "📥 Загрузка модели Vosk для русского языка..."
VOSK_MODEL="vosk-model-small-ru-0.22"
if [ ! -d "/opt/jarona/models/$VOSK_MODEL" ]; then
  cd /opt/jarona/models
  wget "https://alphacephei.com/vosk/models/${VOSK_MODEL}.zip"
  unzip "${VOSK_MODEL}.zip"
  rm "${VOSK_MODEL}.zip"
  ln -sf "$VOSK_MODEL" vosk-model-ru
  echo "✓ Модель Vosk установлена: /opt/jarona/models/$VOSK_MODEL"
else
  echo "✓ Модель Vosk уже установлена"
fi

# Python окружение
echo "🐍 Создание виртуального окружения..."
cd /opt/jarona
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
echo "📦 Установка Python пакетов..."
pip install --upgrade pip
pip install wheel

# Установка основных зависимостей
pip install \
  fastapi \
  uvicorn[standard] \
  websockets \
  pydantic \
  requests \
  vosk \
  sounddevice \
  psutil \
  python-dotenv

# GPIO библиотека (lgpio как fallback, если gpiod не работает)
echo "📦 Установка GPIO библиотеки..."
pip install lgpio || echo "⚠️  lgpio не установлен (требует совместимости с ядром)"

# Копирование файлов проекта
echo "📋 Копирование файлов Jarona..."
# (предполагается, что скрипт запущен из корня репозитория)
cp -r server/ /opt/jarona/
cp -r shared/ /opt/jarona/
cp requirements-server.txt /opt/jarona/

# Конфигурация
echo "⚙️  Создание конфигурационного файла..."
cat > /opt/jarona/.env << EOF
# Jarona конфигурация
JARONA_MODE=server
JARONA_HOST=0.0.0.0
JARONA_PORT=8080

# OpenRouter API (замените на свой ключ)
OPENROUTER_API_KEY=

# Vosk модель
VOSK_MODEL_PATH=/opt/jarona/models/vosk-model-ru

# GPIO
JARONA_GPIO=true
JARONA_GPIO_LIB=lgpio

# TTS
JARONA_TTS=espeak

# Данные
JARONA_DATA_DIR=/var/lib/jarona
JARONA_LOG_LEVEL=INFO
EOF

# Systemd сервис
echo "🔧 Создание systemd сервиса..."
cat > /etc/systemd/system/jarona.service << EOF
[Unit]
Description=Jarona Voice Assistant
After=network.target sound.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/jarona
EnvironmentFile=/opt/jarona/.env
ExecStart=/opt/jarona/venv/bin/python /opt/jarona/server/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Права доступа
echo "🔒 Настройка прав доступа..."
chown -R root:root /opt/jarona
chown -R root:root /var/lib/jarona
chmod 755 /opt/jarona
chmod 644 /opt/jarona/.env

# Включение сервиса
echo "🚀 Включение сервиса..."
systemctl daemon-reload
systemctl enable jarona.service

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Настройка:"
echo "  1. Отредактируйте /opt/jarona/.env"
echo "  2. Добавьте OPENROUTER_API_KEY"
echo "  3. Запустите сервис: systemctl start jarona"
echo ""
echo "Команды:"
echo "  systemctl start jarona    — запустить"
echo "  systemctl stop jarona     — остановить"
echo "  systemctl status jarona   — статус"
echo "  journalctl -u jarona -f   — логи"
echo ""
echo "Тестирование:"
echo "  source /opt/jarona/venv/bin/activate"
echo "  cd /opt/jarona/server"
echo "  python main.py"
echo ""
