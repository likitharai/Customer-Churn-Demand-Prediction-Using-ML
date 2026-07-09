"""
Project Configuration
"""

from pathlib import Path

# Root Directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# -----------------------------
# Data
# -----------------------------

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

RESAMPLED_DATA_DIR = DATA_DIR / "resampled"

EXTERNAL_DATA_DIR = DATA_DIR / "external"

# -----------------------------
# Models
# -----------------------------

MODELS_DIR = PROJECT_ROOT / "models"

# -----------------------------
# Reports
# -----------------------------

REPORTS_DIR = PROJECT_ROOT / "reports"

# -----------------------------
# SQL
# -----------------------------

SQL_DIR = PROJECT_ROOT / "sql"

# -----------------------------
# Dashboard
# -----------------------------

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

# -----------------------------
# Documentation
# -----------------------------

DOCS_DIR = PROJECT_ROOT / "docs"

SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

# -----------------------------
# Logs
# -----------------------------

LOGS_DIR = PROJECT_ROOT / "logs"

# -----------------------------
# Create folders automatically
# -----------------------------

directories = [
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
]

for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)