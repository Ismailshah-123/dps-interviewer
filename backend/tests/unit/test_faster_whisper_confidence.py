from app.services.transcription.faster_whisper_provider import segment_confidence


def test_confidence_is_bounded_and_monotonic():
    assert segment_confidence(None, None) is None
    high = segment_confidence(-0.1, 0.01)
    low = segment_confidence(-1.5, 0.01)
    assert 0 <= low < high <= 1


def test_non_speech_probability_lowers_confidence():
    assert segment_confidence(-0.2, 0.9) < segment_confidence(-0.2, 0.0)
