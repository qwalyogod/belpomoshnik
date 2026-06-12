CREATE TABLE IF NOT EXISTS problems (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    short_description VARCHAR(255) NOT NULL DEFAULT '',
    description VARCHAR(255) NOT NULL DEFAULT '',
    icon VARCHAR(255) NOT NULL DEFAULT '',
    category VARCHAR(255) NOT NULL DEFAULT '',
    status VARCHAR(255) NOT NULL DEFAULT 'draft',
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_problems_slug ON problems(slug);
CREATE INDEX ix_problems_status ON problems(status);

CREATE TABLE IF NOT EXISTS scenarios (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    problem_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    short_description VARCHAR(255) NOT NULL DEFAULT '',
    description VARCHAR(255) NOT NULL DEFAULT '',
    target_audience VARCHAR(255) NOT NULL DEFAULT '',
    estimated_duration VARCHAR(255) NOT NULL DEFAULT '',
    difficulty_level VARCHAR(255) NOT NULL DEFAULT 'medium',
    status VARCHAR(255) NOT NULL DEFAULT 'draft',
    priority BIGINT NOT NULL DEFAULT 0,
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL,
    FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_scenarios_slug ON scenarios(slug);
CREATE INDEX ix_scenarios_status ON scenarios(status);
CREATE INDEX ix_scenarios_problem_id_status ON scenarios(problem_id, status);

CREATE TABLE IF NOT EXISTS scenario_stages (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    scenario_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    order_index BIGINT NOT NULL DEFAULT 0,
    is_required BIGINT NOT NULL DEFAULT 1,
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL,
    FOREIGN KEY(scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_scenario_stages_scenario_order ON scenario_stages(scenario_id, order_index);

CREATE TABLE IF NOT EXISTS authorities (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    website_url VARCHAR(255) NOT NULL DEFAULT '',
    phone VARCHAR(255) NOT NULL DEFAULT '',
    address VARCHAR(255) NOT NULL DEFAULT '',
    working_hours VARCHAR(255) NOT NULL DEFAULT '',
    type VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS deadlines (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    duration_value BIGINT NOT NULL DEFAULT 0,
    duration_unit VARCHAR(255) NOT NULL DEFAULT 'days',
    is_business_days BIGINT NOT NULL DEFAULT 0,
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS documents (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    document_type VARCHAR(255) NOT NULL DEFAULT '',
    is_required BIGINT NOT NULL DEFAULT 1,
    where_to_get VARCHAR(255) NOT NULL DEFAULT '',
    validity_period VARCHAR(255) NOT NULL DEFAULT '',
    status VARCHAR(255) NOT NULL DEFAULT 'draft',
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_documents_status ON documents(status);

CREATE TABLE IF NOT EXISTS scenario_steps (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    stage_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    order_index BIGINT NOT NULL DEFAULT 0,
    action_type VARCHAR(255) NOT NULL DEFAULT 'info',
    authority_id BIGINT NULL,
    deadline_id BIGINT NULL,
    is_required BIGINT NOT NULL DEFAULT 1,
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL,
    FOREIGN KEY(stage_id) REFERENCES scenario_stages(id) ON DELETE CASCADE,
    FOREIGN KEY(authority_id) REFERENCES authorities(id) ON DELETE SET NULL,
    FOREIGN KEY(deadline_id) REFERENCES deadlines(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_scenario_steps_stage_order ON scenario_steps(stage_id, order_index);

CREATE TABLE IF NOT EXISTS scenario_step_documents (
    step_id BIGINT NOT NULL,
    document_id BIGINT NOT NULL,
    created_at VARCHAR(255) NOT NULL,
    PRIMARY KEY(step_id, document_id),
    FOREIGN KEY(step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notification_rules (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    step_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message VARCHAR(255) NOT NULL DEFAULT '',
    notify_before_days BIGINT NOT NULL DEFAULT 0,
    notification_type VARCHAR(255) NOT NULL DEFAULT 'reminder',
    is_active BIGINT NOT NULL DEFAULT 1,
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL,
    FOREIGN KEY(step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS scenario_dependencies (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    scenario_id BIGINT NOT NULL,
    step_id BIGINT NOT NULL,
    depends_on_step_id BIGINT NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL,
    FOREIGN KEY(scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY(step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE,
    FOREIGN KEY(depends_on_step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_scenario_dependencies_scenario ON scenario_dependencies(scenario_id);
CREATE UNIQUE INDEX uq_scenario_dependency_pair ON scenario_dependencies(step_id, depends_on_step_id);

CREATE TABLE IF NOT EXISTS related_scenarios (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    scenario_id BIGINT NOT NULL,
    related_scenario_id BIGINT NOT NULL,
    relation_type VARCHAR(255) NOT NULL DEFAULT 'related_problem',
    description VARCHAR(255) NOT NULL DEFAULT '',
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL,
    FOREIGN KEY(scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY(related_scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE UNIQUE INDEX uq_related_scenario ON related_scenarios(scenario_id, related_scenario_id, relation_type);

CREATE TABLE IF NOT EXISTS source_references (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sourceable_type VARCHAR(255) NOT NULL,
    sourceable_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL,
    source_type VARCHAR(255) NOT NULL DEFAULT 'other',
    description VARCHAR(255) NOT NULL DEFAULT '',
    last_checked_at VARCHAR(255) NULL,
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_source_references_sourceable ON source_references(sourceable_type, sourceable_id);

CREATE TABLE IF NOT EXISTS law_updates (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    source_url VARCHAR(255) NOT NULL DEFAULT '',
    affected_scenario_id BIGINT NULL,
    affected_step_id BIGINT NULL,
    update_date VARCHAR(255) NOT NULL,
    status VARCHAR(255) NOT NULL DEFAULT 'new',
    created_at VARCHAR(255) NOT NULL,
    updated_at VARCHAR(255) NOT NULL,
    FOREIGN KEY(affected_scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL,
    FOREIGN KEY(affected_step_id) REFERENCES scenario_steps(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE INDEX ix_law_updates_status ON law_updates(status);
CREATE INDEX ix_law_updates_scenario_step ON law_updates(affected_scenario_id, affected_step_id);

