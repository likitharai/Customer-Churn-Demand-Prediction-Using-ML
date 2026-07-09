"""Model registry — save and load versioned models."""

from __future__ import annotations

import joblib
from pathlib import Path
from datetime import datetime

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODELS_DIR.mkdir(exist_ok=True)


def save_model(model, name: str) -> Path:
    """Save model with timestamp versioning."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = MODELS_DIR / f"{name}_{timestamp}.pkl"
    joblib.dump(model, path)
    # Also save as latest
    joblib.dump(model, MODELS_DIR / f"{name}_latest.pkl")
    return path


def load_model(name: str):
    """Load the latest version of a model."""
    path = MODELS_DIR / f"{name}_latest.pkl"
    if not path.exists():
        raise FileNotFoundError(f"No model found: {path}")
    return joblib.load(path)
