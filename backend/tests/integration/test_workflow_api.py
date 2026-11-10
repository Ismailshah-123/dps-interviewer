"""Full interviewer -> principal workflow through the HTTP API, using deterministic test providers."""
import pytest

from app.core.config import settings

ADMIN = {"email": "admin@dps.example.com", "password": "TestPassword123!"}
PASSWORD = "Synthetic-Pass-2026!"
# Minimal EBML header: enough to pass the WebM signature check. Content is synthetic, not real audio.
FAKE_WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 256


async def login(client, email, password=PASSWORD):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def create_staff(client, admin, email, role):
    r = await client.post("/api/v1/auth/users", headers=admin, json={"email": email, "full_name": f"Synthetic {role}", "password": PASSWORD, "role": role})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.fixture
def deterministic_ai(monkeypatch):
    monkeypatch.setattr(settings, "transcription_provider", "deterministic-test")
    monkeypatch.setattr(settings, "summarization_provider", "deterministic-test")


async def test_full_review_cycle_with_correction(client, deterministic_ai):
    admin = await login(client, ADMIN["email"], ADMIN["password"])
    await create_staff(client, admin, "wf.interviewer@dps.example.com", "interviewer")
    await create_staff(client, admin, "wf.other@dps.example.com", "interviewer")
    await create_staff(client, admin, "wf.principal@dps.example.com", "principal")
    interviewer = await login(client, "wf.interviewer@dps.example.com")
    other = await login(client, "wf.other@dps.example.com")
    principal = await login(client, "wf.principal@dps.example.com")

    r = await client.post("/api/v1/candidates", headers=interviewer, json={"name": "Synthetic Child A", "grade": "Grade 3"})
    assert r.status_code == 201, r.text
    candidate_id = r.json()["id"]
    r = await client.post("/api/v1/interviews", headers=interviewer, json={"candidate_id": candidate_id})
    assert r.status_code == 201, r.text
    interview = r.json()
    iid = interview["id"]
    assert interview["candidate_reference"].startswith("DPS-")

    # Recording is refused until consent is confirmed.
    r = await client.post(f"/api/v1/interviews/{iid}/recording-start", headers=interviewer)
    assert r.status_code == 400
    r = await client.post(f"/api/v1/interviews/{iid}/consent", headers=interviewer, json={"notice_version": "demo-v1", "confirmed": True})
    assert r.status_code == 200
    assert (await client.post(f"/api/v1/interviews/{iid}/recording-start", headers=interviewer)).json()["status"] == "recording"
    # Retrying recording-start is idempotent rather than a 500.
    assert (await client.post(f"/api/v1/interviews/{iid}/recording-start", headers=interviewer)).status_code == 200

    # Another interviewer cannot see or upload to it (404 hides existence).
    assert (await client.get(f"/api/v1/interviews/{iid}", headers=other)).status_code == 404
    files = {"file": ("interview.webm", FAKE_WEBM, "audio/webm;codecs=opus")}
    assert (await client.post(f"/api/v1/recordings/{iid}", headers=other, files=files)).status_code == 404
    # Reviewer cannot see an interview that has not been submitted.
    assert (await client.get(f"/api/v1/interviews/{iid}", headers=principal)).status_code == 404

    r = await client.post(f"/api/v1/recordings/{iid}", headers=interviewer, files=files)
    assert r.status_code == 201, r.text
    assert r.json()["mime_type"] == "audio/webm"
    # Duplicate upload of the same bytes returns the existing recording, no second job.
    r2 = await client.post(f"/api/v1/recordings/{iid}", headers=interviewer, files={"file": ("again.webm", FAKE_WEBM, "audio/webm")})
    assert r2.status_code in (201, 409)

    r = await client.post("/api/v1/processing/run-once", headers=admin)
    assert r.status_code == 200
    await client.post("/api/v1/processing/run-once", headers=admin)
    status = (await client.get(f"/api/v1/processing/{iid}", headers=interviewer)).json()
    assert status["interview_status"] == "needs_review", status
    assert len([j for j in status["jobs"] if j["type"] == "transcription"]) == 1

    transcript = (await client.get(f"/api/v1/transcriptions/{iid}", headers=interviewer)).json()
    assert transcript["segments"], transcript
    summary = (await client.get(f"/api/v1/summaries/{iid}", headers=interviewer)).json()
    assert summary["provider"] == "deterministic-test"

    form = (await client.get(f"/api/v1/forms/{iid}", headers=interviewer)).json()
    fields = {f["field_id"]: f for f in form["fields"]}
    # Professional-judgement fields are never filled by AI.
    assert fields["interviewer_observations"]["value"]["text"] == ""
    assert fields["interviewer_observations"]["value"]["source"] == "manual_required"
    # Absent information is flagged, not invented.
    assert fields["follow_up_questions"]["value"]["text"] == "Not mentioned"

    # Submission is blocked until every field is confirmed by the interviewer.
    r = await client.post(f"/api/v1/interviews/{iid}/submit", headers=interviewer)
    assert r.status_code == 409
    assert "confirmation" in r.json()["detail"]

    form_id = form["id"]
    r = await client.patch(f"/api/v1/forms/{form_id}/fields/interviewer_observations", headers=interviewer, json={"value": {"text": "Synthetic observation entered by interviewer."}})
    assert r.status_code == 200 and r.json()["human_edited"] is True
    for fid in fields:
        if fid != "interviewer_observations":
            r = await client.post(f"/api/v1/forms/{form_id}/fields/{fid}/confirm", headers=interviewer)
            assert r.status_code == 200 and r.json()["human_edited"] is False
    # Other interviewer cannot edit evidence on this form.
    r = await client.patch(f"/api/v1/forms/{form_id}/fields/interview_overview", headers=other, json={"value": {"text": "tampered"}})
    assert r.status_code == 404

    r = await client.post(f"/api/v1/interviews/{iid}/submit", headers=interviewer)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "submitted"

    # After submission evidence is frozen for the interviewer.
    r = await client.patch(f"/api/v1/forms/{form_id}/fields/interview_overview", headers=interviewer, json={"value": {"text": "late edit"}})
    assert r.status_code == 409

    # Reviewer: cannot edit, can review; correction requires remarks.
    r = await client.patch(f"/api/v1/forms/{form_id}/fields/interview_overview", headers=principal, json={"value": {"text": "x"}})
    assert r.status_code == 403
    assert (await client.post(f"/api/v1/reviews/{iid}", headers=interviewer, json={"action": "review"})).status_code == 403
    assert (await client.post(f"/api/v1/reviews/{iid}", headers=principal, json={"action": "review"})).json()["status"] == "principal_review"
    assert (await client.post(f"/api/v1/reviews/{iid}", headers=principal, json={"action": "finalize"})).status_code == 409
    assert (await client.post(f"/api/v1/reviews/{iid}", headers=principal, json={"action": "request_correction"})).status_code == 422
    r = await client.post(f"/api/v1/reviews/{iid}", headers=principal, json={"action": "request_correction", "remarks": "Please clarify the overview."})
    assert r.json()["status"] == "correction_requested"

    # Interviewer corrects and resubmits.
    r = await client.patch(f"/api/v1/forms/{form_id}/fields/interview_overview", headers=interviewer, json={"value": {"text": "Clarified synthetic overview."}})
    assert r.status_code == 200
    r = await client.post(f"/api/v1/interviews/{iid}/submit", headers=interviewer)
    assert r.status_code == 200, r.text

    assert (await client.post(f"/api/v1/reviews/{iid}", headers=principal, json={"action": "review"})).json()["status"] == "principal_review"
    assert (await client.post(f"/api/v1/reviews/{iid}", headers=principal, json={"action": "review", "remarks": "Documentation complete."})).json()["status"] == "reviewed"
    assert (await client.post(f"/api/v1/reviews/{iid}", headers=principal, json={"action": "finalize"})).json()["status"] == "finalized"

    history = (await client.get(f"/api/v1/reviews/{iid}", headers=principal)).json()
    assert [h["action"] for h in history] == ["review", "request_correction", "review", "review", "finalize"]
    assert (await client.get(f"/api/v1/reviews/{iid}", headers=other)).status_code == 404

    r = await client.get(f"/api/v1/forms/{iid}/pdf", headers=principal)
    assert r.status_code == 200 and r.content.startswith(b"%PDF")
    assert (await client.get(f"/api/v1/forms/{iid}/pdf", headers=other)).status_code == 404
    assert (await client.get(f"/api/v1/recordings/{iid}/download", headers=other)).status_code == 404
    assert (await client.get(f"/api/v1/recordings/{iid}/download", headers=principal)).status_code == 200

    # The finalization action archives the approved PDF and exposes assets only to administrators.
    assert (await client.get("/api/v1/admin/storage", headers=principal)).status_code == 403
    library = await client.get("/api/v1/admin/storage?kind=pdf", headers=admin)
    assert library.status_code == 200, library.text
    pdf_assets = [item for item in library.json()["items"] if item["interview_id"] == iid]
    assert len(pdf_assets) == 1
    assert pdf_assets[0]["filename"].endswith(".pdf")
    pdf_preview = await client.get(
        f"/api/v1/admin/storage/pdf/{pdf_assets[0]['id']}",
        headers={**admin, "Range": "bytes=0-9"},
    )
    assert pdf_preview.status_code == 206
    assert pdf_preview.headers["content-range"].startswith("bytes 0-9/")
    assert pdf_preview.content.startswith(b"%PDF") or len(pdf_preview.content) == 10

    recording_library = await client.get("/api/v1/admin/storage?kind=recording", headers=admin)
    assert recording_library.status_code == 200
    recording_assets = [item for item in recording_library.json()["items"] if item["interview_id"] == iid]
    assert len(recording_assets) == 1
    recording_preview = await client.get(
        f"/api/v1/admin/storage/recording/{recording_assets[0]['id']}",
        headers={**admin, "Range": "bytes=0-9"},
    )
    assert recording_preview.status_code == 206
    assert len(recording_preview.content) == 10

    stats = (await client.get("/api/v1/interviews/stats", headers=interviewer)).json()
    assert stats["by_status"].get("finalized", 0) >= 1
    assert (await client.get("/api/v1/interviews/stats", headers=other)).json()["total"] == 0


async def test_upload_rejects_wrong_signature_and_type(client):
    admin = await login(client, ADMIN["email"], ADMIN["password"])
    await create_staff(client, admin, "up.interviewer@dps.example.com", "interviewer")
    interviewer = await login(client, "up.interviewer@dps.example.com")
    cid = (await client.post("/api/v1/candidates", headers=interviewer, json={"name": "Synthetic Child B"})).json()["id"]
    iid = (await client.post("/api/v1/interviews", headers=interviewer, json={"candidate_id": cid})).json()["id"]
    await client.post(f"/api/v1/interviews/{iid}/consent", headers=interviewer, json={"notice_version": "demo-v1", "confirmed": True})
    r = await client.post(f"/api/v1/recordings/{iid}", headers=interviewer, files={"file": ("x.exe", b"MZ" + b"\x00" * 64, "application/octet-stream")})
    assert r.status_code == 415
    r = await client.post(f"/api/v1/recordings/{iid}", headers=interviewer, files={"file": ("fake.webm", b"not audio at all" * 8, "audio/webm")})
    assert r.status_code == 415
    r = await client.post(f"/api/v1/recordings/{iid}", headers=interviewer, files={"file": ("empty.webm", b"", "audio/webm")})
    assert r.status_code in (400, 413)
