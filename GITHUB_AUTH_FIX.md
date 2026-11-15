# GitHub Authentication Fix — Решение проблемы аутентификации

## Проблема
```
remote: Invalid username or token.
fatal: Authentication failed for 'https://github.com/Indastrias-nob/Jarona.git/'
```

GitHub больше **не поддерживает** аутентификацию по паролю. Нужен **Personal Access Token (PAT)** или **SSH ключ**.

---

## ✅ Решение 1: Personal Access Token (PAT) — БЫСТРОЕ

### 1. Создать токен

1. Откройте: https://github.com/settings/tokens
2. **Generate new token** → **Generate new token (classic)**
3. Заполните:
   - **Note**: `Jarona CLI`
   - **Expiration**: `90 days` (или `No expiration`)
   - **Scopes**: ✅ **repo** (отметьте галочкой)
4. **Generate token**
5. **СКОПИРУЙТЕ ТОКЕН** (показан один раз!) — например: `ghp_ABC123def456...`

### 2. Использовать токен

```bash
cd /home/indastrias/new11

# Push
git push -u origin jarona-v0.1.0

# При запросе:
Username: Indastrias-nob
Password: <вставьте токен ghp_ABC123...>
```

### 3. Сохранить токен (опционально)

Чтобы не вводить каждый раз:

```bash
# Включить сохранение credentials
git config --global credential.helper store

# Теперь повторите push — токен сохранится
git push -u origin jarona-v0.1.0
# Введите username + token последний раз
```

⚠️ Токен сохранится в `~/.git-credentials` в открытом виде. Для большей безопасности используйте SSH.

---

## ✅ Решение 2: SSH ключ — БЕЗОПАСНЕЕ

### 1. Создать SSH ключ

```bash
# Генерация ключа
ssh-keygen -t ed25519 -C "pochatkovds@gmail.com"

# Нажмите Enter (сохранить в ~/.ssh/id_ed25519)
# Passphrase можно оставить пустым или задать

# Запустить SSH agent
eval "$(ssh-agent -s)"

# Добавить ключ
ssh-add ~/.ssh/id_ed25519
```

### 2. Скопировать публичный ключ

```bash
cat ~/.ssh/id_ed25519.pub
```

Скопируйте вывод (начинается с `ssh-ed25519 AAAA...`)

### 3. Добавить на GitHub

1. Откройте: https://github.com/settings/keys
2. **New SSH key**
3. **Title**: `Fedora Desktop`
4. **Key**: вставьте содержимое `id_ed25519.pub`
5. **Add SSH key**

### 4. Изменить remote на SSH

```bash
cd /home/indastrias/new11

# Переключить на SSH
git remote set-url origin git@github.com:Indastrias-nob/Jarona.git

# Проверить
git remote -v

# Push (без пароля!)
git push -u origin jarona-v0.1.0
```

### 5. Тест SSH (опционально)

```bash
ssh -T git@github.com
# Должно вывести: Hi Indastrias-nob! You've successfully authenticated...
```

---

## ✅ Решение 3: GitHub CLI (gh) — СОВРЕМЕННОЕ

### 1. Установить GitHub CLI

```bash
# Fedora
sudo dnf install gh

# Или другой способ
# https://cli.github.com/
```

### 2. Авторизоваться

```bash
gh auth login

# Выберите:
# - GitHub.com
# - HTTPS
# - Authenticate Git with your GitHub credentials: Yes
# - Login with a web browser (или Paste token)
```

### 3. Push

```bash
cd /home/indastrias/new11
git push -u origin jarona-v0.1.0
# Теперь работает автоматически!
```

### 4. Бонус: создать репозиторий через CLI

```bash
# Создать приватный репозиторий
gh repo create Jarona --private --source=. --remote=origin

# Push
git push -u origin jarona-v0.1.0

# Создать release
gh release create v0.1.0 \
  --title "Jarona 0.1.0" \
  --notes-file CHANGELOG.md \
  --target jarona-v0.1.0
```

---

## 🎯 Рекомендация

**Для разовой публикации:** используйте **Personal Access Token** (быстро)

**Для постоянной работы:** настройте **SSH** (безопасно и удобно)

**Если часто работаете с GitHub:** установите **GitHub CLI** (современно)

---

## 📋 Краткая инструкция (PAT)

```bash
# 1. Создайте токен: https://github.com/settings/tokens
#    Scope: repo, Expiration: 90 days

# 2. Скопируйте токен (ghp_...)

# 3. Push с токеном
cd /home/indastrias/new11
git push -u origin jarona-v0.1.0

# Username: Indastrias-nob
# Password: <токен ghp_...>

# 4. Сохранить (опционально)
git config --global credential.helper store
```

---

## 🔧 Проверка статуса

```bash
# Текущий remote
git remote -v

# Изменить на HTTPS (с токеном)
git remote set-url origin https://github.com/Indastrias-nob/Jarona.git

# Изменить на SSH
git remote set-url origin git@github.com:Indastrias-nob/Jarona.git
```

---

## ❓ FAQ

**Q: Где хранить токен безопасно?**  
A: Используйте менеджер паролей (KeePassXC, Bitwarden) или переключитесь на SSH.

**Q: Токен истёк (expired)?**  
A: Создайте новый на https://github.com/settings/tokens

**Q: SSH не работает (Permission denied)?**  
A: Проверьте ключ:
```bash
ssh -T git@github.com
ssh-add -l  # Должен показать ваш ключ
```

**Q: Могу ли я использовать пароль GitHub?**  
A: Нет, GitHub отключил password authentication с 2021 года.

---

**Выберите способ и продолжайте публикацию!** 🚀
