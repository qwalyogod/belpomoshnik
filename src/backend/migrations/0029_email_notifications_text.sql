-- Фикс: тело письма не помещалось в VARCHAR(255) (из старой миграции 0002),
-- что давало DataError 1406 "Data too long for column 'body'". Приводим к модели:
-- body/error_message → TEXT, subject → VARCHAR(500).

ALTER TABLE email_notifications
  MODIFY subject VARCHAR(500) NOT NULL,
  MODIFY body TEXT NOT NULL,
  MODIFY error_message TEXT NOT NULL;
