"""Model registry — save and load versioned models."""

from __future__ import annotations

import joblib
from pathlib import Path
from datetime import datetime
import json
import numpy as np
import sklearn

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODELS_DIR.mkdir(exist_ok=True)


def save_model(model, name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = MODELS_DIR / f"{name}_{timestamp}.pkl"
    latest = MODELS_DIR / f"{name}_latest.pkl"
    meta = MODELS_DIR / f"{name}_latest.json"

    joblib.dump(model, path)
    joblib.dump(model, latest)
    meta.write_text(json.dumps({
        "timestamp": timestamp,
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
        "joblib": joblib.__version__,
    }, indent=2))

    return path

def load_model(name: str):
    """Load the latest version of a model."""
    path = MODELS_DIR / f"{name}_latest.pkl"
    if not path.exists():
        raise FileNotFoundError(f"No model found: {path}")
    return joblib.load(path)
