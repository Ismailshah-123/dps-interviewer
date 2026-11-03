"""Run the V12 PostgreSQL acceptance suite against a disposable database."""
import os
import subprocess
import sys

url = os.getenv("DPS_TEST_DATABASE_URL")
if not url:
    raise SystemExit("DPS_TEST_DATABASE_URL is required")

env = os.environ.copy()
env["DATABASE_URL"] = url
env["AUTO_CREATE_SCHEMA"] = "false"
cmd = [sys.executable, "-m", "pytest", "tests/postgres", "-q"]
raise SystemExit(subprocess.call(cmd, cwd="backend", env=env))
