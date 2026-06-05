-- Посуточный счётчик просмотров материалов для графика дашборда.

CREATE TABLE IF NOT EXISTS article_view_daily (
    day   VARCHAR(10) PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0
);
