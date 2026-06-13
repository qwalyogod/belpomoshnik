-- Промпт 6: dedupe_key и route в UserNotification + UserPushToken для native push.

ALTER TABLE user_notifications
  ADD COLUMN route VARCHAR(255) NOT NULL DEFAULT '',
  ADD COLUMN dedupe_key VARCHAR(255) NOT NULL DEFAULT '',
  ADD INDEX ix_user_notifications_dedupe (user_id, dedupe_key);

CREATE TABLE user_push_tokens (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  platform VARCHAR(16) NOT NULL DEFAULT 'android',
  token_hash VARCHAR(120) NOT NULL,
  token_encrypted TEXT NOT NULL,
  device_label VARCHAR(120) NOT NULL DEFAULT '',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  last_seen_at DATETIME NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  KEY ix_user_push_tokens_user (user_id),
  UNIQUE KEY uq_user_push_tokens_hash (user_id, token_hash),
  CONSTRAINT fk_user_push_tokens_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
