from pathlib import Path

from sqlalchemy import text

from app.database.session import engine


MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "database" / "migrations"


def run_migrations():
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(120) PRIMARY KEY, applied_at TIMESTAMP NOT NULL DEFAULT NOW())"))
        applied = {row[0] for row in connection.execute(text("SELECT version FROM schema_migrations"))}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            sql = "\n".join(
                line for line in path.read_text(encoding="utf-8").splitlines()
                if not line.lstrip().startswith("--")
            )
            statements = [statement.strip() for statement in sql.split(";") if statement.strip()]
            for statement in statements:
                connection.execute(text(statement))
            connection.execute(text("INSERT INTO schema_migrations(version) VALUES (:version)"), {"version": path.name})

