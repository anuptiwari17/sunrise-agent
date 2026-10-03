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

@app.get("/api/health")
def health_check():
    return {"status": "ok", "clinic": "Sunrise Clinic, Dehradun"}


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
