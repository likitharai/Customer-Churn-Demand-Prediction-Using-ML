"""Project-wide constants used across the decision intelligence platform."""

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_TRIALS = 100
CV_FOLDS = 5

TARGET_COLUMN = "Churn_flag"
TARGET_LABEL_COLUMN = "Churn"

PROJECT_NAME = "Decision Intelligence Platform"
VERSION = "1.0.0"
AUTHOR = "Likitha Rai"

MODEL_COMPARE_ORDER = (
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

RISK_THRESHOLDS = {
	"very_high": 0.80,
	"high": 0.60,
	"medium": 0.40,
	"low": 0.20,
}

ARTIFACT_FILENAMES = {
	"best_model": "best_model.pkl",
	"best_model_info": "best_model_info.json",
	"best_params": "best_params.json",
	"study": "study.pkl",
	"optimization_history": "optimization_history.csv",
	"model_metrics": "model_metrics.csv",
	"feature_importance": "feature_importance.csv",
	"preprocessing_pipeline": "preprocessing_pipeline.pkl",
	"feature_columns": "feature_columns.pkl",
	"evaluation_metrics": "evaluation_metrics.json",
	"classification_report": "classification_report.csv",
	"confusion_matrix": "confusion_matrix.csv",
	"predictions": "predictions.csv",
}