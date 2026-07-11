from core.utils.text import srt_timestamp, wrap_subtitle


def test_srt_timestamp_format() -> None:
    assert srt_timestamp(65.432) == "00:01:05,432"


def test_wrap_subtitle_returns_lines() -> None:
    lines = wrap_subtitle("Nunca respondas si el bosque dice tu nombre", 18)

    assert len(lines) >= 2
    assert all(lines)
