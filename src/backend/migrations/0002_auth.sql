-- H1: Таблицы аутентификации и управления пользователями
-- Совместимо с SQLite (MVP) и PostgreSQL (production).
-- При переходе на PostgreSQL: заменить TEXT → VARCHAR, INTEGER → INT,
--   убрать PRAGMA, добавить SERIAL PRIMARY KEY вместо AUTOINCREMENT.

PRAGMA foreign_keys = ON;

-- Роли пользователей (H5)
CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,                      -- 'citizen', 'content_editor', 'platform_admin'
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR IGNORE INTO roles (id, title, description)
VALUES
    ('citizen',          'Гражданин',        'Обычный пользователь приложения'),
    ('content_editor',   'Редактор',         'Управление сценариями и контентом'),
    ('platform_admin',   'Администратор',    'Полный доступ к платформе');

-- Пользователи (H2, H3, H4, H5)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,            -- bcrypt (H4)
    name TEXT NOT NULL DEFAULT '',
    role_id TEXT NOT NULL DEFAULT 'citizen'
        REFERENCES roles(id) ON DELETE SET DEFAULT,
    city TEXT NOT NULL DEFAULT '',
    region TEXT NOT NULL DEFAULT '',
    district TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    employment_status TEXT NOT NULL DEFAULT '',
    has_children INTEGER NOT NULL DEFAULT 0,
    owns_property INTEGER NOT NULL DEFAULT 0,
    has_car INTEGER NOT NULL DEFAULT 0,
    is_renter INTEGER NOT NULL DEFAULT 0,
    interest_tags TEXT NOT NULL DEFAULT '[]',  -- JSON array
    settings TEXT NOT NULL DEFAULT '{}',       -- JSON dict
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_role ON users(role_id);

-- Refresh-токены (H3)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user ON refresh_tokens(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_refresh_tokens_token ON refresh_tokens(token);

-- Личные документы пользователей (G6)
CREATE TABLE IF NOT EXISTS user_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL DEFAULT '',
    number TEXT NOT NULL DEFAULT '',
    issued_by TEXT NOT NULL DEFAULT '',
    issued_date TEXT NOT NULL DEFAULT '',
    expiry_date TEXT NOT NULL DEFAULT '',
    is_sensitive INTEGER NOT NULL DEFAULT 0,
    comment TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_user_documents_user ON user_documents(user_id);
CREATE INDEX IF NOT EXISTS ix_user_documents_expiry ON user_documents(user_id, expiry_date);

-- Личные ситуации (G5)
CREATE TABLE IF NOT EXISTS user_situations (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'В процессе',
    progress INTEGER NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_user_situations_user ON user_situations(user_id);

-- Задачи ситуаций (G5)
CREATE TABLE IF NOT EXISTS user_situation_tasks (
    id TEXT PRIMARY KEY,
    situation_id TEXT NOT NULL REFERENCES user_situations(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    due_date TEXT NOT NULL DEFAULT '',
    stage_title TEXT NOT NULL DEFAULT '',
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_user_tasks_situation ON user_situation_tasks(situation_id);

-- Уведомления пользователей (G7)
CREATE TABLE IF NOT EXISTS user_notifications (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    notification_type TEXT NOT NULL DEFAULT 'task',
    is_read INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT '',
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_user_notifications_user_read ON user_notifications(user_id, is_read);

-- Email-уведомления и журнал доставки (I2, I4, I5)
CREATE TABLE IF NOT EXISTS email_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    recipient_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    notification_type TEXT NOT NULL DEFAULT 'doc_expiry',
    status TEXT NOT NULL DEFAULT 'pending',   -- pending / sent / failed / skipped_limit
    error_message TEXT NOT NULL DEFAULT '',
    scheduled_at TEXT,
    sent_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_email_notifications_user_status ON email_notifications(user_id, status);
CREATE INDEX IF NOT EXISTS ix_email_notifications_scheduled ON email_notifications(status, scheduled_at);

-- Журнал действий (F7, H9)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL DEFAULT '',
    role_id TEXT NOT NULL DEFAULT 'content_editor',
    event_type TEXT NOT NULL DEFAULT 'other',
    action TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ok',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_role ON audit_logs(role_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_event ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created ON audit_logs(created_at);
