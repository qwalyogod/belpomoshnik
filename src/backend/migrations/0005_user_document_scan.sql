-- A: путь к зашифрованному скану личного документа (для Client->API wiring).
-- MySQL (via pymysql/SQLAlchemy)

ALTER TABLE user_documents ADD COLUMN scan_path VARCHAR(255) NOT NULL DEFAULT '';
