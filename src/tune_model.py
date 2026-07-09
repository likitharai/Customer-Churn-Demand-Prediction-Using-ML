"""Tune the selected best model with Optuna and persist the results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import optuna
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score

from src.config import MODELS_DIR, PROCESSED_DATA_DIR
from src.constants import ARTIFACT_FILENAMES, CV_FOLDS, N_TRIALS, RANDOM_STATE
from src.logger import logger
from src.model_config import ModelFactory


class HyperparameterTuner:
    """Optimize the selected model using Optuna and stratified cross-validation."""

    def __init__(self, data_dir: Path | None = None, models_dir: Path | None = None) -> None:
        self.data_dir = data_dir or PROCESSED_DATA_DIR
        self.models_dir = models_dir or MODELS_DIR
        self.best_model_name = self._load_best_model_name()
        self.best_params: dict[str, Any] | None = None
        self.study: optuna.Study | None = None
        self.best_model = None

    def _load_best_model_name(self) -> str:
        """Load the model name saved by the training stage."""

        info_path = self.models_dir / ARTIFACT_FILENAMES["best_model_info"]
        if not info_path.exists():
            raise FileNotFoundError(
                f"Best model metadata not found: {info_path}. Run training first."
            )

        with info_path.open("r", encoding="utf-8") as file:
            info = json.load(file)

        best_model_name = info.get("best_model")
        if not best_model_name:
            raise ValueError("Best model metadata does not contain a model name")

        logger.info("Loaded best model name: %s", best_model_name)
        return str(best_model_name)

    def load_data(self) -> tuple[pd.DataFrame, pd.Series]:
        """Load the processed training split used for optimization."""

        x_train_path = self.data_dir / "x_train.csv"
        y_train_path = self.data_dir / "y_train.csv"

        if not x_train_path.exists() or not y_train_path.exists():
            raise FileNotFoundError("Processed training data not found. Run preprocessing first.")

        X_train = pd.read_csv(x_train_path)
        y_train = pd.read_csv(y_train_path).iloc[:, 0]
        logger.info("Loaded tuning data: X=%s, y=%s", X_train.shape, y_train.shape)
        return X_train, y_train

    def objective(self, trial: optuna.Trial) -> float:
        """Optuna objective that maximizes ROC AUC."""

        X_train, y_train = self.load_data()
        params = ModelFactory.suggest_params(trial, self.best_model_name)
        model = ModelFactory.create_model(self.best_model_name, params)

        cv = StratifiedKFold(
            n_splits=CV_FOLDS,
            shuffle=True,
            random_state=RANDOM_STATE,
        )
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
        return float(scores.mean())

    def optimize(self) -> dict[str, Any]:
        """Run the Optuna study and store the best parameter set."""

        sampler = optuna.samplers.TPESampler(seed=RANDOM_STATE)
        pruner = optuna.pruners.MedianPruner()

        self.study = optuna.create_study(
            direction="maximize",
            sampler=sampler,
            pruner=pruner,
            study_name=f"{self.best_model_name} Optimization",
        )
        self.study.optimize(self.objective, n_trials=N_TRIALS, show_progress_bar=False)
        self.best_params = dict(self.study.best_params)

        logger.info(
            "Optuna completed for %s with best ROC AUC %.4f",
            self.best_model_name,
            self.study.best_value,
        )
        return self.best_params

    def train_best_model(self) -> Any:
        """Fit the selected model using the best Optuna parameters."""

        if self.best_params is None:
            raise RuntimeError("Best parameters are not available")

        X_train, y_train = self.load_data()
        self.best_model = ModelFactory.create_model(self.best_model_name, self.best_params)
        self.best_model.fit(X_train, y_train)
        logger.info("Trained tuned model for %s", self.best_model_name)
        return self.best_model

    def save_best_model(self) -> Path:
        """Persist the tuned model as the production best model artifact."""

        if self.best_model is None:
            raise RuntimeError("Best model is not available")

        self.models_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.models_dir / ARTIFACT_FILENAMES["best_model"]
        joblib.dump(self.best_model, model_path)
        logger.info("Saved tuned model to %s", model_path)
        return model_path

    def save_best_params(self) -> Path:
        """Persist the best hyperparameters selected by Optuna."""

        if self.best_params is None:
            raise RuntimeError("Best parameters are not available")

        params_path = self.models_dir / ARTIFACT_FILENAMES["best_params"]
        with params_path.open("w", encoding="utf-8") as file:
            json.dump(self.best_params, file, indent=4)

        logger.info("Saved best parameters to %s", params_path)
        return params_path

    def save_study(self) -> Path:
        """Persist the full Optuna study object."""

        if self.study is None:
            raise RuntimeError("Optuna study is not available")

        study_path = self.models_dir / ARTIFACT_FILENAMES["study"]
        joblib.dump(self.study, study_path)
        logger.info("Saved study to %s", study_path)
        return study_path

    def save_optimization_history(self) -> Path:
        """Persist the trial history for auditing and review."""

        if self.study is None:
            raise RuntimeError("Optuna study is not available")

        history_path = self.models_dir / ARTIFACT_FILENAMES["optimization_history"]
        history = self.study.trials_dataframe()
        history.to_csv(history_path, index=False)
        logger.info("Saved optimization history to %s", history_path)
        return history_path

    def display_results(self) -> None:
        """Log the final tuning summary."""

        if self.study is None or self.best_params is None:
            raise RuntimeError("Tuning results are not available")

        logger.info("Best ROC AUC for %s: %.4f", self.best_model_name, self.study.best_value)
        logger.info("Best parameters: %s", self.best_params)

    def run(self) -> dict[str, Any]:
        """Execute the full tuning workflow and persist artifacts."""

        try:
            self.optimize()
            self.train_best_model()
            self.save_best_model()
            self.save_best_params()
            self.save_study()
            self.save_optimization_history()
            self.display_results()
            logger.info("Optuna tuning completed successfully")
            return {
                "best_model_name": self.best_model_name,
                "best_params": self.best_params,
                "study_value": self.study.best_value if self.study else None,
            }
        except Exception as exc:
            logger.exception("Optuna tuning failed")
            raise RuntimeError("Hyperparameter tuning pipeline failed") from exc


if __name__ == "__main__":
    tuner = HyperparameterTuner()
    tuner.run()
