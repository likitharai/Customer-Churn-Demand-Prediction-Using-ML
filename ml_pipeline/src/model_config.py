"""Model factory and Optuna search spaces for supported estimators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import optuna
from sklearn.ensemble import (
    AdaBoostClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from ml_pipeline.src.constants import RANDOM_STATE

try:
    from lightgbm import LGBMClassifier
except ImportError:  # pragma: no cover - optional dependency
    LGBMClassifier = None

try:
    from xgboost import XGBClassifier
except ImportError:  # pragma: no cover - optional dependency
    XGBClassifier = None

try:
    from catboost import CatBoostClassifier
except ImportError:  # pragma: no cover - optional dependency
    CatBoostClassifier = None


@dataclass(frozen=True)
class ModelSpecification:
    """Container for a model builder and tuning space."""

    builder: Callable[[dict[str, Any] | None], Any]
    objective_name: str
    supports_proba: bool = True


class ModelFactory:
    """Create and tune the estimators supported by the platform."""

    @staticmethod
    def _build_calibrated_svm(params: dict[str, Any] | None = None) -> CalibratedClassifierCV:
        """Build a calibrated SVM that exposes predict_proba without deprecation warnings."""

        params = params or {}
        svm = SVC(
            random_state=RANDOM_STATE,
            class_weight="balanced",
            **params,
        )
        return CalibratedClassifierCV(svm, ensemble=False)

    @staticmethod
    def supported_model_names() -> tuple[str, ...]:
        """Return the list of supported model names in comparison order."""

        return (
            "Logistic Regression",
            "Random Forest",
            "Decision Tree",
            "Gradient Boosting",
            "AdaBoost",
            "XGBoost",
            "LightGBM",
            "CatBoost",
            "SVM",
        )

    @staticmethod
    def available_models() -> dict[str, Any]:
        """Return default model instances for comparison."""

        models: dict[str, Any] = {
            "Logistic Regression": LogisticRegression(
                max_iter=2000,
                random_state=RANDOM_STATE,
                class_weight="balanced",
            ),
            "Random Forest": RandomForestClassifier(
                n_estimators=400,
                random_state=RANDOM_STATE,
                n_jobs=-1,
                class_weight="balanced_subsample",
            ),
            "Decision Tree": DecisionTreeClassifier(
                random_state=RANDOM_STATE,
                class_weight="balanced",
            ),
            "Gradient Boosting": GradientBoostingClassifier(
                random_state=RANDOM_STATE,
            ),
            "AdaBoost": AdaBoostClassifier(
                random_state=RANDOM_STATE,
                n_estimators=250,
            ),
            "SVM": ModelFactory._build_calibrated_svm(),
        }

        if XGBClassifier is not None:
            models["XGBoost"] = XGBClassifier(
                random_state=RANDOM_STATE,
                eval_metric="logloss",
                n_estimators=300,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.9,
                colsample_bytree=0.9,
                tree_method="hist",
            )

        if LGBMClassifier is not None:
            models["LightGBM"] = LGBMClassifier(
                random_state=RANDOM_STATE,
                verbosity=-1,
                n_estimators=300,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
            )

        if CatBoostClassifier is not None:
            models["CatBoost"] = CatBoostClassifier(
                random_state=RANDOM_STATE,
                verbose=False,
                iterations=400,
                learning_rate=0.05,
                depth=6,
            )

        return models

    @staticmethod
    def create_model(
        model_name: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Create a configured estimator for the requested model name."""

        params = params or {}

        if model_name == "Logistic Regression":
            return LogisticRegression(
                max_iter=2000,
                random_state=RANDOM_STATE,
                class_weight="balanced",
                **params,
            )

        if model_name == "Random Forest":
            return RandomForestClassifier(
                random_state=RANDOM_STATE,
                n_jobs=-1,
                class_weight="balanced_subsample",
                **params,
            )

        if model_name == "Decision Tree":
            return DecisionTreeClassifier(
                random_state=RANDOM_STATE,
                class_weight="balanced",
                **params,
            )

        if model_name == "Gradient Boosting":
            return GradientBoostingClassifier(random_state=RANDOM_STATE, **params)

        if model_name == "AdaBoost":
            return AdaBoostClassifier(random_state=RANDOM_STATE, **params)

        if model_name == "SVM":
            return ModelFactory._build_calibrated_svm(params)

        if model_name == "XGBoost":
            if XGBClassifier is None:
                raise ImportError("xgboost is not installed")
            return XGBClassifier(
                random_state=RANDOM_STATE,
                eval_metric="logloss",
                tree_method="hist",
                **params,
            )

        if model_name == "LightGBM":
            if LGBMClassifier is None:
                raise ImportError("lightgbm is not installed")
            return LGBMClassifier(
                random_state=RANDOM_STATE,
                verbosity=-1,
                **params,
            )

        if model_name == "CatBoost":
            if CatBoostClassifier is None:
                raise ImportError("catboost is not installed")
            return CatBoostClassifier(
                random_state=RANDOM_STATE,
                verbose=False,
                **params,
            )

        raise ValueError(f"Unsupported model name: {model_name}")

    @staticmethod
    def suggest_params(trial: optuna.Trial, model_name: str) -> dict[str, Any]:
        """Build an Optuna parameter space for the requested model."""

        if model_name == "Logistic Regression":
            return {
                "C": trial.suggest_float("C", 1e-3, 100.0, log=True),
                "solver": trial.suggest_categorical(
                    "solver",
                    ["lbfgs", "liblinear"],
                ),
            }

        if model_name == "Random Forest":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 200, 800),
                "max_depth": trial.suggest_int("max_depth", 3, 20),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "max_features": trial.suggest_categorical(
                    "max_features",
                    ["sqrt", "log2", None],
                ),
            }

        if model_name == "Decision Tree":
            return {
                "max_depth": trial.suggest_int("max_depth", 3, 20),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "criterion": trial.suggest_categorical(
                    "criterion",
                    ["gini", "entropy", "log_loss"],
                ),
            }

        if model_name == "Gradient Boosting":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                "learning_rate": trial.suggest_float(
                    "learning_rate",
                    0.01,
                    0.3,
                    log=True,
                ),
                "max_depth": trial.suggest_int("max_depth", 2, 5),
                "min_samples_split": trial.suggest_int("min_samples_split", 2, 20),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            }

        if model_name == "AdaBoost":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 100, 500),
                "learning_rate": trial.suggest_float(
                    "learning_rate",
                    0.01,
                    1.0,
                    log=True,
                ),
            }

        if model_name == "SVM":
            return {
                "C": trial.suggest_float("C", 1e-3, 100.0, log=True),
                "kernel": trial.suggest_categorical("kernel", ["rbf", "linear"]),
                "gamma": trial.suggest_categorical("gamma", ["scale", "auto"]),
            }

        if model_name == "XGBoost":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 200, 800),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float(
                    "learning_rate",
                    0.01,
                    0.3,
                    log=True,
                ),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 10.0),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            }

        if model_name == "LightGBM":
            return {
                "n_estimators": trial.suggest_int("n_estimators", 200, 800),
                "num_leaves": trial.suggest_int("num_leaves", 16, 128),
                "learning_rate": trial.suggest_float(
                    "learning_rate",
                    0.01,
                    0.3,
                    log=True,
                ),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_samples": trial.suggest_int("min_child_samples", 10, 100),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            }

        if model_name == "CatBoost":
            return {
                "iterations": trial.suggest_int("iterations", 200, 1000),
                "depth": trial.suggest_int("depth", 4, 10),
                "learning_rate": trial.suggest_float(
                    "learning_rate",
                    0.01,
                    0.3,
                    log=True,
                ),
                "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 10.0),
                "border_count": trial.suggest_int("border_count", 32, 255),
                "random_strength": trial.suggest_float("random_strength", 0.1, 10.0),
                "bagging_temperature": trial.suggest_float(
                    "bagging_temperature",
                    0.0,
                    10.0,
                ),
            }

        raise ValueError(f"Unsupported model name: {model_name}")