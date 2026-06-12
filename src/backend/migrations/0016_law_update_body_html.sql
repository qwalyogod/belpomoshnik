-- Закон-апдейты как полноценные статьи: HTML-тело материала.

ALTER TABLE law_updates ADD COLUMN body_html VARCHAR(255) NOT NULL DEFAULT '';
