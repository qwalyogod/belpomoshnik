-- Посуточный счётчик просмотров материалов для графика дашборда.

CREATE TABLE IF NOT EXISTS article_view_daily (
    day   VARCHAR(10) PRIMARY KEY,
    count BIGINT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
