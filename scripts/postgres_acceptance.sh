#!/usr/bin/env sh
set -eu
: "${DPS_TEST_DATABASE_URL:?Set DPS_TEST_DATABASE_URL to a disposable PostgreSQL database}"
cd "$(dirname "$0")/../backend"
alembic upgrade head
cd ..
python scripts/postgres_acceptance.py
