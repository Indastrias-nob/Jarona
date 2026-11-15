# Инструкция по публикации Jarona на GitHub

## Шаг 1: Создать репозиторий на GitHub

1. Перейдите на https://github.com/new
2. Заполните форму:
   - **Repository name**: `Jarona`
   - **Description**: `Голосовой помощник для Orange Pi 4 Pro (DietPi) с удалённым управлением Windows ПК`
   - **Visibility**: ✅ **Private** (приватный)
   - **НЕ** создавайте README, .gitignore или LICENSE (они уже есть в проекте)
3. Нажмите **Create repository**

## Шаг 2: Привязать локальный репозиторий

После создания репозитория GitHub покажет команды. Выполните:

```bash
cd /home/indastrias/new11

# Добавить remote
git remote add origin https://github.com/Indastrias-nob/Jarona.git

# Проверить
git remote -v
```

## Шаг 3: Push ветки jarona-v0.1.0

```bash
# Push ветки с новым проектом
git push -u origin jarona-v0.1.0

# Опционально: push ветки master (старый Jarvis)
git push -u origin master
```

## Шаг 4: Создать Release v0.1.0

1. Перейдите в репозиторий: https://github.com/Indastrias-nob/Jarona
2. Нажмите **Releases** → **Create a new release**
3. Заполните:
   - **Tag**: `v0.1.0`
   - **Target**: `jarona-v0.1.0` (выберите ветку)
   - **Title**: `Jarona 0.1.0 — первый релиз`
   - **Description**: скопируйте из `CHANGELOG.md`
4. Нажмите **Publish release**

## Шаг 5: Установить главную ветку (опционально)

Если хотите сделать `jarona-v0.1.0` главной веткой:

1. Settings → Branches → Default branch
2. Выберите `jarona-v0.1.0`
3. Нажмите **Update**

Или создайте `main` ветку из `jarona-v0.1.0`:

```bash
git checkout jarona-v0.1.0
git checkout -b main
git push -u origin main
```

## Альтернатива: использовать GitHub CLI

Если хотите автоматизировать, установите GitHub CLI:

```bash
# Fedora
sudo dnf install gh

# Авторизация
gh auth login

# Создать репозиторий
gh repo create Jarona --private --source=. --remote=origin

# Push
git push -u origin jarona-v0.1.0

# Создать release
gh release create v0.1.0 --title "Jarona 0.1.0" --notes-file CHANGELOG.md --target jarona-v0.1.0
```

## Проверка

После публикации проверьте:

1. Репозиторий доступен: https://github.com/Indastrias-nob/Jarona
2. Ветка `jarona-v0.1.0` загружена
3. Файлы на месте (jarona/, docs/, README.md и т.д.)
4. Release v0.1.0 создан

## Клонирование (для других машин)

```bash
# С аутентификацией
git clone https://github.com/Indastrias-nob/Jarona.git

# Переключиться на рабочую ветку
cd Jarona
git checkout jarona-v0.1.0
```

## Работа с репозиторием

### Обновление кода

```bash
# Внести изменения
git add .
git commit -m "fix: описание изменений

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"

git push origin jarona-v0.1.0
```

### Создание новой версии

```bash
# Обновить VERSION
echo "0.2.0" > jarona/VERSION

# Обновить CHANGELOG.md
# ... добавить изменения ...

# Коммит
git add jarona/VERSION CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"

# Tag и push
git tag v0.2.0
git push origin jarona-v0.1.0 --tags

# Создать release на GitHub
gh release create v0.2.0 --title "Jarona 0.2.0" --notes-file CHANGELOG.md
```

---

**Готово!** Теперь проект можно публиковать на GitHub.

Выполните команды из **Шаг 2** и **Шаг 3** для загрузки кода.
