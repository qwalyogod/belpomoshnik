-- Промпт 4 (п.4): порядок сообщений AI-чата берётся по created_at. При мгновенном
-- ответе user- и assistant-сообщения попадают в одну секунду и сортировка
-- становится недетерминированной. Повышаем точность до микросекунд.

ALTER TABLE ai_chat_messages
  MODIFY created_at DATETIME(6) NOT NULL;
