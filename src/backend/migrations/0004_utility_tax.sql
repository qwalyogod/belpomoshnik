-- G8/G9: ЖКХ-счета, платежи ЖКХ и налоговые обязательства пользователя
-- SQLite (MVP). Для PostgreSQL схема создаётся через backend.bootstrap.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS utility_accounts (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address TEXT NOT NULL DEFAULT '',
    account_number TEXT NOT NULL DEFAULT '',
    provider TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_utility_accounts_user ON utility_accounts(user_id);

CREATE TABLE IF NOT EXISTS utility_payments (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES utility_accounts(id) ON DELETE CASCADE,
    period TEXT NOT NULL DEFAULT '',
    readings_date TEXT NOT NULL DEFAULT '',
    payment_date TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Ожидает',
    readings_deadline TEXT NOT NULL DEFAULT '',
    payment_deadline TEXT NOT NULL DEFAULT '',
    comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_utility_payments_account ON utility_payments(account_id);

CREATE TABLE IF NOT EXISTS tax_obligations (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_type TEXT NOT NULL DEFAULT 'individual',
    title TEXT NOT NULL,
    deadline TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    receipt_path TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Предстоит',
    period TEXT NOT NULL DEFAULT '',
    comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_tax_obligations_user ON tax_obligations(user_id);
