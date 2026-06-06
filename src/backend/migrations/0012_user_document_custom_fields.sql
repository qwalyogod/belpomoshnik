-- v0.4: пользовательские поля для doc_type='other' в user_documents.
-- Хранятся как JSON-строка массива [{"name": "...", "value": "..."}, ...].

ALTER TABLE user_documents ADD COLUMN custom_fields_json VARCHAR(2000) NOT NULL DEFAULT '';
