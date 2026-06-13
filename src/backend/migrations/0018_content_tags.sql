-- 0018 — управляемые теги публикаций.
-- Статьи пока хранят выбранные теги JSON-списком строк для обратной
-- совместимости, но справочник задаёт разрешённый набор для редактора.

CREATE TABLE IF NOT EXISTS content_tags (
  id BIGINT NOT NULL AUTO_INCREMENT,
  name VARCHAR(80) NOT NULL,
  slug VARCHAR(120) NOT NULL,
  description VARCHAR(255) NOT NULL DEFAULT '',
  color VARCHAR(32) NOT NULL DEFAULT '',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_content_tags_name (name),
  UNIQUE KEY uq_content_tags_slug (slug),
  KEY ix_content_tags_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO content_tags (name, slug, description, color, is_active) VALUES
('Документы', 'документы', 'Паспорта, справки, заявления и личные документы', '#2563EB', TRUE),
('Семья', 'семья', 'Семейные ситуации, дети, пособия и регистрация актов', '#16A34A', TRUE),
('ЖКХ', 'жкх', 'Коммунальные платежи, жильё и обслуживание дома', '#0EA5E9', TRUE),
('Налоги', 'налоги', 'Налоговые обязательства физических лиц и ИП', '#F59E0B', TRUE),
('Здоровье', 'здоровье', 'Медицинские документы, поликлиники и обслуживание', '#14B8A6', TRUE),
('Работа', 'работа', 'Трудовые вопросы, занятость и справки', '#7C3AED', TRUE),
('Бизнес/ИП', 'бизнес-ип', 'Регистрация ИП, деятельность и отчётность', '#9333EA', TRUE),
('Авто', 'авто', 'Водительские документы, регистрация и страхование', '#0891B2', TRUE),
('Сроки', 'сроки', 'Дедлайны, напоминания и контроль выполнения', '#EF4444', TRUE),
('Пособия', 'пособия', 'Социальные выплаты и заявления', '#22C55E', TRUE),
('Регистрация', 'регистрация', 'Регистрация по месту жительства и учётные действия', '#0F766E', TRUE),
('Закон-апдейт', 'закон-апдейт', 'Изменения законодательства и официальные новости', '#D97706', TRUE),
('Официальный источник', 'официальный-источник', 'Материалы со ссылками на официальные ресурсы', '#475569', TRUE),
('Экстремистские материалы', 'экстремистские-материалы', 'Справочные материалы по официальным реестрам', '#DC2626', TRUE);
