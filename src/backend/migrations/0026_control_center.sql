-- Скрытый Control Center: сессии владельца, системные настройки и отдельный журнал.

CREATE TABLE IF NOT EXISTS control_center_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    token_hash VARCHAR(128) NOT NULL,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    revoked_at DATETIME NULL,
    last_used_at DATETIME NULL,
    ip_address VARCHAR(64) NOT NULL DEFAULT '',
    user_agent VARCHAR(500) NOT NULL DEFAULT '',
    CONSTRAINT uq_control_center_sessions_token_hash UNIQUE (token_hash)
);

CREATE INDEX ix_control_center_sessions_expires
    ON control_center_sessions (expires_at, revoked_at);

CREATE TABLE IF NOT EXISTS system_settings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    `key` VARCHAR(120) NOT NULL,
    value_json LONGTEXT NOT NULL,
    updated_by VARCHAR(255) NOT NULL DEFAULT 'control-center',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    CONSTRAINT uq_system_settings_key UNIQUE (`key`)
);

CREATE INDEX ix_system_settings_key ON system_settings (`key`);

CREATE TABLE IF NOT EXISTS control_center_audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id BIGINT NULL,
    action VARCHAR(120) NOT NULL,
    entity_type VARCHAR(80) NOT NULL DEFAULT '',
    entity_id VARCHAR(120) NOT NULL DEFAULT '',
    before_json LONGTEXT NOT NULL,
    after_json LONGTEXT NOT NULL,
    ip_address VARCHAR(64) NOT NULL DEFAULT '',
    user_agent VARCHAR(500) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'ok',
    created_at DATETIME NOT NULL,
    CONSTRAINT fk_control_center_audit_logs_session
        FOREIGN KEY (session_id) REFERENCES control_center_sessions(id)
        ON DELETE SET NULL
);

CREATE INDEX ix_control_center_audit_logs_created
    ON control_center_audit_logs (created_at);

CREATE INDEX ix_control_center_audit_logs_action
    ON control_center_audit_logs (action);
