#!/usr/bin/env bash
# Запуск FastAPI backend (uvicorn) для dev-режима.
# Используется через `pnpm dev:all` (concurrently) или напрямую.
# Приоритет источников uvicorn:
#   1) ./.venv/bin/uvicorn (если есть venv)
#   2) системный `python3 -m uvicorn` (если venv нет)
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -x ".venv/bin/uvicorn" ]; then
  PYTHONPATH=src exec ./.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8060 --reload
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH=src exec python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8060 --reload
else
  echo "Не найден ни .venv/bin/uvicorn, ни python3. Создай .venv или установи Python." >&2
  exit 1
fi
