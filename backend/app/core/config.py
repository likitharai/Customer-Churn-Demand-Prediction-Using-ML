import os
from urllib.parse import urlparse


INSECURE_VALUES = {"", "ChangeMe123!", "development-only-change-me", "local-development-secret-change-before-deploy", "2005"}


def is_production():
    return os.getenv("APP_ENV", "development").lower() == "production"


def validate_environment():
    if not is_production():
        return
    errors = []
    token_secret = os.getenv("TOKEN_SECRET", "")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    database_url = os.getenv("DATABASE_URL", "")
    origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "").split(",") if value.strip()]
    if token_secret in INSECURE_VALUES or len(token_secret) < 48:
        errors.append("TOKEN_SECRET must be a unique random value of at least 48 characters")
    if admin_password in INSECURE_VALUES or len(admin_password) < 12:
        errors.append("ADMIN_PASSWORD must be unique and at least 12 characters")
    if not database_url or "localhost" in database_url or "2005" in database_url:
        errors.append("DATABASE_URL must use production credentials")
    if not origins or any(urlparse(origin).scheme != "https" for origin in origins):
        errors.append("CORS_ORIGINS must contain only explicit HTTPS origins")
    if os.getenv("APP_BASE_URL", "").startswith("http://"):
        errors.append("APP_BASE_URL must use HTTPS")
    if errors:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(errors))
