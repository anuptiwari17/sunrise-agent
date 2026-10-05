"""FastAPI server exposing POST /agent/run and frontend API endpoints."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.agent import AgentRunner
from backend.store import ClinicStore

CLINIC_JSON_PATH = pathlib.Path(__file__).resolve().parent.parent / "clinic.json"
BASE_STORE = ClinicStore.from_file(CLINIC_JSON_PATH)

app = FastAPI(
    title="Sunrise Clinic Front Desk Agent API",
    description="Deterministic REST API for front desk reception agent at Sunrise Clinic, Dehradun",
    version="1.0.0",
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for Handoff Queue items shown in the React frontend
handoff_records: List[Dict[str, Any]] = []


class AgentRunRequest(BaseModel):
    conversation_id: str
    today: str = "2026-10-01"
    turns: List[str]


class ToolCallItem(BaseModel):
    name: str
    arguments: Dict[str, Any]


class MetricsItem(BaseModel):
    turns: int
    tokens: int
    latency_ms: int


class AgentRunResponse(BaseModel):
    conversation_id: str
    tool_calls: List[ToolCallItem]
    terminal_state: str
    escalation_reason: Optional[str] = None
    patient_id: Optional[str] = None
    appointment_id: Optional[str] = None
    reply: str
    metrics: MetricsItem


@app.post("/agent/run", response_model=AgentRunResponse)
def run_agent(req: AgentRunRequest) -> Dict[str, Any]:
    """The mandatory evaluation endpoint defined in schema.md.
    
    Every run starts with a fresh isolated clone of clinic.json.
    """
    # Clone store so runs never bleed into one another
    request_store = BASE_STORE.clone()
    runner = AgentRunner(request_store)

    result = runner.run(
        conversation_id=req.conversation_id,
        today=req.today,
        turns=req.turns,
    )

    # If conversation was escalated, record it for the frontend handoff queue
    if result.get("terminal_state") == "escalated":
        caller_said = req.turns[-1] if req.turns else ""
        handoff_records.append({
            "id": f"hf_{len(handoff_records) + 1:03d}",
            "conversation_id": req.conversation_id,
            "caller_said": caller_said,
            "all_turns": req.turns,
            "reason": result.get("escalation_reason"),
            "patient_id": result.get("patient_id"),
            "tool_calls": result.get("tool_calls", []),
            "status": "open",
        })

    return result


# --- Frontend Helper Endpoints ---

# Seed initial handoffs from known escalated conversations so the UI is immediately populated
def _seed_handoffs():
    script_dirs = [
        pathlib.Path(__file__).resolve().parent.parent / "conversations",
        pathlib.Path(__file__).resolve().parent.parent / "adversarial",
    ]
    count = 1
    for sdir in script_dirs:
        if not sdir.exists():
            continue
        for p in sorted(sdir.glob("*.json")):
            try:
                import json
                with open(p, "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                if sdata.get("expected", {}).get("terminal_state") == "escalated":
                    caller_said = sdata["turns"][-1] if sdata.get("turns") else ""
                    handoff_records.append({
                        "id": f"hf_{count:03d}",
                        "conversation_id": sdata["id"],
                        "caller_said": caller_said,
                        "all_turns": sdata.get("turns", []),
                        "reason": sdata["expected"].get("escalation_reason"),
                        "patient_id": None,
                        "tool_calls": [
                            {"name": "lookup_patient", "arguments": {}},
                            {"name": "escalate_to_human", "arguments": {"reason": sdata["expected"].get("escalation_reason")}}
                        ],
                        "status": "open",
                    })
                    count += 1
            except Exception:
                pass

_seed_handoffs()


@app.api_route("/health", methods=["GET", "HEAD"])
@app.api_route("/api/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok", "clinic": "Sunrise Clinic, Dehradun"}


@app.get("/api/conversations")
def list_conversations():
    """Lists all available conversation scripts from conversations/ and adversarial/."""
    import json
    scripts = []
    dirs = [
        ("Official Baseline", pathlib.Path(__file__).resolve().parent.parent / "conversations"),
        ("Adversarial Suite", pathlib.Path(__file__).resolve().parent.parent / "adversarial"),
    ]
    for category, sdir in dirs:
        if not sdir.exists():
            continue
        for p in sorted(sdir.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                scripts.append({
                    "id": data["id"],
                    "category": category,
                    "description": data.get("description", ""),
                    "today": data.get("today", "2026-10-01"),
                    "turns": data.get("turns", []),
                    "expected": data.get("expected", {}),
                })
            except Exception:
                pass
    return {"conversations": scripts}


@app.get("/api/conversations/{conv_id}/run")
def run_specific_conversation(conv_id: str):
    """Runs a specific conversation and returns full trace with inline tool mapping."""
    import json
    dirs = [
        pathlib.Path(__file__).resolve().parent.parent / "conversations",
        pathlib.Path(__file__).resolve().parent.parent / "adversarial",
    ]
    script_data = None
    for sdir in dirs:
        p = sdir / f"{conv_id}.json"
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                script_data = json.load(f)
            break

    if not script_data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    request_store = BASE_STORE.clone()
    runner = AgentRunner(request_store)
    result = runner.run(
        conversation_id=script_data["id"],
        today=script_data.get("today", "2026-10-01"),
        turns=script_data["turns"],
    )

    return {
        "script": script_data,
        "result": result,
    }


@app.get("/api/handoffs")
def list_handoffs():
    """Returns open and resolved handoffs for Screen 1 (Handoff Queue)."""
    return {"handoffs": handoff_records}


@app.post("/api/handoffs/{handoff_id}/resolve")
def resolve_handoff(handoff_id: str):
    """Marks a handoff as resolved by clinic human staff."""
    for hf in handoff_records:
        if hf["id"] == handoff_id:
            hf["status"] = "resolved"
            return {"success": True, "handoff": hf}
    raise HTTPException(status_code=404, detail="Handoff not found")


@app.get("/api/clinic-info")
def get_clinic_info():
    """Returns clinic doctors, windows, and holidays for UI display."""
    return BASE_STORE.raw_data
