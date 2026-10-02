"""Pytest configuration for backend test discovery."""

import sys
from pathlib import Path

# Add backend directory and project root to sys.path
backend_dir = Path(__file__).resolve().parents[1]
root_dir = backend_dir.parent

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
