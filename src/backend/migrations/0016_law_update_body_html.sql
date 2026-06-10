-- Закон-апдейты как полноценные статьи: HTML-тело материала.

ALTER TABLE law_updates ADD COLUMN body_html TEXT NOT NULL DEFAULT '';
