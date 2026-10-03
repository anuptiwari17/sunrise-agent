"""The six mandatory clinic tools defined in schema.md.

These tools interact directly and deterministically with the ClinicStore.
THEY NEVER CALL AN LLM.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from backend.store import ClinicStore

ALLOWED_ESCALATION_REASONS = {
    "clinical_urgent",
    "medical_advice",
    "not_authorised",
    "ambiguous_patient",
    "out_of_scope",
}


class ToolExecutionRecord:
    """Tracks a tool call for reporting in schema.md."""

    def __init__(self, name: str, arguments: Dict[str, Any], result: Any):
        self.name = name
        self.arguments = arguments
        self.result = result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "arguments": self.arguments,
        }


class ClinicTools:
    """Wrapper that executes the 6 tools on a specific isolated ClinicStore instance."""

    def __init__(self, store: ClinicStore):
        self.store = store
        self.history: List[ToolExecutionRecord] = []

    def _record(self, name: str, args: Dict[str, Any], res: Any) -> Any:
        self.history.append(ToolExecutionRecord(name, args, res))
        return res

    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Returns the list of tool calls made in schema.md format."""
        return [record.to_dict() for record in self.history]

    # --- Tool 1: search_slots ---
    def search_slots(self, doctor_id: str, date: str) -> List[str]:
        """Returns available 15-minute slot start times for doctor on date."""
        args = {"doctor_id": doctor_id, "date": date}
        # Check doctor ID
        if doctor_id not in self.store.doctors:
            return self._record("search_slots", args, [])

        slots = self.store.get_available_slots(doctor_id, date)
        return self._record("search_slots", args, slots)

    # --- Tool 2: book_appointment ---
    def book_appointment(
        self, patient_id: str, doctor_id: str, date: str, start: str
    ) -> Dict[str, Any]:
        """Books an appointment for a patient."""
        args = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "date": date,
            "start": start,
        }
        res = self.store.book_slot(patient_id, doctor_id, date, start)
        return self._record("book_appointment", args, res)

    # --- Tool 3: reschedule_appointment ---
    def reschedule_appointment(
        self,
        appointment_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        new_date: Optional[str] = None,
        new_start: Optional[str] = None,
        date: Optional[str] = None,
        start: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Moves an existing appointment to a new date and time."""
        target_date = new_date or date
        target_start = new_start or start
        
        # If appointment_id is not provided, look it up by patient_id
        actual_appointment_id = appointment_id
        if not actual_appointment_id and patient_id:
            ap = self.store.find_appointment(patient_id=patient_id)
            if ap:
                actual_appointment_id = ap["id"]

        args = {
            "appointment_id": actual_appointment_id,
            "new_date": target_date,
            "new_start": target_start,
        }
        if patient_id and not appointment_id:
            args["patient_id"] = patient_id

        if not actual_appointment_id:
            return self._record(
                "reschedule_appointment",
                args,
                {"success": False, "error": "No active appointment found to reschedule"},
            )

        res = self.store.reschedule_slot(actual_appointment_id, target_date, target_start)
        return self._record("reschedule_appointment", args, res)

    # --- Tool 4: cancel_appointment ---
    def cancel_appointment(
        self,
        appointment_id: Optional[str] = None,
        patient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancels an existing appointment."""
        actual_appointment_id = appointment_id
        if not actual_appointment_id and patient_id:
            ap = self.store.find_appointment(patient_id=patient_id)
            if ap:
                actual_appointment_id = ap["id"]

        args = {"appointment_id": actual_appointment_id}
        if patient_id and not appointment_id:
            args["patient_id"] = patient_id

        if not actual_appointment_id:
            return self._record(
                "cancel_appointment",
                args,
                {"success": False, "error": "No active appointment found to cancel"},
            )

        res = self.store.cancel_slot(actual_appointment_id)
        return self._record("cancel_appointment", args, res)

    # --- Tool 5: lookup_patient ---
    def lookup_patient(
        self, name: Optional[str] = None, phone: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Looks up a patient record. Returns matches or candidate list."""
        clean_args = {}
        if name:
            clean_args["name"] = name
        if phone:
            clean_args["phone"] = phone

        candidates = self.store.search_patients(name=name, phone=phone)
        return self._record("lookup_patient", clean_args, candidates)

    # --- Tool 6: escalate_to_human ---
    def escalate_to_human(
        self, reason: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Hands the conversation off to a human receptionist."""
        args: Dict[str, Any] = {"reason": reason}
        if context:
            args["context"] = context

        if reason not in ALLOWED_ESCALATION_REASONS:
            res = {"success": False, "error": f"Invalid escalation reason: {reason}"}
        else:
            res = {"success": True, "escalated": True, "reason": reason}

        return self._record("escalate_to_human", args, res)
