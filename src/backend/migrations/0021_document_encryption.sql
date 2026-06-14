-- Промпт 1: шифрование чувствительных полей и сканов «Моих документов».
-- Старые plain-колонки (number, issued_by, comment, custom_fields_json, scan_path)
-- НЕ удаляем — read-путь умеет fallback. После заполнения encrypted-колонок
-- plain-значения остаются пустыми (write-путь пишет только в encrypted).

ALTER TABLE user_documents
  ADD COLUMN number_encrypted TEXT NULL,
  ADD COLUMN issued_by_encrypted TEXT NULL,
  ADD COLUMN comment_encrypted MEDIUMTEXT NULL,
  ADD COLUMN custom_fields_encrypted MEDIUMTEXT NULL,
  ADD COLUMN scan_encrypted_path VARCHAR(500) NOT NULL DEFAULT '',
  ADD COLUMN scan_original_filename VARCHAR(255) NOT NULL DEFAULT '',
  ADD COLUMN scan_mime_type VARCHAR(120) NOT NULL DEFAULT '',
  ADD COLUMN scan_size INT NOT NULL DEFAULT 0,
  ADD COLUMN scan_uploaded_at DATETIME NULL;
