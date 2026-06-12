-- G8/G9: ЖКХ-счета, платежи ЖКХ и налоговые обязательства пользователя
-- MySQL (via pymysql/SQLAlchemy)
CREATE TABLE IF NOT EXISTS utility_accounts (
    id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(255) NOT NULL DEFAULT '',
    account_number VARCHAR(255) NOT NULL DEFAULT '',
    provider VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_utility_accounts_user ON utility_accounts(user_id);

CREATE TABLE IF NOT EXISTS utility_payments (
    id VARCHAR(255) PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL REFERENCES utility_accounts(id) ON DELETE CASCADE,
    period VARCHAR(255) NOT NULL DEFAULT '',
    readings_date VARCHAR(255) NOT NULL DEFAULT '',
    payment_date VARCHAR(255) NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    status VARCHAR(255) NOT NULL DEFAULT 'Ожидает',
    readings_deadline VARCHAR(255) NOT NULL DEFAULT '',
    payment_deadline VARCHAR(255) NOT NULL DEFAULT '',
    comment VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_utility_payments_account ON utility_payments(account_id);

CREATE TABLE IF NOT EXISTS tax_obligations (
    id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_type VARCHAR(255) NOT NULL DEFAULT 'individual',
    title VARCHAR(255) NOT NULL,
    deadline VARCHAR(255) NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    receipt_path VARCHAR(255) NOT NULL DEFAULT '',
    status VARCHAR(255) NOT NULL DEFAULT 'Предстоит',
    period VARCHAR(255) NOT NULL DEFAULT '',
    comment VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_tax_obligations_user ON tax_obligations(user_id);
