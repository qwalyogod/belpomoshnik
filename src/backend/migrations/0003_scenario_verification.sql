-- P5: Поля юридической верификации сценариев
-- content_verified_at — дата последней проверки по официальным источникам
-- verified_by         — email/имя редактора, проводившего проверку
-- verification_notes  — комментарий редактора (что проверено, что уточнено)

PRAGMA foreign_keys = ON;

ALTER TABLE scenarios ADD COLUMN content_verified_at TEXT;
ALTER TABLE scenarios ADD COLUMN verified_by TEXT NOT NULL DEFAULT '';
ALTER TABLE scenarios ADD COLUMN verification_notes TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS ix_scenarios_verified ON scenarios(content_verified_at);
