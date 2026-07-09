"""Generate SHAP explainability artifacts for the trained churn model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import MODELS_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, SCREENSHOTS_DIR
from src.constants import ARTIFACT_FILENAMES
from src.logger import logger

try:
    import shap
except ImportError:  # pragma: no cover - optional dependency
    shap = None


class SHAPExplainer:
    """Create SHAP artifacts from the saved model and transformed features."""

    def __init__(self, models_dir: Path | None = None, reports_dir: Path | None = None) -> None:
        self.models_dir = models_dir or MODELS_DIR
        self.reports_dir = reports_dir or REPORTS_DIR
        self.model = self._load_model()
        self.feature_columns = self._load_feature_columns()
        self.background_data = self._load_background_data()
        self.explainer = None
        self.shap_values = None
        self.explanation = None

    def _load_model(self) -> Any:
        """Load the persisted best model artifact."""

        model_path = self.models_dir / ARTIFACT_FILENAMES["best_model"]
        if not model_path.exists():
            raise FileNotFoundError(f"Best model artifact not found: {model_path}")
        return joblib.load(model_path)

    def _load_feature_columns(self) -> list[str]:
        """Load the transformed feature names used by the trained model."""

        feature_path = self.models_dir / ARTIFACT_FILENAMES["feature_columns"]
        if feature_path.exists():
            feature_columns = joblib.load(feature_path)
            return [str(column) for column in feature_columns]

        x_train = pd.read_csv(PROCESSED_DATA_DIR / "x_train.csv")
        return [str(column) for column in x_train.columns]

    def _load_background_data(self) -> pd.DataFrame:
        """Load transformed training features for SHAP background sampling."""

        x_train_path = PROCESSED_DATA_DIR / "x_train.csv"
        if not x_train_path.exists():
            raise FileNotFoundError(
                f"Transformed training data not found: {x_train_path}. Run preprocessing first."
            )
        dataframe = pd.read_csv(x_train_path)
        if list(dataframe.columns) != self.feature_columns:
            dataframe = dataframe.reindex(columns=self.feature_columns, fill_value=0)
        return dataframe

    def create_explainer(self) -> Any:
        """Create a SHAP explainer for the selected model."""

        if shap is None:
            raise ImportError("shap is not installed")

        background_sample = self.background_data.sample(
            n=min(200, len(self.background_data)),
            random_state=42,
        )
        self.explainer = shap.Explainer(self.model, background_sample, feature_names=self.feature_columns)
        logger.info("Created SHAP explainer")
        return self.explainer

    def calculate_shap_values(self, sample_size: int = 200) -> pd.DataFrame:
        """Calculate SHAP values for a representative sample."""

        if shap is None:
            raise ImportError("shap is not installed")

        if self.explainer is None:
            self.create_explainer()

        sample = self.background_data.sample(
            n=min(sample_size, len(self.background_data)),
            random_state=42,
        )
        self.explanation = self.explainer(sample)

        values = self.explanation.values
        if values.ndim == 3:
            values = values[:, :, -1]
        self.shap_values = values

        absolute_values = np.abs(values)
        if absolute_values.ndim != 2:
            raise ValueError(
                f"Expected a 2D SHAP matrix after reduction, got shape {absolute_values.shape}"
            )

        importance = pd.DataFrame(
            {
                "Feature": self.feature_columns,
                "Mean_Abs_SHAP": absolute_values.mean(axis=0),
            }
        ).sort_values(by="Mean_Abs_SHAP", ascending=False)
        importance.to_csv(self.reports_dir / "shap_feature_importance.csv", index=False)
        logger.info("Calculated SHAP values for %s rows", len(sample))
        return importance

    def save_summary_plot(self) -> Path:
        """Save the SHAP summary plot as a PNG file."""

        if shap is None:
            raise ImportError("shap is not installed")

        if self.shap_values is None or self.explanation is None:
            self.calculate_shap_values()

        output_dir = self.reports_dir / "shap"
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_path = output_dir / "summary_plot.png"

        plt.figure(figsize=(12, 8))
        shap.summary_plot(self.shap_values, self.explanation.data, feature_names=self.feature_columns, show=False)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        return plot_path

    def save_waterfall_plot(self, row_index: int = 0) -> Path:
        """Save a waterfall plot for a single prediction explanation."""

        if shap is None:
            raise ImportError("shap is not installed")

        if self.explanation is None:
            self.calculate_shap_values()

        output_dir = self.reports_dir / "shap"
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_path = output_dir / f"waterfall_plot_{row_index}.png"

        plt.figure(figsize=(12, 8))
        shap.plots.waterfall(self.explanation[row_index], show=False)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        return plot_path

    def save_force_plot(self, row_index: int = 0) -> Path:
        """Save a SHAP force plot as HTML for interactive review."""

        if shap is None:
            raise ImportError("shap is not installed")

        if self.explanation is None:
            self.calculate_shap_values()

        output_dir = self.reports_dir / "shap"
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_path = output_dir / f"force_plot_{row_index}.html"

        force_plot = shap.force_plot(
            self.explanation.base_values[row_index],
            self.explanation.values[row_index],
            self.explanation.data[row_index],
            feature_names=self.feature_columns,
            matplotlib=False,
        )
        shap.save_html(str(plot_path), force_plot)
        return plot_path

    def save_dependence_plot(self, feature_name: str | None = None) -> Path:
        """Save a dependence plot for the specified feature or the top feature."""

        if shap is None:
            raise ImportError("shap is not installed")

        if self.shap_values is None or self.explanation is None:
            self.calculate_shap_values()

        output_dir = self.reports_dir / "shap"
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_path = output_dir / "dependence_plot.png"

        feature = feature_name or self.feature_columns[0]
        plt.figure(figsize=(12, 8))
        shap.dependence_plot(
            feature,
            self.shap_values,
            self.explanation.data,
            feature_names=self.feature_columns,
            show=False,
        )
        plt.tight_layout()
        plt.savefig(plot_path, dpi=300, bbox_inches="tight")
        plt.close()
        return plot_path

    def save_feature_importance(self) -> Path:
        """Ensure the feature importance CSV exists and return its path."""

        importance_path = self.reports_dir / "shap_feature_importance.csv"
        if not importance_path.exists():
            self.calculate_shap_values()
        return importance_path

    def run(self) -> dict[str, Path]:
        """Generate all explainability artifacts."""

        try:
            self.create_explainer()
            self.calculate_shap_values()
            summary_plot = self.save_summary_plot()
            waterfall_plot = self.save_waterfall_plot()
            force_plot = self.save_force_plot()
            dependence_plot = self.save_dependence_plot()
            importance_csv = self.save_feature_importance()
            logger.info("SHAP explainability artifacts generated successfully")
            return {
                "summary_plot": summary_plot,
                "waterfall_plot": waterfall_plot,
                "force_plot": force_plot,
                "dependence_plot": dependence_plot,
                "feature_importance": importance_csv,
            }
        except Exception as exc:
            logger.exception("SHAP explainability failed")
            raise RuntimeError("SHAP explainability pipeline failed") from exc


if __name__ == "__main__":
    explainer = SHAPExplainer()
    explainer.run()
