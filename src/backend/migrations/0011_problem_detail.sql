-- Rich «что делать» content for problems (ported from Flet PROBLEM_DETAIL).

ALTER TABLE problems ADD COLUMN what_to_do_now VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE problems ADD COLUMN steps_json VARCHAR(255) NOT NULL DEFAULT '[]';
ALTER TABLE problems ADD COLUMN documents_json VARCHAR(255) NOT NULL DEFAULT '[]';
ALTER TABLE problems ADD COLUMN deadlines_json VARCHAR(255) NOT NULL DEFAULT '[]';
ALTER TABLE problems ADD COLUMN institutions_json VARCHAR(255) NOT NULL DEFAULT '[]';
ALTER TABLE problems ADD COLUMN mistakes_json VARCHAR(255) NOT NULL DEFAULT '[]';
