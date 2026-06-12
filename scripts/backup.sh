#!/usr/bin/env bash
# H10 — Резервное копирование «Белпомощник» (MySQL)
#
# Что делает:
#   1. mysqldump основной БД (BELPOMOSHNIK_DATABASE_URL)
#   2. Архив файлов загрузок (data/uploads/)
#   3. Сохраняет в BACKUP_DIR с временной меткой
#   4. Удаляет резервные копии старше KEEP_DAYS дней
#
# Использование:
#   chmod +x scripts/backup.sh
#   ./scripts/backup.sh                    # ручной запуск
#   # cron: каждый день в 03:00
#   0 3 * * * /path/to/belpomoshnik/scripts/backup.sh >> /var/log/belpomoshnik-backup.log 2>&1
#
# Зависимости: mysqldump (mysql-client), tar, gzip. Стандартно в Debian/Ubuntu
# пакет `default-mysql-client` (apt) / `mysql-client` (brew).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKUP_DIR="${BELPOMOSHNIK_BACKUP_DIR:-$PROJECT_DIR/backups}"
UPLOADS_DIR="${BELPOMOSHNIK_UPLOAD_DIR:-$PROJECT_DIR/data/uploads}"
KEEP_DAYS="${BELPOMOSHNIK_BACKUP_KEEP_DAYS:-14}"

# Парсим MySQL-URL для mysqldump. Ожидаемый формат:
#   mysql+pymysql://user:password@host:port/database?charset=utf8mb4
parse_mysql_url() {
    local url="${1:-}"
    if [[ -z "$url" ]]; then
        echo "ERROR: BELPOMOSHNIK_DATABASE_URL is empty" >&2
        exit 1
    fi
    # Отрезаем диалектный префикс, чтобы urlparse отдал корректные user/pass/host/port/path
    echo "$url" | sed -E 's#^mysql\+pymysql://##'
}

DB_URL="${BELPOMOSHNIK_DATABASE_URL:-mysql+pymysql://root:belp_root@127.0.0.1:3306/belpomoshnik?charset=utf8mb4}"
DB_URL_BARE="$(parse_mysql_url "$DB_URL")"

# Простой парсер на awk: scheme://user:pass@host:port/db?...
PARSED_HOST="$(echo "$DB_URL_BARE" | awk -F'@' '{print $NF}' | awk -F'/' '{print $1}' | awk -F':' '{print $1}')"
PARSED_PORT="$(echo "$DB_URL_BARE" | awk -F'@' '{print $NF}' | awk -F'/' '{print $1}' | awk -F':' '{print $2}')"
PARSED_DB="$(echo "$DB_URL_BARE" | awk -F'/' '{print $NF}' | awk -F'?' '{print $1}')"
PARSED_USER="$(echo "$DB_URL_BARE" | awk -F'@' '{print $1}' | awk -F'/' '{print $NF}' | awk -F':' '{print $1}')"
PARSED_PASS="$(echo "$DB_URL_BARE" | awk -F'@' '{print $1}' | awk -F'/' '{print $NF}' | awk -F':' '{print $2}')"

PARSED_PORT="${PARSED_PORT:-3306}"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$BACKUP_DIR/$TIMESTAMP"

echo "[backup] Начало: $TIMESTAMP"
mkdir -p "$DEST"

# 1. mysqldump
if command -v mysqldump >/dev/null 2>&1; then
    MYSQLDUMP_PWD="$PARSED_PASS" mysqldump \
        --user="$PARSED_USER" \
        --host="$PARSED_HOST" \
        --port="$PARSED_PORT" \
        --default-character-set=utf8mb4 \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --add-drop-table \
        "$PARSED_DB" > "$DEST/belpomoshnik.sql"
    echo "[backup] БД сохранена: $DEST/belpomoshnik.sql (host=$PARSED_HOST db=$PARSED_DB)"
else
    echo "[backup] WARN: mysqldump не найден в PATH. Установите mysql-client (apt/brew) и повторите." >&2
    exit 1
fi

# 2. Файлы загрузок
if [ -d "$UPLOADS_DIR" ]; then
    tar -czf "$DEST/uploads.tar.gz" -C "$(dirname "$UPLOADS_DIR")" "$(basename "$UPLOADS_DIR")"
    echo "[backup] uploads архивирован: $DEST/uploads.tar.gz"
else
    echo "[backup] INFO: $UPLOADS_DIR не существует, файлы пропущены."
fi

# 3. Архивировать всё в один .tar.gz и удалить поддиректорию
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$DEST"
echo "[backup] Архив: $BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# 4. Ротация: удалить старые резервные копии
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime "+$KEEP_DAYS" -delete
echo "[backup] Ротация: удалены копии старше $KEEP_DAYS дней."

echo "[backup] Завершено."
