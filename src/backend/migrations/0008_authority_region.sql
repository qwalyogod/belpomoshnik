-- §14: регион/город учреждения для подбора по профилю пользователя.
-- SQLite (MVP). PostgreSQL получает колонки через backend.bootstrap (create_all).

ALTER TABLE authorities ADD COLUMN region TEXT NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN city TEXT NOT NULL DEFAULT '';
