-- 0019 — расширенные поля учреждений для полного справочника Беларуси.
-- Данные приходят из data/import/*institutions*.json и используются для
-- подбора «Куда обращаться» по адресу пользователя.

ALTER TABLE authorities MODIFY COLUMN description TEXT NOT NULL;
ALTER TABLE authorities MODIFY COLUMN website_url VARCHAR(500) NOT NULL DEFAULT '';
ALTER TABLE authorities MODIFY COLUMN address VARCHAR(500) NOT NULL DEFAULT '';

ALTER TABLE authorities ADD COLUMN external_id VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN district VARCHAR(120) NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN settlement VARCHAR(120) NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN email VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN services_json TEXT NULL;
ALTER TABLE authorities ADD COLUMN tags_json TEXT NULL;
ALTER TABLE authorities ADD COLUMN related_scenario_categories_json TEXT NULL;
ALTER TABLE authorities ADD COLUMN related_scenarios_json TEXT NULL;
ALTER TABLE authorities ADD COLUMN source_ids_json TEXT NULL;
ALTER TABLE authorities ADD COLUMN source_urls_json TEXT NULL;
ALTER TABLE authorities ADD COLUMN last_checked_at VARCHAR(40) NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN confidence VARCHAR(40) NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN notes TEXT NOT NULL;
ALTER TABLE authorities ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE authorities SET
    services_json = '[]',
    tags_json = '[]',
    related_scenario_categories_json = '[]',
    related_scenarios_json = '[]',
    source_ids_json = '[]',
    source_urls_json = '[]'
WHERE services_json IS NULL
   OR tags_json IS NULL
   OR related_scenario_categories_json IS NULL
   OR related_scenarios_json IS NULL
   OR source_ids_json IS NULL
   OR source_urls_json IS NULL;

ALTER TABLE authorities MODIFY COLUMN services_json TEXT NOT NULL;
ALTER TABLE authorities MODIFY COLUMN tags_json TEXT NOT NULL;
ALTER TABLE authorities MODIFY COLUMN related_scenario_categories_json TEXT NOT NULL;
ALTER TABLE authorities MODIFY COLUMN related_scenarios_json TEXT NOT NULL;
ALTER TABLE authorities MODIFY COLUMN source_ids_json TEXT NOT NULL;
ALTER TABLE authorities MODIFY COLUMN source_urls_json TEXT NOT NULL;

CREATE INDEX ix_authorities_external_id ON authorities(external_id);
CREATE INDEX ix_authorities_type ON authorities(type);
CREATE INDEX ix_authorities_region_city ON authorities(region, city);
CREATE INDEX ix_authorities_region_district ON authorities(region, district);
