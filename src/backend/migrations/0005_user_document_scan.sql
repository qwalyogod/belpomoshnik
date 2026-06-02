-- A: путь к зашифрованному скану личного документа (для Client->API wiring).
-- SQLite (MVP). PostgreSQL получает колонку через backend.bootstrap (create_all).

ALTER TABLE user_documents ADD COLUMN scan_path TEXT NOT NULL DEFAULT '';
