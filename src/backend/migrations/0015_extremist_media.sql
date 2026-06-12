-- P7: таблица и медиа для раздела «Экстремистские материалы».
-- Миграция совместима и с чистой базой, и с базой, где таблица была
-- создана через SQLAlchemy без media-колонок.

CREATE TABLE IF NOT EXISTS extremist_entries (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title               VARCHAR(255)  NOT NULL,
    category            VARCHAR(32)   NOT NULL DEFAULT 'registry',
    source_url          VARCHAR(1000) NOT NULL,
    source_name         VARCHAR(255)  NOT NULL DEFAULT '',
    included_at         TIMESTAMP,
    last_checked_at     TIMESTAMP,
    short_description   VARCHAR(255)          NOT NULL DEFAULT '',
    cover_url           VARCHAR(1000) NOT NULL DEFAULT '',
    media_urls          VARCHAR(255)          NOT NULL DEFAULT '[]',
    attachment_urls     VARCHAR(255)          NOT NULL DEFAULT '[]',
    filters_json        VARCHAR(255)          NOT NULL DEFAULT '{}',
    status              VARCHAR(16)   NOT NULL DEFAULT 'draft',
    created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE extremist_entries_v2 (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title               VARCHAR(255)  NOT NULL,
    category            VARCHAR(32)   NOT NULL DEFAULT 'registry',
    source_url          VARCHAR(1000) NOT NULL,
    source_name         VARCHAR(255)  NOT NULL DEFAULT '',
    included_at         TIMESTAMP,
    last_checked_at     TIMESTAMP,
    short_description   VARCHAR(255)          NOT NULL DEFAULT '',
    cover_url           VARCHAR(1000) NOT NULL DEFAULT '',
    media_urls          VARCHAR(255)          NOT NULL DEFAULT '[]',
    attachment_urls     VARCHAR(255)          NOT NULL DEFAULT '[]',
    filters_json        VARCHAR(255)          NOT NULL DEFAULT '{}',
    status              VARCHAR(16)   NOT NULL DEFAULT 'draft',
    created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO extremist_entries_v2 (
    id,
    title,
    category,
    source_url,
    source_name,
    included_at,
    last_checked_at,
    short_description,
    filters_json,
    status,
    created_at,
    updated_at
)
SELECT
    id,
    title,
    category,
    source_url,
    source_name,
    included_at,
    last_checked_at,
    short_description,
    filters_json,
    status,
    created_at,
    updated_at
FROM extremist_entries;

DROP TABLE extremist_entries;
ALTER TABLE extremist_entries_v2 RENAME TO extremist_entries;

CREATE INDEX ix_extremist_entries_status ON extremist_entries(status);
CREATE INDEX ix_extremist_entries_category ON extremist_entries(category);
