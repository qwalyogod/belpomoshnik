#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# Запуск Белпомощника в web-режиме.
#
# Использование:
#   ./scripts/run_web.sh
#
# Открывает:
#   http://localhost:8888  — Flet-приложение (F5 для обновления)
#   http://localhost:8060  — FastAPI бэкенд (Swagger: /docs)
# ──────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_FLET="$PROJECT_ROOT/.venv/bin/flet"

# Используем venv python если есть
PYTHON="${VENV_PYTHON:-python3}"
FLET_BIN="${VENV_FLET:-flet}"

cd "$PROJECT_ROOT"

# Применить миграцию 0004 если нужно (добавление колонок паспорт/права)
DB_FILE="$SRC_DIR/belpomoshnik.db"
MIGRATION="$SRC_DIR/backend/migrations/0004_passport_auth.sql"
if [ -f "$DB_FILE" ] && [ -f "$MIGRATION" ]; then
    echo "[migrate] Применяем $MIGRATION если колонки ещё не добавлены..."
    sqlite3 "$DB_FILE" < "$MIGRATION" 2>/dev/null || true
fi

# Запустить FastAPI бэкенд в фоне
echo "[backend] Запуск FastAPI на порту 8060..."
cd "$SRC_DIR"
"$PYTHON" -m uvicorn backend.app:app --host 127.0.0.1 --port 8060 --reload &
BACKEND_PID=$!
echo "[backend] PID: $BACKEND_PID"

# Дать бэкенду время запуститься
sleep 2

# Запустить Flet в web-режиме
echo "[flet] Запуск web-приложения на порту 8888..."
echo "[flet] Открыть: http://localhost:8888"
echo ""
"$FLET_BIN" run --web --port 8888 "$SRC_DIR/main.py" &
FLET_PID=$!
echo "[flet] PID: $FLET_PID"

# Обработать Ctrl+C — остановить оба процесса
trap "echo ''; echo 'Остановка...'; kill $BACKEND_PID $FLET_PID 2>/dev/null; exit 0" INT TERM

wait
