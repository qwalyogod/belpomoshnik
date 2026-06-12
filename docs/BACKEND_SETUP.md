# Backend — установка, запуск, БД, тесты

Backend: FastAPI + SQLAlchemy. Dev — SQLite, production — PostgreSQL.

## 1. Зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Для PostgreSQL дополнительно:

```bash
pip install "psycopg[binary]>=3.1"
```

Для тестов:

```bash
pip install pytest httpx
```

> Примечание (Python 3.14): старые жёсткие пины `fastapi==0.116.1`,
> `pydantic==2.11.7` не имеют wheels — pip разрешит более новые версии.
> `passlib` удалён: 1.7.4 несовместим с `bcrypt` 5.x, используем `bcrypt`
> напрямую (`src/backend/auth.py`).

## 2. Переменные окружения

| Переменная | Назначение | Дефолт |
|---|---|---|
| `BELPOMOSHNIK_DATABASE_URL` | URL БД (SQLAlchemy → MySQL 8) | `mysql+pymysql://root:belp_root@127.0.0.1:3306/belpomoshnik?charset=utf8mb4` |
| `BELPOMOSHNIK_UPLOAD_DIR`   | директория загрузок (аватары, обложки, сканы) | `<корень проекта>/data/uploads` |
| `BELPOMOSHNIK_SECRET_KEY` | ключ JWT + шифрования сканов | dev-заглушка (сменить!) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | TTL access-токена | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | TTL refresh-токена | `7` |
| `SMTP_HOST/PORT/USER/PASSWORD/FROM` | SMTP для email | gmail/пусто |
| `BELPOMOSHNIK_ADMIN_EMAIL` / `_PASSWORD` | создать админа при bootstrap | — |

> **Безопасность:** в production `BELPOMOSHNIK_SECRET_KEY` обязателен
> (256-бит). От него зависят и JWT, и ключ шифрования файлов сканов.

## 3. Инициализация БД

MySQL — единственная поддерживаемая СУБД. Поднимите её локально через
`docker compose up -d mysql` (см. `docker-compose.yml`) либо установите
mysql-server вручную и создайте БД/пользователя:

```sql
CREATE DATABASE belpomoshnik CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'belp'@'%' IDENTIFIED BY 'belp_root';
GRANT ALL ON belpomoshnik.* TO 'belp'@'%';
```

Затем — миграции + bootstrap одним скриптом (`scripts/init_db.py` сейчас
эквивалентен `migrate.py` + `bootstrap`):

```bash
PYTHONPATH=src python -m backend.scripts.init_db   # .sql-миграции + роли + тест-аккаунты
PYTHONPATH=src python -m backend.scripts.seed_db   # демо-контент (опц.)
```

`init_db` идемпотентен: применённые миграции записываются в таблицу
`schema_migrations` и не переигрываются.

## 4. Запуск API

```bash
cd src
uvicorn backend.app:app --host 0.0.0.0 --port 8060
```

- Swagger: `http://127.0.0.1:8060/docs`
- Health: `GET /api/health`
- Фоновый планировщик (asyncio, в lifespan): рассылка email-очереди
  каждые 60 с + очистка протухших refresh-токенов раз в час.

## 5. Тесты

```bash
python -m pytest          # 53 теста: auth, security, admin, dashboard, bootstrap
```

Изолированная MySQL-БД `belpomoshnik_test`, схема пересоздаётся на каждый тест
через `Base.metadata.drop_all/create_all` (env override — `BELPOMOSHNIK_TEST_DATABASE_URL`).

## 6. HTTPS (production)

API отдаёт HTTP. TLS терминировать на reverse-proxy:

```nginx
server {
    listen 443 ssl;
    server_name belpomoshnik.by;
    ssl_certificate     /etc/letsencrypt/live/belpomoshnik.by/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/belpomoshnik.by/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:8060;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Сертификат — Let's Encrypt (`certbot --nginx`). HTTP→HTTPS редирект на :80.

## 7. Резервное копирование

`scripts/backup.sh` — дамп БД (.backup + .sql), `app_state.json`,
зашифрованные сканы (`data/private_uploads/`), ротация. Cron:

```cron
0 3 * * * /path/to/belpomoshnik/scripts/backup.sh >> /var/log/belpomoshnik-backup.log 2>&1
```
