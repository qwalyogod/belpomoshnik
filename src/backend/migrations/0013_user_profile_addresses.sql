-- v1.1 (P4): адреса пользователя (до 5 шт.) хранятся как JSON-строка массива
-- [{"id": "...", "label": "...", "region": "...", "district": "...",
--   "city": "...", "street": "...", "isPrimary": true|false}, ...].
-- Лимит 2000 символов на стороне БД; валидация — в api/user.py.

ALTER TABLE users ADD COLUMN addresses_json VARCHAR(2000) NOT NULL DEFAULT '[]';
