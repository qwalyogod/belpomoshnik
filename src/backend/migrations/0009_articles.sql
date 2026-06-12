-- K-этап: редакторские и пользовательские публикации + блок-лист предложений.

CREATE TABLE IF NOT EXISTS articles (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    kind           VARCHAR(16)  NOT NULL DEFAULT 'news',
    title          VARCHAR(255) NOT NULL DEFAULT '',
    summary        VARCHAR(255)         NOT NULL DEFAULT '',
    body_html      VARCHAR(255)         NOT NULL DEFAULT '',
    cover          VARCHAR(1000) NOT NULL DEFAULT '',
    video          VARCHAR(1000) NOT NULL DEFAULT '',
    gallery        VARCHAR(255)         NOT NULL DEFAULT '[]',
    tags           VARCHAR(255)         NOT NULL DEFAULT '[]',
    category       VARCHAR(255) NOT NULL DEFAULT '',
    specialization VARCHAR(255) NOT NULL DEFAULT '',
    audience       VARCHAR(64)  NOT NULL DEFAULT 'all',
    source         VARCHAR(255) NOT NULL DEFAULT '',
    source_url     VARCHAR(1000) NOT NULL DEFAULT '',
    status         VARCHAR(16)  NOT NULL DEFAULT 'draft',
    author_name    VARCHAR(255) NOT NULL DEFAULT '',
    author_role    VARCHAR(32)  NOT NULL DEFAULT 'editor',
    proposed_by    VARCHAR(255) NOT NULL DEFAULT '',
    proposer_id    BIGINT      REFERENCES users(id) ON DELETE SET NULL,
    anonymous      BOOLEAN      NOT NULL DEFAULT 0,
    reported       BOOLEAN      NOT NULL DEFAULT 0,
    publish_date   VARCHAR(32)  NOT NULL DEFAULT '',
    views          BIGINT      NOT NULL DEFAULT 0,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_articles_status ON articles (status);
CREATE INDEX ix_articles_kind_status ON articles (kind, status);
CREATE INDEX ix_articles_proposer ON articles (proposer_id);

CREATE TABLE IF NOT EXISTS blocked_submitters (
    user_id    BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    blocked_by VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
