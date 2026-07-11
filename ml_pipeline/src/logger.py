"""Logging helpers for the platform."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from ml_pipeline.src.config import LOGS_DIR


def get_logger(name: str = "decision_intelligence_platform") -> logging.Logger:
    """Return a configured application logger.

    The logger writes to both stdout and a rotating log file. Handlers are only
    attached once to avoid duplicate messages during repeated imports.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    log_file = LOGS_DIR / "project.log"
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


logger = get_logger()