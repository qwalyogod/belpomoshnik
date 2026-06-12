-- v1.1 (P4): пользовательские заметки с категорией и сроком напоминания.
-- Отделены от задач ситуаций: это свободные напоминания пользователя,
-- которые показываются на главной и в профиле. CRUD на стороне
-- api/user.py, миграция только описывает таблицу.

CREATE TABLE IF NOT EXISTS user_notes (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    text VARCHAR(1000) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT 'Общее',
    reminder_at VARCHAR(40) NOT NULL DEFAULT '',
    done BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_user_notes_user_id ON user_notes(user_id);
CREATE INDEX ix_user_notes_done ON user_notes(done);
CREATE INDEX ix_user_notes_reminder_at ON user_notes(reminder_at);
