LIGHTGBM_PARAMS = {
    "objective": "binary",
    "metric": "binary_logloss",
    "verbosity": -1,
    "random_state": 42,
}

OPTUNA_CONFIG = {
    "n_trials": 100,
    "timeout": None,
}