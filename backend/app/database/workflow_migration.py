from sqlalchemy import text

from app.database.session import engine


STATEMENTS = [
    "ALTER TABLE tenant_interactions ADD COLUMN IF NOT EXISTS problem_category VARCHAR(40)",
    "ALTER TABLE tenant_interactions ADD COLUMN IF NOT EXISTS cancellation_intent VARCHAR(20) NOT NULL DEFAULT 'none'",
    "ALTER TABLE tenant_interactions ADD COLUMN IF NOT EXISTS requested_solution TEXT",
    "ALTER TABLE tenant_interactions ADD COLUMN IF NOT EXISTS reaction VARCHAR(30) NOT NULL DEFAULT 'neutral'",
    "ALTER TABLE tenant_interactions ADD COLUMN IF NOT EXISTS follow_up_required BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE tenant_interactions ADD COLUMN IF NOT EXISTS base_probability DOUBLE PRECISION",
    "ALTER TABLE tenant_interactions ADD COLUMN IF NOT EXISTS operational_probability DOUBLE PRECISION",
    "ALTER TABLE retention_tasks ADD COLUMN IF NOT EXISTS interaction_id INTEGER REFERENCES tenant_interactions(id) ON DELETE SET NULL",
    "ALTER TABLE retention_tasks ADD COLUMN IF NOT EXISTS suggested_action TEXT",
    "ALTER TABLE retention_tasks ADD COLUMN IF NOT EXISTS offer_type VARCHAR(100)",
    "ALTER TABLE retention_tasks ADD COLUMN IF NOT EXISTS offer_cost DOUBLE PRECISION NOT NULL DEFAULT 0",
    "ALTER TABLE retention_tasks ADD COLUMN IF NOT EXISTS offer_duration VARCHAR(80)",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS task_id INTEGER REFERENCES retention_tasks(id) ON DELETE SET NULL",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS interaction_id INTEGER REFERENCES tenant_interactions(id) ON DELETE SET NULL",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS customer_response VARCHAR(40)",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS offer_type VARCHAR(100)",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS offer_cost DOUBLE PRECISION NOT NULL DEFAULT 0",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS offer_duration VARCHAR(80)",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS final_sentiment VARCHAR(20)",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS base_probability DOUBLE PRECISION",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS operational_probability DOUBLE PRECISION",
    "ALTER TABLE retention_outcomes ADD COLUMN IF NOT EXISTS expected_net_value DOUBLE PRECISION NOT NULL DEFAULT 0",
    "CREATE INDEX IF NOT EXISTS ix_retention_tasks_interaction_id ON retention_tasks (interaction_id)",
    "CREATE INDEX IF NOT EXISTS ix_retention_outcomes_task_id ON retention_outcomes (task_id)",
    "CREATE INDEX IF NOT EXISTS ix_retention_outcomes_interaction_id ON retention_outcomes (interaction_id)",
]


def migrate_retention_workflow():
    with engine.begin() as connection:
        for statement in STATEMENTS:
            connection.execute(text(statement))
