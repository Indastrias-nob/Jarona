# Jarona 0.1.0 — Быстрый старт

## Установка на Orange Pi 4 Pro (DietPi)

```bash
# Клонировать репозиторий
git clone https://github.com/ВАШЕ_ИМЯ/Jarona.git
cd Jarona/jarona

# Запустить установку (требуется sudo)
sudo bash setup-dietpi.sh

# Настроить конфигурацию
sudo nano /opt/jarona/.env

# Добавить API ключ OpenRouter
OPENROUTER_API_KEY=sk-or-...

# Запустить сервер
sudo systemctl start jarona

# Проверить статус
sudo systemctl status jarona

# Посмотреть логи
journalctl -u jarona -f
```

## Установка Windows клиента

```powershell
# Установить Python 3.9+ с python.org

# Перейти в папку клиента
cd Jarona\jarona\client

# Установить зависимости
pip install -r ..\requirements-client.txt

# Настроить IP сервера
notepad config.py
# Изменить: SERVER_IP = "192.168.1.100"

# Запустить клиент
python client.py
```

## Тестирование

### Автономный режим (без Windows)

```bash
# На Orange Pi
export JARONA_MODE=standalone
cd /opt/jarona/server
source ../venv/bin/activate
python main.py

# Говорите после слова "Жарона":
# "Жарона, включи пин 17"
# "Жарона, статус GPIO"
# "Жарона, выход"
```

### Серверный режим (с Windows клиентом)

```bash
# На Orange Pi
sudo systemctl start jarona

# На Windows
python client.py

# Говорите на Orange Pi:
# "Жарона, открой браузер" → откроется на Windows
# "Жарона, громкость 50" → изменится на Windows
# "Жарона, скриншот" → сохранится на Windows
```

## Команды

### Локальные (Orange Pi)
```
включи пин 17
выключи пин 17
прочитай пин 17
статус GPIO
```

### Удалённые (Windows)
```
открой браузер
запусти блокнот
громкость 50 / громче / тише
создай файл C:\test.txt
напиши в файл C:\test.txt привет от Жароны
скриншот
найди в интернете рецепт борща
```

### Общие
```
помощь
выход
```

## Troubleshooting

### Vosk не распознаёт
```bash
# Проверить микрофон
arecord -l

# Проверить модель
ls /opt/jarona/models/vosk-model-ru

# Тест распознавания
cd /opt/jarona/server
python recognition.py
```

### WebSocket не подключается
```bash
# Открыть порт
sudo ufw allow 8080

# Проверить IP
ip addr show

# Проверить сервер
sudo systemctl status jarona
curl http://localhost:8080/
```

### GPIO не работает
```bash
# Проверить права
ls -l /dev/gpiochip0

# Тест GPIO
cd /opt/jarona/server
sudo python gpio_control.py
```

## Обновление версии

```bash
# Остановить сервис
sudo systemctl stop jarona

# Обновить код
cd /path/to/Jarona
git pull

# Скопировать новые файлы
sudo cp -r jarona/server/* /opt/jarona/server/
sudo cp -r jarona/shared/* /opt/jarona/shared/

# Обновить зависимости
cd /opt/jarona
source venv/bin/activate
pip install -r requirements-server.txt

# Запустить
sudo systemctl start jarona
```

## Документация

- **README**: `jarona/README.md` — полное описание
- **Архитектура**: `jarona/docs/ARCHITECTURE.md`
- **Миграция с Jarvis**: `jarona/docs/MIGRATION.md`

## Контакты

GitHub: https://github.com/ВАШЕ_ИМЯ/Jarona
Issues: https://github.com/ВАШЕ_ИМЯ/Jarona/issues
