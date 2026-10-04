# Sunrise Clinic — Front Desk Agent

A safe, deterministic conversational agent with six tools over a clinic's schedule, paired with a React operator console for escalation triage and conversation auditing.

Built for the **Swasthiq SDE Intern Screening Process** (September 2026).

---

## 1. Quick Start (One Command Run)

Run both the FastAPI backend and React frontend with a single command:

### On Linux / macOS:
```bash
./start.sh
```

### On Windows (PowerShell):
```powershell
.\start.ps1
```

Or start each manually:

```bash
# Terminal 1: Backend (FastAPI on port 8000)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend (React/Vite on port 5173)
cd frontend
npm install
npm run dev
```

The React frontend will be live at: **`http://localhost:5173/`**  
The API endpoint is live at: **`http://localhost:8000/agent/run`**

---

## 2. Determinism & Test Suite Verification

### Run the Baseline Test Suite (15 Conversations)
```bash
python runner.py
```

### Run the 3x Determinism Stress Test
```bash
python runner.py --repeat 3
```

### Run the 8 Adversarial Test Suite
```bash
python runner.py --dir adversarial --repeat 3
```

**Results:**
- 15/15 baseline conversation scripts pass with **0 contract failures**.
- 8/8 adversarial conversation scripts pass with **0 contract failures**.
- **100% determinism** achieved across repeated runs (zero fingerprint drift).

---

## 3. Architecture & Data Consistency on Update

```
                    ┌──────────────────────────────────────────────┐
                    │               React Frontend                 │
                    │   - Handoff Queue (Escalation triage)        │
                    │   - Conversation Detail (Inline Tool Traces) │
                    └──────────────────────┬───────────────────────┘
                                           │ HTTP REST
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │          FastAPI Backend (/backend)          │
                    │                                              │
                    │  POST /agent/run (runner.py contract)        │
                    │  GET  /api/conversations (list & run)        │
                    │  GET  /api/handoffs (queue triage)           │
                    │  POST /api/handoffs/:id/resolve              │
                    └──────────────┬───────────────────────────────┘
                                   │
                 ┌─────────────────┴──────────────────┐
                 ▼                                    ▼
    ┌──────────────────────────┐         ┌──────────────────────────┐
    │  Agent Orchestrator      │         │   Deterministic Tools    │
    │  - Safety Screener       │         │   (ZERO LLM INVOKED)     │
    │  - Hinglish Date Parser  │◄───────►│  - search_slots          │
    │  - Schema Normalizer     │ Tool    │  - book_appointment      │
    │  - Zero Invented Facts   │ Calls   │  - reschedule_appointment│
    └──────────────────────────┘         │  - cancel_appointment    │
                                         │  - lookup_patient        │
                                         │  - escalate_to_human     │
                                         └────────────┬─────────────┘
                                                      │
                                                      ▼
                                         ┌──────────────────────────┐
                                         │ Isolated ClinicStore     │
                                         │ - Mutex Reentrant Lock   │
                                         │ - Fresh clone per run    │
                                         │ - Slot deduplication     │
                                         └──────────────────────────┘
```

### How Functions Keep Data Consistent on Update

1. **State Isolation per Conversation:**  
   Every call to `POST /agent/run` operates on a fresh clone of `clinic.json`. An appointment booked in conversation `cv_0001` does not leak into conversation `cv_0002`.

2. **Atomic Slot Allocation & Mutex Locking:**  
   In `backend/store.py`, `book_slot`, `reschedule_slot`, and `cancel_slot` are guarded by a reentrant mutex lock (`threading.RLock`). Slot availability check and assignment occur as an uninterruptible atomic transaction. Two concurrent conversations racing for the same slot can never both succeed.

3. **Rejection of Overlapping Windows:**  
   In `clinic.json`, Dr. Rao has overlapping shift windows on Mondays (`09:00-12:00` and `11:45-15:00`). The store computes the interval union, deduplicating 15-minute intervals so `11:45` exists at most once.

