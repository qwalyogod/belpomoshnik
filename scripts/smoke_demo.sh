#!/usr/bin/env bash
# scripts/smoke_demo.sh — e2e проверка 5 ключевых защитных сценариев.
# Требует: запущенный backend на $API (default http://127.0.0.1:8060).
# Использование: bash scripts/smoke_demo.sh
set -euo pipefail

API="${API:-http://127.0.0.1:8060}"
USER="demo-smoke-$(date +%s)@bel.by"
PASS="demo-pass-12"

echo "==> smoke_demo against $API"

# 1. Health
echo "[1/5] /api/health"
H=$(curl -sf "$API/api/health")
echo "  $H"

# 2. Register
echo "[2/5] register + login (citizen)"
TOKENS=$(curl -sf -X POST "$API/api/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$USER\",\"password\":\"$PASS\",\"name\":\"Smoke\"}")
ACCESS=$(echo "$TOKENS" | "$PYTHON" -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "  ✓ citizen registered, got access_token (${#ACCESS} chars)"

# 3. /me
echo "[3/5] /api/auth/me (citizen)"
ME=$(curl -sf -H "Authorization: Bearer $ACCESS" "$API/api/auth/me")
echo "  ✓ me: $ME"

# 4. Public read
echo "[4/5] /api/problems (public)"
COUNT=$(curl -sf "$API/api/problems" | "$PYTHON" -c "import sys,json;print(len(json.load(sys.stdin)))")
echo "  ✓ problems: $COUNT"

# 5. Admin защищён
echo "[5/5] admin endpoints 401"
CODE=$(curl -s -o /dev/null -w '%{http_code}' "$API/api/admin/problems")
[ "$CODE" = "401" ] || { echo "  ✗ /api/admin/problems вернул $CODE, ожидался 401" >&2; exit 1; }
echo "  ✓ /api/admin/problems → 401"

CODE=$(curl -s -o /dev/null -w '%{http_code}' "$API/api/admin/bootstrap/problems")
[ "$CODE" = "401" ] || { echo "  ✗ /api/admin/bootstrap/problems вернул $CODE, ожидался 401" >&2; exit 1; }
echo "  ✓ /api/admin/bootstrap/problems → 401"

# 6. Documents CRUD
echo "[+] /api/user/documents CRUD"
DOC=$(curl -sf -X POST "$API/api/user/documents" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"title":"Smoke","doc_type":"passport","number":"HB1234567"}')
DOC_ID=$(echo "$DOC" | "$PYTHON" -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "  ✓ created doc #$DOC_ID"

CODE=$(curl -s -o /dev/null -w '%{http_code}' "$API/api/user/documents/$DOC_ID/scan" -H "Authorization: Bearer $ACCESS")
[ "$CODE" = "404" ] || { echo "  ✗ /api/user/documents/$DOC_ID/scan → $CODE, ожидался 404" >&2; exit 1; }
echo "  ✓ /api/user/documents/$DOC_ID/scan → 404 (без скана)"

# 7. Settings allow-list
echo "[+] /api/user/settings allow-list"
SETT=$(curl -sf -X PATCH "$API/api/user/settings" \
  -H "Authorization: Bearer $ACCESS" -H 'Content-Type: application/json' \
  -d '{"role":"platform_admin","is_admin":true,"theme":"dark"}')
echo "  ✓ settings response: $SETT"
echo "$SETT" | grep -q '"role"' && { echo "  ✗ role применился!" >&2; exit 1; }
echo "  ✓ role отфильтрован allow-list"

echo ""
echo "✅ smoke_demo: 5 защитных сценариев + 2 расширенных — все ok."
