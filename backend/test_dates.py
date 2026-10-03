"""Unit tests for deterministic date and Hinglish time parsing."""

from backend.dates import resolve_relative_date, resolve_clock_time

TODAY = "2026-10-01"  # Thursday


def test_cv_0001_saturday():
    date = resolve_relative_date("Shanivaar subah, 3 tareekh.", TODAY)
    assert date == "2026-10-03"


def test_cv_0002_mind_change():
    text = "Mangalwar 6 tareekh ko... nahi nahi, budhwar kar dijiye, 7 tareekh."
    date = resolve_relative_date(text, TODAY)
    assert date == "2026-10-07"


def test_cv_0003_reschedule():
    text_date = "Mera aaj ka appointment hai Dr. Rao ke saath, use Saturday karwana hai."
    date = resolve_relative_date(text_date, TODAY)
    assert date == "2026-10-03"

    text_time = "Subah 10 baje theek hai."
    time = resolve_clock_time(text_time)
    assert time == "10:00"


def test_cv_0005_sunday():
    text = "Sunday ko, 4 tareekh, Dr. Rao se milna hai."
    date = resolve_relative_date(text, TODAY)
    assert date == "2026-10-04"


def test_cv_0008_evening():
    text = "8 tareekh ko shaam ko."
    date = resolve_relative_date(text, TODAY)
    assert date == "2026-10-08"


def test_cv_0012_parso_gyarah_baje():
    text = "Dr. Rao ke paas parso gyarah baje aa sakta hoon?"
    date = resolve_relative_date(text, TODAY)
    assert date == "2026-10-03"
    time = resolve_clock_time(text)
    assert time == "11:00"


def test_cv_0015_slot_switch():
    time1 = resolve_clock_time("8 tareekh subah 9 baje Dr. Rao ke saath.")
    assert time1 == "09:00"
    time2 = resolve_clock_time("Accha, toh 9:30 kar dijiye.")
    assert time2 == "09:30"
