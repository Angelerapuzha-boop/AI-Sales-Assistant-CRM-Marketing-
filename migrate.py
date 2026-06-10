#!/usr/bin/env python3
"""Run Alembic migrations."""
import subprocess
import sys
import os

backend_dir = os.path.join(os.path.dirname(__file__), "..", "backend")
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend_dir, check=True)
