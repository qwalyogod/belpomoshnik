-- P5: Поля юридической верификации сценариев
-- content_verified_at — дата последней проверки по официальным источникам
-- verified_by         — email/имя редактора, проводившего проверку
-- verification_notes  — комментарий редактора (что проверено, что уточнено)
ALTER TABLE scenarios ADD COLUMN content_verified_at VARCHAR(255);
ALTER TABLE scenarios ADD COLUMN verified_by VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE scenarios ADD COLUMN verification_notes VARCHAR(255) NOT NULL DEFAULT '';

CREATE INDEX ix_scenarios_verified ON scenarios(content_verified_at);
