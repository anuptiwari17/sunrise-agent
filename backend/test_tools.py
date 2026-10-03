"""Unit tests for ClinicStore and ClinicTools."""

import pathlib
import pytest
from backend.store import ClinicStore
from backend.tools import ClinicTools

CLINIC_PATH = pathlib.Path(__file__).resolve().parent.parent / "clinic.json"


@pytest.fixture
def store():
    return ClinicStore.from_file(CLINIC_PATH)


@pytest.fixture
def tools(store):
    return ClinicTools(store)


def test_holiday_has_no_slots(tools):
    # 2026-10-02 is clinic holiday
    slots = tools.search_slots("dr_rao", "2026-10-02")
    assert slots == []


def test_sunday_has_no_slots(tools):
    # 2026-10-04 is Sunday
    slots = tools.search_slots("dr_rao", "2026-10-04")
    assert slots == []


def test_doctor_leave_has_no_slots(tools):
    # Dr. Sethi is on leave 2026-10-05 to 2026-10-07
    slots = tools.search_slots("dr_sethi", "2026-10-05")
    assert slots == []
    slots_rao = tools.search_slots("dr_rao", "2026-10-05")
    assert len(slots_rao) > 0  # Rao is working


def test_overlapping_windows_deduplication(store):
    # Dr. Rao on Monday (2026-10-05 is Mon, but let's test 2026-10-12 Mon)
    # Windows are 09:00-12:00 and 11:45-15:00
    slots = store.get_all_doctor_slots("dr_rao", "2026-10-12")
    assert "11:45" in slots
    # Must not have duplicates
    assert len(slots) == len(set(slots))


def test_double_booking_rejected(tools):
    # Book a slot
    res1 = tools.book_appointment("pt_0001", "dr_rao", "2026-10-03", "09:00")
    assert res1["success"] is True

    # Try booking the exact same slot again
    res2 = tools.book_appointment("pt_0002", "dr_rao", "2026-10-03", "09:00")
    assert res2["success"] is False
    assert "unavailable or already booked" in res2["error"]


def test_lookup_patient_by_phone(tools):
    res = tools.lookup_patient(phone="9812200311")
    assert len(res) == 1
    assert res[0]["name"] == "Harpreet Singh"
    assert res[0]["id"] == "pt_0013"


def test_lookup_patient_ambiguous_surname(tools):
    # "Sharma" matches Rajesh Kumar Sharma, R. K. Sharma, Rajesh Sharma
    res = tools.lookup_patient(name="Sharma")
    assert len(res) == 3
    ids = {p["id"] for p in res}
    assert ids == {"pt_0001", "pt_0002", "pt_0003"}


def test_lookup_patient_ambiguous_first_name(tools):
    # "Priya" matches Priya Nair and Priya Menon
    res = tools.lookup_patient(name="Priya")
    assert len(res) == 2


def test_guardian_authorization(store):
    # Sunita Gupta (pt_0008) is guardian of Aarav (pt_0006) and Arjun (pt_0007)
    assert store.is_guardian_authorized("pt_0008", "pt_0006") is True
    assert store.is_guardian_authorized("pt_0008", "pt_0007") is True

    # Mohit Negi (pt_0020) is NOT guardian of Lakshmi Iyer (pt_0012)
    assert store.is_guardian_authorized("pt_0020", "pt_0012") is False


def test_reschedule_appointment(tools):
    # Reschedule existing ap_0001 (Rajesh Kumar Sharma) from 2026-10-01 to 2026-10-03 10:00
    res = tools.reschedule_appointment("ap_0001", new_date="2026-10-03", new_start="10:00")
    assert res["success"] is True
    assert res["appointment"]["date"] == "2026-10-03"
    assert res["appointment"]["start"] == "10:00"


def test_cancel_appointment(tools):
    # Cancel ap_0004
    res = tools.cancel_appointment("ap_0004")
    assert res["success"] is True
    assert res["appointment"]["status"] == "cancelled"
