-- 0006: флаг тестовых аккаунтов
-- Используется переключателем ролей в UI (показывает только пользователей с is_test_account=1).
-- Production: отключить переключатель через env-флаг или скрыть endpoint.

ALTER TABLE users ADD COLUMN is_test_account INTEGER NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS ix_users_is_test_account ON users(is_test_account);
