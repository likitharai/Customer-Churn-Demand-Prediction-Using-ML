import os
import unittest
from unittest.mock import patch

from app.core.config import validate_environment


class ProductionConfigTests(unittest.TestCase):
    def test_development_allows_local_defaults(self):
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=True):
            validate_environment()

    def test_production_rejects_weak_defaults(self):
        with patch.dict(os.environ, {"APP_ENV": "production", "TOKEN_SECRET": "short", "ADMIN_PASSWORD": "ChangeMe123!"}, clear=True):
            with self.assertRaises(RuntimeError):
                validate_environment()

    def test_production_accepts_hardened_configuration(self):
        values = {
            "APP_ENV": "production",
            "TOKEN_SECRET": "x" * 64,
            "ADMIN_PASSWORD": "Unique-Admin-Password-2026!",
            "DATABASE_URL": "postgresql+psycopg://retainiq:strong@db:5432/retainiq",
            "CORS_ORIGINS": "https://app.example.com",
            "APP_BASE_URL": "https://app.example.com",
        }
        with patch.dict(os.environ, values, clear=True):
            validate_environment()


if __name__ == "__main__":
    unittest.main()
