"""Offline production release checks. Does not require PostgreSQL or Groq."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "backend/app/main.py",
    ROOT / "backend/app/core/config.py",
    ROOT / "backend/app/api/meta.py",
    ROOT / "backend/Dockerfile",
    ROOT / "backend/alembic.ini",
]
missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
if missing:
    raise SystemExit("Missing release files: " + ", ".join(missing))
for path in (ROOT / "backend/app").rglob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print("release_check: PASS")
print("python_syntax: PASS")
print("release_files: PASS")
