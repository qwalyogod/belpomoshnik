#!/usr/bin/env bash
# Запуск FastAPI backend (uvicorn) для dev-режима.
# Используется через `pnpm dev:all` (concurrently) или напрямую.
# Приоритет источников uvicorn:
#   1) ./.venv/bin/uvicorn (если есть venv)
#   2) системный `python3 -m uvicorn` (если venv нет)
#
# Хост: 0.0.0.0 — обязательно для доступа с мобильного устройства по LAN
# (иначе телефон/планшет по Wi-Fi не достучатся до бэка). Override через
# BELPOMOSHNIK_BACKEND_HOST (по умолчанию 0.0.0.0).
# Override порта — BELPOMOSHNIK_BACKEND_PORT (по умолчанию 8060).
set -euo pipefail

cd "$(dirname "$0")/.."

HOST="${BELPOMOSHNIK_BACKEND_HOST:-0.0.0.0}"
PORT="${BELPOMOSHNIK_BACKEND_PORT:-8060}"

# Подсказка: напечатать LAN-адрес для подключения мобильного WebView.
lan_hint() {
  python3 - <<'PY' 2>/dev/null || true
import socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    print(f"http://{s.getsockname()[0]}:{PORT}")
    s.close()
except OSError:
    pass
PY
}

if [ -x ".venv/bin/uvicorn" ]; then
  echo "Backend будет доступен по:"
  lan_hint
  echo "Скопируйте этот адрес в ServerPicker (или BELPOMOSHNIK_API_BASE_URL)."
  PYTHONPATH=src exec ./.venv/bin/uvicorn backend.app:app --host "$HOST" --port "$PORT" --reload
elif command -v python3 >/dev/null 2>&1; then
  echo "Backend будет доступен по:"
  lan_hint
  echo "Скопируйте этот адрес в ServerPicker (или BELPOMOSHNIK_API_BASE_URL)."
  PYTHONPATH=src exec python3 -m uvicorn backend.app:app --host "$HOST" --port "$PORT" --reload
else
  echo "Не найден ни .venv/bin/uvicorn, ни python3. Создай .venv или установи Python." >&2
  exit 1
fi
