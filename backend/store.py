"""In-memory clinic data store with concurrency locking and fresh per-request isolation.

Loads clinic.json and provides isolated, thread-safe access to:
- Clinic metadata
- Doctors and working windows
- Holidays and doctor leaves
- Patients and guardians
- Appointments (with atomic booking and cancellation)
"""

from __future__ import annotations

import copy
import datetime
import json
import pathlib
import threading
from typing import Any, Dict, List, Optional


class ClinicStore:
    """Thread-safe transactional store initialized from clinic.json."""

    def __init__(self, clinic_data: Dict[str, Any]):
        self._lock = threading.RLock()
        self.raw_data = clinic_data
        self.clinic = clinic_data.get("clinic", {})
        self.doctors = {doc["id"]: doc for doc in clinic_data.get("doctors", [])}
        self.holidays = set(clinic_data.get("holidays", []))
        self.patients = {p["id"]: p for p in clinic_data.get("patients", [])}
        
        # Clone appointments so modifications in one request never touch another
        self.appointments = [copy.deepcopy(ap) for ap in clinic_data.get("appointments", [])]

    @classmethod
    def from_file(cls, path: pathlib.Path | str) -> ClinicStore:
        """Create a fresh isolated store by loading clinic.json."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def clone(self) -> ClinicStore:
        """Create an isolated clone of this store for a single conversation run."""
        with self._lock:
            return ClinicStore(copy.deepcopy(self.raw_data))

    # --- Doctors & Working Hours ---
    def get_doctor(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        return self.doctors.get(doctor_id)

    def is_holiday(self, date_str: str) -> bool:
        return date_str in self.holidays

    def is_doctor_on_leave(self, doctor_id: str, date_str: str) -> bool:
        doc = self.get_doctor(doctor_id)
        if not doc:
            return False
        return date_str in doc.get("leave_dates", [])

    # --- Slot Utilities ---
    @staticmethod
    def _add_minutes(time_str: str, minutes: int) -> str:
        t = datetime.datetime.strptime(time_str, "%H:%M")
        t_plus = t + datetime.timedelta(minutes=minutes)
        return t_plus.strftime("%H:%M")

    @staticmethod
    def get_weekday_abbr(date_str: str) -> str:
        """Returns 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'."""
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%a")

    def get_all_doctor_slots(self, doctor_id: str, date_str: str) -> List[str]:
        """Calculates all theoretical 15-minute slot starts for a doctor on a date.
        
        Handles overlapping windows (e.g. Dr. Rao's Monday shift) by taking the
        union of intervals and deduplicating.
        """
        doc = self.get_doctor(doctor_id)
        if not doc:
            return []

        # Check holiday
        if self.is_holiday(date_str):
            return []

        # Check doctor leave
        if self.is_doctor_on_leave(doctor_id, date_str):
            return []

        weekday = self.get_weekday_abbr(date_str)
        # Sunday check: no windows defined for Sunday
        if weekday == "Sun":
            return []

        slot_minutes = self.clinic.get("slot_minutes", 15)
        slots_set = set()

        for window in doc.get("windows", []):
            if window.get("day") != weekday:
                continue
            cur = window["start"]
            end = window["end"]
            while True:
                next_cur = self._add_minutes(cur, slot_minutes)
                if next_cur > end:
                    break
                slots_set.add(cur)
                cur = next_cur

        return sorted(list(slots_set))

    def get_available_slots(self, doctor_id: str, date_str: str) -> List[str]:
        """Returns free slot starts for doctor on date, excluding existing bookings."""
        with self._lock:
            all_slots = self.get_all_doctor_slots(doctor_id, date_str)
            if not all_slots:
                return []

            # Find active bookings for this doctor and date
            booked_starts = {
                ap["start"]
                for ap in self.appointments
                if ap.get("doctor_id") == doctor_id
                and ap.get("date") == date_str
                and ap.get("status") == "booked"
            }

            return [s for s in all_slots if s not in booked_starts]

    # --- Atomic Appointment Operations ---
    def _generate_next_appointment_id(self) -> str:
        """Generates next ID monotonically like ap_0026, ap_0027."""
        max_num = 0
        for ap in self.appointments:
            ap_id = ap.get("id", "")
            if ap_id.startswith("ap_"):
                try:
                    num = int(ap_id.split("_")[1])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    pass
        return f"ap_{max_num + 1:04d}"

    def book_slot(
        self, patient_id: str, doctor_id: str, date_str: str, start_time: str
    ) -> Dict[str, Any]:
        """Atomically checks and books a slot."""
        with self._lock:
            # 1. Validate patient exists
            if patient_id not in self.patients:
                return {"success": False, "error": f"Patient '{patient_id}' not found"}

            # 2. Validate doctor exists
            if doctor_id not in self.doctors:
                return {"success": False, "error": f"Doctor '{doctor_id}' not found"}

            # 3. Check if date is holiday
            if self.is_holiday(date_str):
                return {"success": False, "error": f"Clinic is closed on holiday {date_str}"}

            # 4. Check if doctor on leave
            if self.is_doctor_on_leave(doctor_id, date_str):
                return {"success": False, "error": f"Doctor {doctor_id} is on leave on {date_str}"}

            # 5. Check if Sunday
            if self.get_weekday_abbr(date_str) == "Sun":
                return {"success": False, "error": "Clinic is closed on Sundays"}

            # 6. Check slot availability
            free_slots = self.get_available_slots(doctor_id, date_str)
            if start_time not in free_slots:
                return {
                    "success": False,
                    "error": f"Slot {start_time} on {date_str} for {doctor_id} is unavailable or already booked",
                }

            # 7. Create appointment
            slot_minutes = self.clinic.get("slot_minutes", 15)
            end_time = self._add_minutes(start_time, slot_minutes)
            new_id = self._generate_next_appointment_id()

            appointment = {
                "id": new_id,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "date": date_str,
                "start": start_time,
                "end": end_time,
                "status": "booked",
            }
            self.appointments.append(appointment)
            return {"success": True, "appointment": appointment}

    def find_appointment(
        self,
        appointment_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Finds an active booked appointment matching the criteria."""
        with self._lock:
            for ap in self.appointments:
                if ap.get("status") != "booked":
                    continue
                if appointment_id and ap.get("id") == appointment_id:
                    return ap
                if patient_id and ap.get("patient_id") == patient_id:
                    if date_str and ap.get("date") != date_str:
                        continue
                    return ap
            return None

    def reschedule_slot(
        self, appointment_id: str, new_date_str: str, new_start_time: str
    ) -> Dict[str, Any]:
        """Atomically moves an appointment to a new date/time."""
        with self._lock:
            ap = self.find_appointment(appointment_id=appointment_id)
            if not ap:
                return {"success": False, "error": f"Active appointment '{appointment_id}' not found"}

            doctor_id = ap["doctor_id"]

            # Check new slot availability
            free_slots = self.get_available_slots(doctor_id, new_date_str)
            if new_start_time not in free_slots:
                return {
                    "success": False,
                    "error": f"Slot {new_start_time} on {new_date_str} for {doctor_id} is unavailable",
                }

            # Move slot
            slot_minutes = self.clinic.get("slot_minutes", 15)
            ap["date"] = new_date_str
            ap["start"] = new_start_time
            ap["end"] = self._add_minutes(new_start_time, slot_minutes)

            return {"success": True, "appointment": ap}

    def cancel_slot(self, appointment_id: str) -> Dict[str, Any]:
        """Cancels an existing appointment."""
        with self._lock:
            ap = self.find_appointment(appointment_id=appointment_id)
            if not ap:
                return {"success": False, "error": f"Active appointment '{appointment_id}' not found"}

            ap["status"] = "cancelled"
            return {"success": True, "appointment": ap}

    # --- Patient Lookup ---
    def search_patients(
        self, name: Optional[str] = None, phone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Looks up patients. Returns matches or candidate list."""
        with self._lock:
            # 1. Exact phone match takes precedence
            if phone:
                clean_phone = "".join(filter(str.isdigit, phone))
                matched = [p for p in self.patients.values() if p.get("phone") == clean_phone]
                if matched:
                    return matched

            # 2. Name search
            if name:
                query = name.strip().lower()
                query_tokens = [t for t in query.replace(".", " ").split() if len(t) > 1]
                matches = []
                for p in self.patients.values():
                    p_name = p.get("name", "").lower()
                    # Exact full name match
                    if p_name == query:
                        matches.append(p)
                        continue
                    # Match if query tokens are part of patient name
                    if any(token in p_name for token in query_tokens):
                        matches.append(p)

                return matches

            return []

    def is_guardian_authorized(self, caller_patient_id: str, target_patient_id: str) -> bool:
        """Checks if caller is the patient or a registered guardian of the target."""
        if caller_patient_id == target_patient_id:
            return True
        caller = self.patients.get(caller_patient_id)
        if not caller:
            return False
        return target_patient_id in caller.get("guardian_of", [])
