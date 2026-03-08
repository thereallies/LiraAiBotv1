#!/bin/sh
set -eu

APP_FILE=""

for candidate in \
  "/app/index.py" \
  "/app/LiraAiBOT/index.py" \
  "/app/backend/main.py" \
  "/app/LiraAiBOT/backend/main.py"
do
  if [ -f "$candidate" ]; then
    APP_FILE="$candidate"
    break
  fi
done

if [ -z "$APP_FILE" ]; then
  echo "❌ Не найден entrypoint приложения. Проверенные пути:" >&2
  echo "   /app/index.py" >&2
  echo "   /app/LiraAiBOT/index.py" >&2
  echo "   /app/backend/main.py" >&2
  echo "   /app/LiraAiBOT/backend/main.py" >&2
  echo "📂 Содержимое /app:" >&2
  find /app -maxdepth 3 \( -name "index.py" -o -path "*/backend/main.py" \) 2>/dev/null || true
  exit 1
fi

echo "🚀 Запускаю: $APP_FILE"
exec python "$APP_FILE"
