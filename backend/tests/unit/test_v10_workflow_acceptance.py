from app.models.models import InterviewStatus
from app.services.workflow import ALLOWED


def test_full_happy_path_is_represented_in_workflow_graph():
    path = [
        InterviewStatus.DRAFT.value,
        InterviewStatus.RECORDING.value,
        InterviewStatus.UPLOADING.value,
        InterviewStatus.UPLOADED.value,
        InterviewStatus.QUEUED.value,
        InterviewStatus.TRANSCRIBING.value,
        InterviewStatus.TRANSCRIPT_READY.value,
        InterviewStatus.SUMMARIZING.value,
        InterviewStatus.FORM_DRAFT_READY.value,
        InterviewStatus.NEEDS_REVIEW.value,
        InterviewStatus.SUBMITTED.value,
        InterviewStatus.PRINCIPAL_REVIEW.value,
        InterviewStatus.REVIEWED.value,
        InterviewStatus.FINALIZED.value,
    ]
    assert all(b in ALLOWED[a] for a, b in zip(path, path[1:]))


def test_correction_loop_returns_to_needs_review():
    assert InterviewStatus.CORRECTION_REQUESTED.value in ALLOWED[InterviewStatus.PRINCIPAL_REVIEW.value]
    assert InterviewStatus.NEEDS_REVIEW.value in ALLOWED[InterviewStatus.CORRECTION_REQUESTED.value]


def test_failed_processing_can_recover_to_queue():
    assert InterviewStatus.QUEUED.value in ALLOWED[InterviewStatus.FAILED.value]


def test_terminal_states_have_no_outgoing_transitions():
    assert ALLOWED[InterviewStatus.FINALIZED.value] == set()
    assert ALLOWED[InterviewStatus.CANCELLED.value] == set()
