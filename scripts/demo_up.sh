#!/usr/bin/env sh
set -eu
if [ ! -f .env ]; then
  echo "Missing .env. Copy .env.demo.example to .env and configure it first." >&2
  exit 1
fi
docker compose -f docker-compose.demo.yml up --build -d
printf '\nDemo backend: http://localhost:8000\nAPI docs:     http://localhost:8000/docs\nHealth:       http://localhost:8000/api/v1/health/ready\nAI config:    http://localhost:8000/api/v1/health/ai\nMetrics:      http://localhost:8000/metrics\n'
