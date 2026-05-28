PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    short_description TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_problems_slug ON problems(slug);
CREATE INDEX IF NOT EXISTS ix_problems_status ON problems(status);

CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    problem_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    short_description TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    target_audience TEXT NOT NULL DEFAULT '',
    estimated_duration TEXT NOT NULL DEFAULT '',
    difficulty_level TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'draft',
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(problem_id) REFERENCES problems(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_scenarios_slug ON scenarios(slug);
CREATE INDEX IF NOT EXISTS ix_scenarios_status ON scenarios(status);
CREATE INDEX IF NOT EXISTS ix_scenarios_problem_id_status ON scenarios(problem_id, status);

CREATE TABLE IF NOT EXISTS scenario_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    order_index INTEGER NOT NULL DEFAULT 0,
    is_required INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_scenario_stages_scenario_order ON scenario_stages(scenario_id, order_index);

CREATE TABLE IF NOT EXISTS authorities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    website_url TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    working_hours TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    duration_value INTEGER NOT NULL DEFAULT 0,
    duration_unit TEXT NOT NULL DEFAULT 'days',
    is_business_days INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    document_type TEXT NOT NULL DEFAULT '',
    is_required INTEGER NOT NULL DEFAULT 1,
    where_to_get TEXT NOT NULL DEFAULT '',
    validity_period TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_documents_status ON documents(status);

CREATE TABLE IF NOT EXISTS scenario_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stage_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    order_index INTEGER NOT NULL DEFAULT 0,
    action_type TEXT NOT NULL DEFAULT 'info',
    authority_id INTEGER NULL,
    deadline_id INTEGER NULL,
    is_required INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(stage_id) REFERENCES scenario_stages(id) ON DELETE CASCADE,
    FOREIGN KEY(authority_id) REFERENCES authorities(id) ON DELETE SET NULL,
    FOREIGN KEY(deadline_id) REFERENCES deadlines(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_scenario_steps_stage_order ON scenario_steps(stage_id, order_index);

CREATE TABLE IF NOT EXISTS scenario_step_documents (
    step_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(step_id, document_id),
    FOREIGN KEY(step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notification_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    notify_before_days INTEGER NOT NULL DEFAULT 0,
    notification_type TEXT NOT NULL DEFAULT 'reminder',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scenario_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    step_id INTEGER NOT NULL,
    depends_on_step_id INTEGER NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY(step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE,
    FOREIGN KEY(depends_on_step_id) REFERENCES scenario_steps(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS ix_scenario_dependencies_scenario ON scenario_dependencies(scenario_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_scenario_dependency_pair ON scenario_dependencies(step_id, depends_on_step_id);

CREATE TABLE IF NOT EXISTS related_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    related_scenario_id INTEGER NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'related_problem',
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY(related_scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_related_scenario ON related_scenarios(scenario_id, related_scenario_id, relation_type);

CREATE TABLE IF NOT EXISTS source_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sourceable_type TEXT NOT NULL,
    sourceable_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'other',
    description TEXT NOT NULL DEFAULT '',
    last_checked_at TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_source_references_sourceable ON source_references(sourceable_type, sourceable_id);

CREATE TABLE IF NOT EXISTS law_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    affected_scenario_id INTEGER NULL,
    affected_step_id INTEGER NULL,
    update_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(affected_scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL,
    FOREIGN KEY(affected_step_id) REFERENCES scenario_steps(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS ix_law_updates_status ON law_updates(status);
CREATE INDEX IF NOT EXISTS ix_law_updates_scenario_step ON law_updates(affected_scenario_id, affected_step_id);

