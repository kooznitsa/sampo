#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Использование: $0 <tag>"
  exit 1
fi

TAG=$1

echo ">>> Переключаемся на main"
git checkout main

echo ">>> Подтягиваем последние изменения из origin/main"
git pull origin main

echo ">>> Мержим ветку dev"
git merge --no-ff dev

echo ">>> Отправляем изменения в origin/main"
git push origin main

echo ">>> Создаём тег $TAG"
git tag -a "$TAG" -m "Release $TAG"

echo ">>> Отправляем тег $TAG на origin"
git push origin "$TAG"

echo ">>> Готово!"
