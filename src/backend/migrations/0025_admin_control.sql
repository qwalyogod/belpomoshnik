-- Промпт 7: расширенное управление пользователями и аудит админ-панели.

ALTER TABLE users
  ADD COLUMN email_verified TINYINT(1) NOT NULL DEFAULT 0,
  ADD COLUMN last_login_at DATETIME NULL,
  ADD INDEX ix_users_last_login_at (last_login_at);

ALTER TABLE audit_logs
  ADD COLUMN actor_user_id BIGINT NULL AFTER id,
  ADD COLUMN entity_type VARCHAR(80) NOT NULL DEFAULT '' AFTER action,
  ADD COLUMN entity_id VARCHAR(120) NOT NULL DEFAULT '' AFTER entity_type,
  ADD COLUMN before_json TEXT NOT NULL AFTER entity_id,
  ADD COLUMN after_json TEXT NOT NULL AFTER before_json,
  ADD COLUMN ip_address VARCHAR(64) NOT NULL DEFAULT '' AFTER after_json,
  ADD COLUMN user_agent VARCHAR(500) NOT NULL DEFAULT '' AFTER ip_address,
  ADD INDEX ix_audit_logs_actor_user_id (actor_user_id),
  ADD CONSTRAINT fk_audit_logs_actor_user
    FOREIGN KEY (actor_user_id) REFERENCES users (id) ON DELETE SET NULL;

UPDATE audit_logs SET status = 'ok' WHERE status = 'demo';
