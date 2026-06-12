-- §14: регион/город учреждения для подбора по профилю пользователя.
-- MySQL (via pymysql/SQLAlchemy)

ALTER TABLE authorities ADD COLUMN region VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE authorities ADD COLUMN city VARCHAR(255) NOT NULL DEFAULT '';
