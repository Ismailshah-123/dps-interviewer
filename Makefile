backend-install:
	cd backend && python -m pip install -e '.[dev]'

backend-test:
	cd backend && pytest

backend-compile:
	cd backend && python -m compileall -q app migrations

backend-run:
	cd backend && uvicorn app.main:app --reload --port 8000

worker-run:
	cd backend && python -m app.workers.runner

migration:
	cd backend && alembic revision --autogenerate -m "change"

migrate:
	cd backend && alembic upgrade head
