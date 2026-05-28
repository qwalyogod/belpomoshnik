# SECURITY_POLICY.md — Политика безопасности «Белпомощник»

> Документ описывает меры защиты персональных данных, аутентификации и хранения файлов.  
> Этап H ТЗ — «PostgreSQL, авторизация, безопасность».

---

## H8.1 Категории персональных данных

| Категория | Поля | Уровень чувствительности |
|-----------|------|--------------------------|
| Идентификатор | `email`, `name` | Средний |
| Профиль | `city`, `region`, `district`, `address`, `employment_status` | Средний |
| Признаки | `has_children`, `owns_property`, `has_car`, `is_renter` | Низкий |
| Документы | `number`, `issued_by`, `issued_date`, `expiry_date` | **Высокий** |
| Пароль | `hashed_password` | **Критический** (только хэш bcrypt, plaintext не хранится) |

---

## H8.2 Хранение и шифрование

### Пароли (H4)
- Хранятся только в виде bcrypt-хэша (cost factor 12).  
- Plaintext-пароль нигде не записывается, не логируется.  
- Реализация: `passlib[bcrypt]` → `src/backend/auth.py`.

### JWT-токены (H3)
- Access-токен: HS256, срок 30 минут (`ACCESS_TOKEN_EXPIRE_MINUTES`).  
- Refresh-токен: HS256, срок 7 дней (`REFRESH_TOKEN_EXPIRE_DAYS`).  
- Секретный ключ: переменная окружения `BELPOMOSHNIK_SECRET_KEY` (256-битный случайный ключ в production).  
- **MVP-ограничение:** в `auth.py` стоит дефолтный ключ `"change-me-in-production-use-256-bit-key"` — в production обязательно заменить.

### Персональные данные в БД
- MVP: SQLite-файл `data/belpomoshnik.db` — хранится локально, не реплицируется.  
- Production: PostgreSQL с шифрованием на уровне диска (pgcrypto / LUKS / managed DB).  
- Поля `number`, `issued_by` в таблице `user_documents` в production рекомендуется шифровать симметричным ключом (pgcrypto `pgp_sym_encrypt`).

### Файлы документов (H7)
- Загружаемые файлы хранятся в `data/user_docs/<user_id>/<doc_id>`.  
- Доступ — только через аутентифицированный endpoint `GET /api/user/documents/{doc_id}/file`.  
- **Не** раздаются через статику nginx/Apache.  
- В production: вынести за webroot или использовать S3 с pre-signed URLs.

---

## H8.3 Разграничение доступа (H5/H6)

Роли и права:

| Роль | ID | Доступ |
|------|----|--------|
| Гражданин | `citizen` | Только собственные данные `/api/user/*` |
| Редактор | `content_editor` | + контентные admin-endpoints `/api/admin/*` |
| Администратор | `platform_admin` | Полный доступ + управление пользователями |

Иерархия реализована в `backend.api.auth.require_role()`.  
Все `/api/admin/*` endpoints защищены `Depends(require_role("content_editor"))` на уровне роутера.

---

## H8.4 Транспортный уровень

- Production: HTTPS обязателен (TLS 1.2+).  
- HSTS-заголовок: `Strict-Transport-Security: max-age=31536000`.  
- CORS: в production ограничить список `allow_origins` до домена приложения.  
- MVP: HTTP локально приемлем.

---

## H8.5 Журнал аудита (H9)

- Все create/update/delete действия редактора пишутся в таблицу `audit_logs`.  
- Поля: `actor` (email), `role_id`, `event_type`, `action`, `status`, `created_at`.  
- Endpoint для просмотра: `GET /api/admin/audit-logs` (только platform_admin в production).  
- MVP-ограничение: статус записей — `"ok"` без подробностей об ошибках.

---

## H8.6 Ограничения MVP

| Ограничение | Влияние | Путь решения |
|-------------|---------|--------------|
| Refresh-токены не хранятся в БД | Нельзя отозвать токен до истечения срока | Включить `refresh_tokens` таблицу, проверять `revoked` |
| Единый SECRET_KEY захардкожен | Критично при утечке | Env-переменная + rotation |
| Файлы документов — stub | Нет реального хранилища файлов | S3/MinIO + pre-signed URLs |
| Нет rate limiting | Уязвимость к brute-force | nginx `limit_req` / FastAPI slowapi |
| CORS открыт для всех (`"*"`) | XSS риск | Ограничить origins |
| Нет 2FA | Слабая аутентификация | TOTP после MVP |

---

## H8.7 Генерация безопасного ключа

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Результат (64 hex-символа = 256 бит) записать в:
```bash
export BELPOMOSHNIK_SECRET_KEY="<generated-key>"
```

Или в `.env` (не коммитить в git):
```
BELPOMOSHNIK_SECRET_KEY=<generated-key>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```
