-- Промпт 3 (п.3): пользовательские API-ключи AI-провайдеров.
-- Полный ключ хранится только зашифрованным (Fernet, BELPOMOSHNIK_AI_KEYS_MASTER_KEY).

CREATE TABLE user_ai_provider_credentials (
  id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  provider VARCHAR(40) NOT NULL DEFAULT 'groq',
  encrypted_api_key TEXT NOT NULL,
  masked_key VARCHAR(64) NOT NULL DEFAULT '',
  model VARCHAR(120) NOT NULL DEFAULT '',
  is_enabled TINYINT(1) NOT NULL DEFAULT 1,
  last_checked_at DATETIME NULL,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  KEY ix_user_ai_provider_credentials_user (user_id),
  UNIQUE KEY uq_user_ai_provider (user_id, provider),
  CONSTRAINT fk_user_ai_cred_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
