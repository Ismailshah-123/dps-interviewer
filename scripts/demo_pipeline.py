"""Drive one SYNTHETIC interview through the running API with the configured (real) AI providers.

Usage (backend and worker already running):
    python scripts/demo_pipeline.py --audio samples/synthetic/english_interview.webm
Admin credentials are read from backend/.env. Creates staff accounts if absent. Synthetic data only.
"""
import argparse
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
STAFF_PASSWORD = "Synthetic-Pass-2026!"  # fixture value shared with tests; demo only


def env_value(key: str) -> str:
    for line in (ROOT / "backend" / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"{key} missing from backend/.env")


def login(c: httpx.Client, email: str, password: str) -> dict:
    r = c.post("/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def ensure_user(c, admin, email, name, role):
    r = c.post("/auth/users", headers=admin, json={"email": email, "full_name": name, "password": STAFF_PASSWORD, "role": role})
    if r.status_code not in (200, 201) and "already exists" not in r.text:
        r.raise_for_status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", default=str(ROOT / "samples" / "synthetic" / "english_interview.webm"))
    ap.add_argument("--base", default="http://127.0.0.1:8000/api/v1")
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    with httpx.Client(base_url=args.base, timeout=120) as c:
        admin = login(c, env_value("DEFAULT_ADMIN_EMAIL"), env_value("DEFAULT_ADMIN_PASSWORD"))
        ensure_user(c, admin, "sana.interviewer@dps.example.com", "Sana Interviewer (Synthetic)", "interviewer")
        ensure_user(c, admin, "principal@dps.example.com", "Principal Reviewer (Synthetic)", "reviewer")
        iv = login(c, "sana.interviewer@dps.example.com", STAFF_PASSWORD)
        cand = c.post("/candidates", headers=iv, json={"name": "Ayesha Khan (Synthetic)", "grade": "Class 3", "application_reference": f"SYN-{int(time.time())}"}).raise_for_status().json()
        interview = c.post("/interviews", headers=iv, json={"candidate_id": cand["id"]}).raise_for_status().json()
        iid = interview["id"]
        c.post(f"/interviews/{iid}/consent", headers=iv, json={"notice_version": "DPS-DEMO-NOTICE-1.0", "confirmed": True}).raise_for_status()
        c.post(f"/interviews/{iid}/recording-start", headers=iv).raise_for_status()
        audio = Path(args.audio)
        with audio.open("rb") as f:
            rec = c.post(f"/recordings/{iid}", headers=iv, files={"file": (audio.name, f, "audio/webm")}).raise_for_status().json()
        print(f"candidate {cand['reference_number']} interview {iid}")
        print(f"uploaded {rec['size_bytes']} bytes sha256={rec['sha256'][:16]}")
        started = time.monotonic()
        last = None
        while time.monotonic() - started < args.timeout:
            st = c.get(f"/processing/{iid}", headers=iv).raise_for_status().json()
            if st["interview_status"] != last:
                last = st["interview_status"]
                print(f"[{time.monotonic() - started:6.1f}s] {last}")
            if last in ("needs_review", "failed"):
                for j in st["jobs"]:
                    print(f"  job {j['type']}: {j['status']} attempts={j['attempts']} error={j['error']}")
                break
            time.sleep(2)
        try:
            t = c.get(f"/transcriptions/{iid}", headers=iv).raise_for_status().json()
            print(f"transcript: provider={t['provider']} model={t['model_name']} language={t['language']} segments={len(t['segments'])} seconds={t['processing_seconds']}")
        except httpx.HTTPStatusError:
            print("transcript: not available")
        print(f"open http://localhost:5173/interviews/{iid}")
        return 0 if last == "needs_review" else 1


if __name__ == "__main__":
    sys.exit(main())
