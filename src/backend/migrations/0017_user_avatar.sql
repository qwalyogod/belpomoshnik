-- v1.2: аватар пользователя (Telegram-style редактор: кроп/зум/круг).
-- Обрезанное фото загружается файлом в data/uploads/avatars/<user_id>/<token>.<ext>,
-- в БД храним публичный путь вида /uploads/avatars/<user_id>/<token>.webp.
-- Пустая строка = аватар не задан (UI показывает инициал).

ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255) NOT NULL DEFAULT '';
