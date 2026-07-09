"""
Project      : Decision Intelligence Platform
Module       : tune_model.py
Author       : Likitha Rai

Description:
Hyperparameter tuning using Optuna.
"""

import json
import joblib
import optuna
import pandas as pd

from catboost import CatBoostClassifier

from sklearn.metrics import accuracy_score
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
)

from src.config import (
    MODELS_DIR,
    PROCESSED_DATA_DIR,
)

from src.constants import (
    RANDOM_STATE,
    CV_FOLDS,
    N_TRIALS,
)

from src.logger import logger


class HyperparameterTuner:

    def __init__(self):

        self.best_model = None

        self.best_params = None

        self.study = None

    # ==========================================================
    # Load Dataset
    # ==========================================================

    def load_data(self):

        logger.info("Loading processed dataset...")

        X_train = pd.read_csv(

            PROCESSED_DATA_DIR /

            "x_train.csv"

        )

        y_train = pd.read_csv(

            PROCESSED_DATA_DIR /

            "y_train.csv"

        ).values.ravel()

        logger.info(

            f"Training Shape : {X_train.shape}"

        )

        return (

            X_train,

            y_train,

        )

    # ==========================================================
    # Objective Function
    # ==========================================================

    def objective(self, trial):

        X_train, y_train = self.load_data()

        params = {

            "iterations": trial.suggest_int(
                "iterations",
                200,
                1000,
            ),

            "depth": trial.suggest_int(
                "depth",
                4,
                10,
            ),

            "learning_rate": trial.suggest_float(
                "learning_rate",
                0.01,
                0.3,
                log=True,
            ),

            "l2_leaf_reg": trial.suggest_float(
                "l2_leaf_reg",
                1,
                10,
            ),

            "random_strength": trial.suggest_float(
                "random_strength",
                0.1,
                10,
            ),

            "bagging_temperature": trial.suggest_float(
                "bagging_temperature",
                0,
                10,
            ),

            "border_count": trial.suggest_int(
                "border_count",
                32,
                255,
            ),

            "loss_function": "Logloss",

            "eval_metric": "AUC",

            "random_state": RANDOM_STATE,

            "verbose": False,

        }

        model = CatBoostClassifier(
            **params
        )

        cv = StratifiedKFold(

            n_splits=CV_FOLDS,

            shuffle=True,

            random_state=RANDOM_STATE,

        )

        score = cross_val_score(

            model,

            X_train,

            y_train,

            cv=cv,

            scoring="roc_auc",

        )

        return score.mean()
    
    # ==========================================================
    # Run Optuna Study
    # ==========================================================

    def optimize(self):

        sampler = optuna.samplers.TPESampler(

            seed=RANDOM_STATE

        )

        pruner = optuna.pruners.MedianPruner()

        self.study = optuna.create_study(

            direction="maximize",

            sampler=sampler,

            pruner=pruner,

            study_name="CatBoost Optimization",

        )

        self.study.optimize(

            self.objective,

            n_trials=N_TRIALS,

            show_progress_bar=True,

        )

        self.best_params = self.study.best_params

        print("\n")

        print("=" * 80)

        print("Best ROC-AUC")

        print(self.study.best_value)

        print("\n")

        print(self.best_params)

        return self.best_params

    # ==========================================================
    # Train Best Model
    # ==========================================================

    def train_best_model(self):

        X_train, y_train = self.load_data()

        logger.info("Training Optimized CatBoost...")

        self.best_model = CatBoostClassifier(

            **self.best_params,

            loss_function="Logloss",

            eval_metric="AUC",

            random_state=RANDOM_STATE,

            verbose=False,

        )

        self.best_model.fit(

            X_train,

            y_train,

        )

        logger.info("Training Completed.")

        return self.best_model

    # ==========================================================
    # Save Best Model
    # ==========================================================

    def save_best_model(self):

        MODELS_DIR.mkdir(

            parents=True,

            exist_ok=True,

        )

        model_path = (

            MODELS_DIR /

            "best_model.pkl"

        )

        joblib.dump(

            self.best_model,

            model_path,

        )

        logger.info(

            f"Best Model Saved : {model_path}"

        )

    # ==========================================================
    # Save Best Parameters
    # ==========================================================

    def save_best_params(self):

        params_path = (

            MODELS_DIR /

            "best_params.json"

        )

        with open(

            params_path,

            "w",

        ) as file:

            json.dump(

                self.best_params,

                file,

                indent=4,

            )

        logger.info(

            f"Best Parameters Saved : {params_path}"

        )

    # ==========================================================
    # Save Study
    # ==========================================================

    def save_study(self):

        study_path = (

            MODELS_DIR /

            "study.pkl"

        )

        joblib.dump(

            self.study,

            study_path,

        )

        logger.info(

            f"Study Saved : {study_path}"

        )

    # ==========================================================
    # Save Optimization History
    # ==========================================================

    def save_optimization_history(self):

        history = self.study.trials_dataframe()

        history_path = (

            MODELS_DIR /

            "optimization_history.csv"

        )

        history.to_csv(

            history_path,

            index=False,

        )

        logger.info(

            f"Optimization History Saved : {history_path}"

        )

    # ==========================================================
    # Display Results
    # ==========================================================

    def display_results(self):

        print("\n")

        print("=" * 80)

        print("OPTUNA HYPERPARAMETER TUNING")

        print("=" * 80)

        print(f"Best ROC-AUC : {self.study.best_value:.4f}")

        print("\n")

        print("Best Parameters")

        print("-" * 80)

        for key, value in self.best_params.items():

            print(f"{key:25} : {value}")

        print("=" * 80)

    # ==========================================================
    # Run Complete Pipeline
    # ==========================================================

    def run(self):

        self.optimize()

        self.train_best_model()

        self.save_best_model()

        self.save_best_params()

        self.save_study()

        self.save_optimization_history()

        self.display_results()

        logger.info("=" * 80)

        logger.info("OPTUNA TUNING COMPLETED")

        logger.info("=" * 80)

        print("\n")

        print("=" * 80)

        print("OPTUNA TUNING COMPLETED SUCCESSFULLY")

        print("=" * 80)

        print()

        print("Generated Files")

        print("-------------------------------")

        print("✔ best_model.pkl")

        print("✔ best_params.json")

        print("✔ study.pkl")

        print("✔ optimization_history.csv")


# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    tuner = HyperparameterTuner()

    tuner.run()            