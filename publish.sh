#!/bin/bash
# Быстрая публикация на GitHub

set -e

REPO_URL="https://github.com/Indastrias-nob/Jarona.git"

echo "╔════════════════════════════════════════╗"
echo "║   Jarona 0.1.0 — Push to GitHub        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Проверка, что мы в правильной ветке
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "jarona-v0.1.0" ]; then
  echo "❌ Не на ветке jarona-v0.1.0 (текущая: $CURRENT_BRANCH)"
  echo "Выполните: git checkout jarona-v0.1.0"
  exit 1
fi

# Проверка remote
if git remote | grep -q "^origin$"; then
  echo "✓ Remote 'origin' уже настроен:"
  git remote get-url origin
else
  echo "📡 Добавление remote 'origin'..."
  git remote add origin "$REPO_URL"
  echo "✓ Remote добавлен: $REPO_URL"
fi

echo ""
echo "📤 Push ветки jarona-v0.1.0..."
echo ""
echo "⚠️  ВАЖНО: GitHub требует Personal Access Token (PAT)"
echo "Если push не работает:"
echo "  1. Создайте токен: https://github.com/settings/tokens"
echo "  2. Выберите scope: repo"
echo "  3. При запросе пароля введите токен"
echo ""
echo "Или переключитесь на SSH:"
echo "  git remote set-url origin git@github.com:Indastrias-nob/Jarona.git"
echo ""
read -p "Нажмите Enter для продолжения..."

git push -u origin jarona-v0.1.0

echo ""
echo "✅ Готово!"
echo ""
echo "Проверьте репозиторий:"
echo "  https://github.com/Indastrias-nob/Jarona"
echo ""
echo "Следующие шаги:"
echo "  1. Создать Release v0.1.0 на GitHub"
echo "  2. Опционально: push ветку master (git push origin master)"
echo ""
