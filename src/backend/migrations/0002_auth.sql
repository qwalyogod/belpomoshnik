-- H1: Таблицы аутентификации и управления пользователями
-- Совместимо с SQLite (MVP) и PostgreSQL (production).
-- При переходе на PostgreSQL: заменить VARCHAR(255) → VARCHAR, BIGINT → INT,
-- (auto-converted to AUTO_INCREMENT)
-- Роли пользователей (H5)
CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(255) PRIMARY KEY,                      -- 'citizen', 'content_editor', 'platform_admin'
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO roles (id, title, description)
VALUES
    ('citizen',          'Гражданин',        'Обычный пользователь приложения'),
    ('content_editor',   'Редактор',         'Управление сценариями и контентом'),
    ('platform_admin',   'Администратор',    'Полный доступ к платформе');

-- Пользователи (H2, H3, H4, H5)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,            -- bcrypt (H4)
    name VARCHAR(255) NOT NULL DEFAULT '',
    role_id VARCHAR(255) NOT NULL DEFAULT 'citizen'
        REFERENCES roles(id) ON DELETE RESTRICT,
    city VARCHAR(255) NOT NULL DEFAULT '',
    region VARCHAR(255) NOT NULL DEFAULT '',
    district VARCHAR(255) NOT NULL DEFAULT '',
    address VARCHAR(255) NOT NULL DEFAULT '',
    employment_status VARCHAR(255) NOT NULL DEFAULT '',
    has_children BIGINT NOT NULL DEFAULT 0,
    owns_property BIGINT NOT NULL DEFAULT 0,
    has_car BIGINT NOT NULL DEFAULT 0,
    is_renter BIGINT NOT NULL DEFAULT 0,
    interest_tags VARCHAR(255) NOT NULL DEFAULT '[]',  -- JSON array
    settings VARCHAR(255) NOT NULL DEFAULT '{}',       -- JSON dict
    is_active BIGINT NOT NULL DEFAULT 1,
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE UNIQUE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_role ON users(role_id);

-- Refresh-токены (H3)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL,
    expires_at VARCHAR(255) NOT NULL,
    revoked BIGINT NOT NULL DEFAULT 0,
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_refresh_tokens_user ON refresh_tokens(user_id);
CREATE UNIQUE INDEX ix_refresh_tokens_token ON refresh_tokens(token);

-- Личные документы пользователей (G6)
CREATE TABLE IF NOT EXISTS user_documents (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    doc_type VARCHAR(255) NOT NULL DEFAULT '',
    number VARCHAR(255) NOT NULL DEFAULT '',
    issued_by VARCHAR(255) NOT NULL DEFAULT '',
    issued_date VARCHAR(255) NOT NULL DEFAULT '',
    expiry_date VARCHAR(255) NOT NULL DEFAULT '',
    is_sensitive BIGINT NOT NULL DEFAULT 0,
    comment VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_user_documents_user ON user_documents(user_id);
CREATE INDEX ix_user_documents_expiry ON user_documents(user_id, expiry_date);

-- Личные ситуации (G5)
CREATE TABLE IF NOT EXISTS user_situations (
    id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'В процессе',
    progress BIGINT NOT NULL DEFAULT 0,
    category VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_user_situations_user ON user_situations(user_id);

-- Задачи ситуаций (G5)
CREATE TABLE IF NOT EXISTS user_situation_tasks (
    id VARCHAR(255) PRIMARY KEY,
    situation_id VARCHAR(255) NOT NULL REFERENCES user_situations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    completed BIGINT NOT NULL DEFAULT 0,
    due_date VARCHAR(255) NOT NULL DEFAULT '',
    stage_title VARCHAR(255) NOT NULL DEFAULT '',
    order_index BIGINT NOT NULL DEFAULT 0,
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_user_tasks_situation ON user_situation_tasks(situation_id);

-- Уведомления пользователей (G7)
CREATE TABLE IF NOT EXISTS user_notifications (
    id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    notification_type VARCHAR(255) NOT NULL DEFAULT 'task',
    is_read BIGINT NOT NULL DEFAULT 0,
    source VARCHAR(255) NOT NULL DEFAULT '',
    due_date VARCHAR(255),
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_user_notifications_user_read ON user_notifications(user_id, is_read);

-- Email-уведомления и журнал доставки (I2, I4, I5)
CREATE TABLE IF NOT EXISTS email_notifications (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body VARCHAR(255) NOT NULL DEFAULT '',
    notification_type VARCHAR(255) NOT NULL DEFAULT 'doc_expiry',
    status VARCHAR(255) NOT NULL DEFAULT 'pending',   -- pending / sent / failed / skipped_limit
    error_message VARCHAR(255) NOT NULL DEFAULT '',
    scheduled_at VARCHAR(255),
    sent_at VARCHAR(255),
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_email_notifications_user_status ON email_notifications(user_id, status);
CREATE INDEX ix_email_notifications_scheduled ON email_notifications(status, scheduled_at);

-- Журнал действий (F7, H9)
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    actor VARCHAR(255) NOT NULL DEFAULT '',
    role_id VARCHAR(255) NOT NULL DEFAULT 'content_editor',
    event_type VARCHAR(255) NOT NULL DEFAULT 'other',
    action VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'ok',
    created_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    updated_at VARCHAR(255) NOT NULL DEFAULT (CURRENT_TIMESTAMP)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_audit_logs_role ON audit_logs(role_id);
CREATE INDEX ix_audit_logs_event ON audit_logs(event_type);
CREATE INDEX ix_audit_logs_created ON audit_logs(created_at);
