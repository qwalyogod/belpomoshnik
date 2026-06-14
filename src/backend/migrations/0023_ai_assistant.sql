-- Промпт 3: AI-чат с историей. Sessions + messages.

CREATE TABLE ai_chat_sessions (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  title VARCHAR(255) NOT NULL DEFAULT '',
  mode VARCHAR(16) NOT NULL DEFAULT 'citizen',
  archived TINYINT(1) NOT NULL DEFAULT 0,
  last_message_preview VARCHAR(255) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL,
  KEY ix_ai_chat_sessions_user (user_id),
  CONSTRAINT fk_ai_chat_sessions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ai_chat_messages (
  id VARCHAR(64) NOT NULL PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  role VARCHAR(16) NOT NULL DEFAULT 'user',
  content TEXT NOT NULL,
  links_json TEXT NOT NULL,
  actions_json TEXT NOT NULL,
  sources_json TEXT NOT NULL,
  source VARCHAR(16) NOT NULL DEFAULT 'llm',
  model VARCHAR(120) NOT NULL DEFAULT '',
  provider VARCHAR(40) NOT NULL DEFAULT '',
  error_code VARCHAR(40) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL,
  KEY ix_ai_chat_messages_session (session_id),
  CONSTRAINT fk_ai_chat_messages_session FOREIGN KEY (session_id) REFERENCES ai_chat_sessions (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
