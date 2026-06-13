-- Промпт 2: «ЖКХ и налоги» v2 — расширенные поля + заявки 115.

-- UtilityAccount: пользовательская подпись, услуги, плательщик, manualMode.
ALTER TABLE utility_accounts
  ADD COLUMN label VARCHAR(120) NOT NULL DEFAULT '',
  ADD COLUMN service_types VARCHAR(500) NOT NULL DEFAULT '[]',
  ADD COLUMN payer_name VARCHAR(255) NOT NULL DEFAULT '',
  ADD COLUMN manual_mode TINYINT(1) NOT NULL DEFAULT 1,
  ADD COLUMN last_sync_note VARCHAR(500) NOT NULL DEFAULT '';

-- UtilityPayment: breakdown, источник, квитанция.
ALTER TABLE utility_payments
  ADD COLUMN breakdown_json TEXT NOT NULL,
  ADD COLUMN source VARCHAR(32) NOT NULL DEFAULT 'manual',
  ADD COLUMN receipt_path VARCHAR(500) NOT NULL DEFAULT '';

-- TaxObligation: тип налога, источник, реквизиты, helpText.
ALTER TABLE tax_obligations
  ADD COLUMN tax_type VARCHAR(40) NOT NULL DEFAULT 'other',
  ADD COLUMN source VARCHAR(32) NOT NULL DEFAULT 'manual',
  ADD COLUMN recipient VARCHAR(255) NOT NULL DEFAULT '',
  ADD COLUMN unp VARCHAR(40) NOT NULL DEFAULT '',
  ADD COLUMN notice_number VARCHAR(80) NOT NULL DEFAULT '',
  ADD COLUMN payment_code VARCHAR(80) NOT NULL DEFAULT '',
  ADD COLUMN paid_at VARCHAR(20) NOT NULL DEFAULT '',
  ADD COLUMN external_url VARCHAR(500) NOT NULL DEFAULT '',
  ADD COLUMN help_text VARCHAR(500) NOT NULL DEFAULT '';

-- Заявки 115 — новая таблица.
CREATE TABLE utility_requests (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  account_id VARCHAR(64) NULL,
  address VARCHAR(500) NOT NULL DEFAULT '',
  title VARCHAR(255) NOT NULL,
  category VARCHAR(40) NOT NULL DEFAULT 'other',
  description TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'draft',
  external_number VARCHAR(80) NOT NULL DEFAULT '',
  external_url VARCHAR(500) NOT NULL DEFAULT '',
  target_service VARCHAR(80) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  KEY ix_utility_requests_user (user_id),
  KEY ix_utility_requests_account (account_id),
  KEY ix_utility_requests_status (status),
  CONSTRAINT fk_utility_requests_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_utility_requests_account FOREIGN KEY (account_id) REFERENCES utility_accounts (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
