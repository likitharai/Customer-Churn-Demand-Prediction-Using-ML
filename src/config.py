"""Project configuration and filesystem paths."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "Data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESAMPLED_DATA_DIR = DATA_DIR / "resampled"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"
SQL_DIR = PROJECT_ROOT / "sql"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
DOCS_DIR = PROJECT_ROOT / "docs"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
LOGS_DIR = PROJECT_ROOT / "logs"

DIRECTORIES = (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    RESAMPLED_DATA_DIR,
    EXTERNAL_DATA_DIR,
    MODELS_DIR,
    REPORTS_DIR,
    SQL_DIR,
    DASHBOARD_DIR,
    DOCS_DIR,
    SCREENSHOTS_DIR,
    LOGS_DIR,
)

for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)