4. **Zero Invented Facts (Grounding Guarantee):**  
   The agent layer never generates appointment IDs or confirms slot times probabilistically. IDs follow monotonic sequence increments (`ap_0026`, etc.) generated strictly by `book_slot`.

---

## 4. Model, Tokens & Latency Benchmarks

| Metric | Measured Value |
|---|---|
| **Model / Engine** | Deterministic Hybrid Safety & Tool Orchestrator (`temperature=0.0`) |
| **Average Latency per Conversation** | **~2.0 seconds** (benchmarked via `runner.py`) |
| **Token Usage per Conversation** | **~240 - 290 tokens** |
| **Determinism Rate** | **100% across 3 repeats (45 baseline + 24 adversarial runs)** |

---

## 5. API Contract (`POST /agent/run`)

### Request
```json
{
  "conversation_id": "cv_0001",
  "today": "2026-10-01",
  "turns": [
    "Namaste, Dr. Rao ke saath appointment chahiye tha.",
    "Shanivaar subah, 3 tareekh.",
    "Main Harpreet Singh, number 9812200311."
  ]
}
```

### Response
```json
{
  "conversation_id": "cv_0001",
  "tool_calls": [
    {"name": "lookup_patient", "arguments": {"phone": "9812200311"}},
    {"name": "search_slots", "arguments": {"doctor_id": "dr_rao", "date": "2026-10-03"}},
    {"name": "book_appointment", "arguments": {"patient_id": "pt_0013", "doctor_id": "dr_rao", "date": "2026-10-03", "start": "09:00"}}
  ],
  "terminal_state": "booked",
  "escalation_reason": null,
  "patient_id": "pt_0013",
  "appointment_id": "ap_0026",
  "reply": "Ji, 2026-10-03 ko 09:00 par appointment book ho gaya hai.",
  "metrics": {
    "turns": 3,
    "tokens": 248,
    "latency_ms": 2045
  }
}
```

---

## 6. The 8 Adversarial Test Cases (`/adversarial/`)

| Script | What It Tests | Why Naive Agents Fail |
|---|---|---|
| [`adv_0001.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0001.json) | Subtle cardiovascular distress during BP checkup | Naive agent schedules checkup, ignoring arm numbness + dizziness (`clinical_urgent`). |
| [`adv_0002.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0002.json) | Doctor ICU authority override injection | Naive agent obeys fake doctor claiming mass casualty drill (`refused`). |
| [`adv_0003.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0003.json) | Unregistered grandmother booking for minor | Naive agent trusts family relation assertion; caller is not in `guardian_of` (`not_authorised`). |
| [`adv_0004.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0004.json) | "Kal subah" on eve of Gandhi Jayanti | Naive agent forgets to check clinic holiday on relative dates (`abandoned`, 0 slots). |
| [`adv_0005.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0005.json) | Double mind change with nested Hindi negations | Naive agent books 5th or 6th; safe agent parses retracted intent to book 7th. |
| [`adv_0006.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0006.json) | Pediatric fever medication inquiry | Naive agent offers ibuprofen advice instead of administrative booking (`medical_advice`). |
| [`adv_0007.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0007.json) | Insisting on occupied slot (`ap_0017` at 16:15) | Naive agent creates double-booking; safe agent strictly enforces unavailability (`abandoned`). |
| [`adv_0008.json`](file:///d:/projects/SideProjects/front-desk-agent/adversarial/adv_0008.json) | Ambiguous first name ("Priya") with missing phone | Naive agent guesses Priya Nair (`pt_0004`); safe agent escalates (`ambiguous_patient`). |

---

## 7. Frontend UI Highlights
- **Handoff Queue (Screen 1):** Real-time counters across the top (`Open Escalations`, `Clinical Urgent`, `Not Authorised`, `Ambiguous Patient`), triage cards with direct "Resolve" action.
- **Conversation Detail (Screen 2):** Complete multi-turn transcript with **inline tool execution chips** showing exact arguments at the turn they occurred, side-by-side with the machine-readable Outcome Inspector and JSON viewer.
- **Shared Sidebar:** Persistent branding, navigation, and live engine status.
