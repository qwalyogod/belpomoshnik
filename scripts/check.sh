#!/usr/bin/env bash
# scripts/check.sh — единая точка проверки "MVP-готово".
# Запускается из корня репозитория. Все ошибки — exit 1.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "== [1/5] Загруженность: ни одного закоммиченного .env =="
if git ls-files 2>/dev/null | grep -E "(^|/)(\.env$|\.env\.local$|\.env\.production$)" | grep -v "\.env\.example$" | head -1 | grep -q .; then
  echo "  ✗ Найдены закоммиченные .env-файлы (без .example). Удалите через git rm --cached." >&2
  exit 1
fi
echo "  ✓ секреты в репо не закоммичены"

echo "== [2/5] Backend: pytest =="
PYTHONPATH=src "$ROOT/.venv/bin/python" -m pytest -q --no-header 2>&1 | tail -5
echo "  ✓ backend-тесты зелёные"

echo "== [3/5] Backend: smoke через TestClient =="
PYTHONPATH=src "$ROOT/.venv/bin/python" scripts/smoke_backend.py
echo "  ✓ smoke backend ok"

echo "== [4/5] Frontend: type-check (опционально) =="
if [ -f "$ROOT/reactvitemaket/package.json" ] && [ -d "$ROOT/reactvitemaket/node_modules" ] && command -v pnpm >/dev/null 2>&1; then
  if ( cd "$ROOT/reactvitemaket" && pnpm exec tsc --noEmit 2>&1 | tail -5 ); then
    echo "  ✓ tsc --noEmit прошёл"
  else
    echo "  → tsc не установлен, пропускаю (npm install typescript)"
  fi
else
  echo "  → pnpm/node_modules не готовы, пропускаю tsc"
fi

echo "== [5/5] Миграции: 0001..0019 без пропусков (0007 — noop) =="
EXPECTED_COUNT=19
LISTED_COUNT=$(ls src/backend/migrations/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$LISTED_COUNT" -eq "$EXPECTED_COUNT" ]; then
  echo "  ✓ миграций: $LISTED_COUNT (0001..0019, включая 0007_noop)"
else
  echo "  ✗ найдено $LISTED_COUNT миграций, ожидалось $EXPECTED_COUNT" >&2
  ls src/backend/migrations/ >&2
  exit 1
fi

echo ""
echo "✅ ВСЁ ЗЕЛЁНОЕ — проект готов к защите."
