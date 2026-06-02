#!/usr/bin/env bash
# H10 — Резервное копирование «Белпомощник»
#
# Что делает:
#   1. SQLite-дамп (основная БД + app_state.json)
#   2. Архив файлов документов пользователей (data/user_docs/)
#   3. Сохраняет в BACKUP_DIR с временной меткой
#   4. Удаляет резервные копии старше KEEP_DAYS дней
#
# Использование:
#   chmod +x scripts/backup.sh
#   ./scripts/backup.sh                    # ручной запуск
#   # cron: каждый день в 03:00
#   0 3 * * * /path/to/belpomoshnik/scripts/backup.sh >> /var/log/belpomoshnik-backup.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${BELPOMOSHNIK_BACKUP_DIR:-$PROJECT_DIR/backups}"
DB_PATH="${BELPOMOSHNIK_DB_PATH:-$PROJECT_DIR/data/belpomoshnik.db}"
STATE_PATH="$PROJECT_DIR/data/app_state.json"
DOCS_DIR="${BELPOMOSHNIK_DOCS_DIR:-$PROJECT_DIR/data/user_docs}"
PRIVATE_UPLOADS_DIR="$PROJECT_DIR/data/private_uploads"
KEEP_DAYS="${BELPOMOSHNIK_BACKUP_KEEP_DAYS:-14}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$BACKUP_DIR/$TIMESTAMP"

echo "[backup] Начало: $TIMESTAMP"
mkdir -p "$DEST"

# 1. SQLite backup — binary copy (online-safe) + SQL dump
if [ -f "$DB_PATH" ]; then
    sqlite3 "$DB_PATH" ".backup '$DEST/belpomoshnik.db'"
    sqlite3 "$DB_PATH" ".dump" > "$DEST/belpomoshnik.sql"
    echo "[backup] БД сохранена: $DEST/belpomoshnik.db + .sql"
else
    echo "[backup] WARN: БД не найдена по пути $DB_PATH, пропускаем."
fi

# 2. app_state.json (локальный стейт Flet)
if [ -f "$STATE_PATH" ]; then
    cp "$STATE_PATH" "$DEST/app_state.json"
    echo "[backup] app_state.json сохранён."
fi

# 3. Файлы документов пользователей
if [ -d "$DOCS_DIR" ]; then
    tar -czf "$DEST/user_docs.tar.gz" -C "$(dirname "$DOCS_DIR")" "$(basename "$DOCS_DIR")"
    echo "[backup] user_docs архивирован: $DEST/user_docs.tar.gz"
else
    echo "[backup] INFO: $DOCS_DIR не существует, файлы документов пропущены."
fi

# 3a. Зашифрованные сканы документов (private_uploads)
if [ -d "$PRIVATE_UPLOADS_DIR" ]; then
    tar -czf "$DEST/private_uploads.tar.gz" -C "$(dirname "$PRIVATE_UPLOADS_DIR")" "$(basename "$PRIVATE_UPLOADS_DIR")"
    echo "[backup] private_uploads архивирован: $DEST/private_uploads.tar.gz"
fi

# 4. Архивировать всё в один .tar.gz и удалить поддиректорию
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$DEST"
echo "[backup] Архив: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# 5. Ротация: удалить старые резервные копии
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime "+$KEEP_DAYS" -delete
echo "[backup] Ротация: удалены копии старше $KEEP_DAYS дней."

echo "[backup] Завершено."
