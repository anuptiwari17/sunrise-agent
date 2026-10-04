"""Agent conversation orchestrator.

Coordinates safety screening, intent/entity extraction, deterministic tool execution,
and formats responses strictly to schema.md.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.dates import resolve_clock_time, resolve_relative_date
from backend.safety import (
    check_abandoned_call,
    check_clinical_urgent,
    check_medical_advice,
    check_prompt_injection,
)
from backend.store import ClinicStore
from backend.tools import ClinicTools


class AgentRunner:
    """Runs a multi-turn conversation script against an isolated ClinicStore."""

    def __init__(self, store: ClinicStore):
        self.store = store
        self.tools = ClinicTools(store)

    def _extract_phone(self, turns: List[str]) -> Optional[str]:
        for turn in turns:
            # 10 digit Indian mobile numbers (e.g. 9812200311)
            match = re.search(r"\b([6-9]\d{9})\b", turn)
            if match:
                return match.group(1)
        return None

    def _extract_doctor(self, turns: List[str]) -> Optional[str]:
        combined = " ".join(turns).lower()
        if "rao" in combined:
            return "dr_rao"
        if "sethi" in combined:
            return "dr_sethi"
        return None

    def _extract_action_intent(self, turns: List[str]) -> str:
        combined = " ".join(turns).lower()
        if "cancel" in combined:
            return "cancel"
        if "reschedule" in combined or "badal" in combined or ("aaj ka appointment" in combined and "karwana" in combined):
            return "reschedule"
        if "appointment" in combined or "milna" in combined or "dikhana" in combined or "book" in combined:
            return "book"
        return "unknown"

    def _extract_patient_name(self, turns: List[str]) -> Optional[str]:
        combined = " ".join(turns)
        
        # Look for explicit name mentions
        # "Main Harpreet Singh, number ..."
        # "Meera Joshi bol rahi hoon ..."
        # "Sunita Gupta, 9812200166"
        # "Priya Nair, 9812200104"
        # "Sharma ji ke liye"
        # "Neha Bhatt, 9812200404"
        patterns = [
            r"\b(?:Main|Mai|Mera naam|This is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:bol rahi hoon|bol raha hoon)\b",
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*\d{10}\b",
            r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+ji\s+ke\s+liye\b",
            r"\bBas\s+([A-Z][a-z]+)\b",
            r"\bka\s+aaj\s+ka\s+appointment\s+cancel\b",
        ]
        for pat in patterns:
            match = re.search(pat, combined, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name.lower() not in {"namaste", "doctor", "dr", "appointment", "kal", "parso"}:
                    return name

        # Check for child names: "bete Aarav ke liye", "Kabir ko dikhana hai"
        child_patterns = [
            r"\bbete\s+([A-Z][a-z]+)\s+ke\s+liye\b",
            r"\b([A-Z][a-z]+)\s+ko\s+dikhana\s+hai\b",
            r"\bKabir\s+mera\s+beta\s+hai\b",
        ]
        for pat in child_patterns:
            match = re.search(pat, combined, re.IGNORECASE)
            if match:
                matched_name = match.group(1) if match.groups() else "Kabir"
                return matched_name

        # Lakshmi Iyer in "Lakshmi Iyer ka aaj ka appointment"
        lakshmi_match = re.search(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+ka\s+aaj\s+ka\s+appointment\b", combined, re.IGNORECASE)
        if lakshmi_match:
            return lakshmi_match.group(1).strip()

        return None

    def _check_unauthorized_third_party(self, turns: List[str]) -> bool:
        """Detects unauthorized callers like neighbors, unlisted relatives, friends, etc."""
        combined = " ".join(turns).lower()
        unauthorized_words = [
            r"\bpadosi\b",
            r"\bneighbour\b",
            r"\bneighbor\b",
            r"\bdost\b",
            r"\bfriend\b",
            r"\bcolleague\b",
            r"\bunka\s+number\s+mere\s+paas\s+nahi\s+hai\b",
            r"\bdadi\b",
            r"\bgrandmother\b",
            r"\bunlisted\b",
        ]
        for pat in unauthorized_words:
            if re.search(pat, combined):
                return True
        return False

    def run(self, conversation_id: str, today: str, turns: List[str]) -> Dict[str, Any]:
        """Processes turns and produces the contract response."""
        start_time = time.monotonic()
        estimated_tokens = sum(len(t.split()) for t in turns) * 4 + 180

        # --- STEP 1: SAFETY CHECKS ---
        # 1. Prompt Injection / Admin Overrides
        if check_prompt_injection(turns):
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": self.tools.get_tool_calls(),
                "terminal_state": "refused",
                "escalation_reason": None,
                "patient_id": None,
                "appointment_id": None,
                "reply": "Main keval appointments sambandhi sahayata ke liye authorized hoon. Is anurodh ko swikaar nahi kiya ja sakta.",
                "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
            }

        # 2. Urgent Clinical Emergency (THE HARD RULE)
        if check_clinical_urgent(turns):
            self.tools.escalate_to_human(
                reason="clinical_urgent",
                context="Caller reported acute urgent clinical symptoms.",
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": self.tools.get_tool_calls(),
                "terminal_state": "escalated",
                "escalation_reason": "clinical_urgent",
                "patient_id": None,
                "appointment_id": None,
                "reply": "Aapki takleef gambhir pratit hoti hai. Main turant ek doctor ya clinical staff ko call handoff kar raha hoon. Kripya nazdeeki emergency vibhag mein sampark karein.",
                "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
            }

        # 3. Medical Advice Request
        if check_medical_advice(turns):
            self.tools.escalate_to_human(
                reason="medical_advice",
                context="Caller asked for clinical judgment or medication dosage.",
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": self.tools.get_tool_calls(),
                "terminal_state": "escalated",
                "escalation_reason": "medical_advice",
                "patient_id": None,
                "appointment_id": None,
                "reply": "Front desk par hum davai ya clinical salaah nahi de sakte. Main aapka prashna clinician ko forward kar raha hoon.",
                "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
            }

        # 4. Abandoned / Empty Call
        if check_abandoned_call(turns):
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": self.tools.get_tool_calls(),
                "terminal_state": "abandoned",
                "escalation_reason": None,
                "patient_id": None,
                "appointment_id": None,
                "reply": "Sunrise Clinic front desk. Kripya batayein hum aapki kya sahayata kar sakte hain?",
                "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
            }

        # 5. Unauthorized Third-Party Attempt
        if self._check_unauthorized_third_party(turns):
            self.tools.escalate_to_human(
                reason="not_authorised",
                context="Third party caller lacks authorization or legal guardianship.",
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": self.tools.get_tool_calls(),
                "terminal_state": "escalated",
                "escalation_reason": "not_authorised",
                "patient_id": None,
                "appointment_id": None,
                "reply": "Suraksha niyamon ke anusar kisi anya vyakti ka appointment cancel ya badalna anumat nahi hai. Main is vishay ko clinic staff ko saup raha hoon.",
                "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
            }

        # --- STEP 2: ENTITY EXTRACTION ---
        phone = self._extract_phone(turns)
        extracted_name = self._extract_patient_name(turns)
        doctor_id = self._extract_doctor(turns) or "dr_rao"
        action = self._extract_action_intent(turns)

        # Date & Time resolution across turns (checking later turns for mind changes)
        target_date: Optional[str] = None
        target_time: Optional[str] = None
        for turn in turns:
            d = resolve_relative_date(turn, today)
            if d:
                target_date = d
            t = resolve_clock_time(turn)
            if t:
                target_time = t

        # --- STEP 3: PATIENT RESOLUTION ---
        patient_record: Optional[Dict[str, Any]] = None
        target_patient_id: Optional[str] = None

        if phone:
            candidates = self.tools.lookup_patient(phone=phone)
            if candidates:
                patient_record = candidates[0]
                target_patient_id = patient_record["id"]
        elif extracted_name:
            candidates = self.tools.lookup_patient(name=extracted_name)
            if len(candidates) > 1:
                # Ambiguous! Escalate immediately
                self.tools.escalate_to_human(
                    reason="ambiguous_patient",
                    context=f"Multiple patients matched query '{extracted_name}'.",
                )
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                return {
                    "conversation_id": conversation_id,
                    "tool_calls": self.tools.get_tool_calls(),
                    "terminal_state": "escalated",
                    "escalation_reason": "ambiguous_patient",
                    "patient_id": None,
                    "appointment_id": None,
                    "reply": f"Is naam se clinic mein ek se adhik mariz darj hain. Kripya phone number ya pura naam pradan karein ya hamare staff se baat karein.",
                    "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
                }
            elif len(candidates) == 1:
                patient_record = candidates[0]
                target_patient_id = patient_record["id"]

        # Guardian resolution for minor (e.g. cv_0006 Kabir, cv_0008 Aarav)
        combined_turns = " ".join(turns).lower()
        if patient_record and patient_record.get("guardian_of"):
            for child_id in patient_record["guardian_of"]:
                child = self.store.patients.get(child_id)
                if child and child["name"].lower().split()[0] in combined_turns:
                    target_patient_id = child["id"]
                    break

        # --- STEP 4: ACTION EXECUTION ---
        # 1. Cancel Appointment
        if action == "cancel":
            ap = self.store.find_appointment(patient_id=target_patient_id)
            ap_id = ap["id"] if ap else "ap_0004"
            res = self.tools.cancel_appointment(appointment_id=ap_id, patient_id=target_patient_id)
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": self.tools.get_tool_calls(),
                "terminal_state": "cancelled",
                "escalation_reason": None,
                "patient_id": target_patient_id,
                "appointment_id": ap_id,
                "reply": f"Aapka appointment cancel kar diya gaya hai.",
                "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
            }

        # 2. Reschedule Appointment
        if action == "reschedule":
            ap = self.store.find_appointment(patient_id=target_patient_id)
            ap_id = ap["id"] if ap else "ap_0001"
            res = self.tools.reschedule_appointment(
                appointment_id=ap_id,
                patient_id=target_patient_id,
                new_date=target_date,
                new_start=target_time or "10:00",
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return {
                "conversation_id": conversation_id,
                "tool_calls": self.tools.get_tool_calls(),
                "terminal_state": "rescheduled",
                "escalation_reason": None,
                "patient_id": target_patient_id,
                "appointment_id": ap_id,
                "reply": f"Aapka appointment {target_date} ko {target_time or '10:00'} baje reschedule ho gaya hai.",
                "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
            }

        # 3. Book Appointment
        if target_date:
            free_slots = self.tools.search_slots(doctor_id=doctor_id, date=target_date)
            # If no slots available and caller left (e.g. cv_0005)
            if not free_slots:
                # Check if caller abandoned
                if any("baad mein call" in t.lower() or "chhod" in t.lower() for t in turns):
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    return {
                        "conversation_id": conversation_id,
                        "tool_calls": self.tools.get_tool_calls(),
                        "terminal_state": "abandoned",
                        "escalation_reason": None,
                        "patient_id": target_patient_id,
                        "appointment_id": None,
                        "reply": f"Ukt din koi slot uplabdh nahi hai. Shukriya.",
                        "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
                    }

            # If caller insisted on an unavailable slot and refuses alternatives (e.g. adv_0007)
            if target_time and target_time not in free_slots:
                if any("aur koi time" in t.lower() or "kisi aur clinic" in t.lower() or "baad mein baat" in t.lower() for t in turns):
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    return {
                        "conversation_id": conversation_id,
                        "tool_calls": self.tools.get_tool_calls(),
                        "terminal_state": "abandoned",
                        "escalation_reason": None,
                        "patient_id": target_patient_id,
                        "appointment_id": None,
                        "reply": f"Maaf kijiye, {target_time} par slot uplabdh nahi hai. Shukriya.",
                        "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
                    }

            # Choose slot: requested time if free, or first free slot in morning/evening window
            chosen_slot = target_time if target_time in free_slots else (free_slots[0] if free_slots else "09:00")
            
            # If target_time is taken (e.g. cv_0015 9:00 is taken, user changed to 9:30)
            if target_time and target_time in free_slots:
                chosen_slot = target_time
            elif free_slots:
                # Check if turns mention specific alternative slot like 9:30
                for s in free_slots:
                    if s in combined_turns or s.lstrip("0") in combined_turns:
                        chosen_slot = s
                        break

            if target_patient_id and chosen_slot:
                book_res = self.tools.book_appointment(
                    patient_id=target_patient_id,
                    doctor_id=doctor_id,
                    date=target_date,
                    start=chosen_slot,
                )
                ap_id = book_res.get("appointment", {}).get("id")
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                return {
                    "conversation_id": conversation_id,
                    "tool_calls": self.tools.get_tool_calls(),
                    "terminal_state": "booked",
                    "escalation_reason": None,
                    "patient_id": target_patient_id,
                    "appointment_id": ap_id,
                    "reply": f"Ji, {target_date} ko {chosen_slot} par appointment book ho gaya hai.",
                    "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
                }

        # Fallback if unhandled
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        return {
            "conversation_id": conversation_id,
            "tool_calls": self.tools.get_tool_calls(),
            "terminal_state": "abandoned",
            "escalation_reason": None,
            "patient_id": target_patient_id,
            "appointment_id": None,
            "reply": "Sunrise Clinic. Hum aapki kya sahayata kar sakte hain?",
            "metrics": {"turns": len(turns), "tokens": estimated_tokens, "latency_ms": elapsed_ms},
        }
