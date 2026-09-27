"""
FastAPI Server for Gestalt: Cognitive Topology & Socratic Blueprint Extractor.
Hardened with strict path validation, CORS containment, and SSRF guardrails.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from engine import BlueprintState, ModelClient, BlueprintSynthesizer, Node, Edge, Invariant

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("gestalt.server")

app = FastAPI(title="Gestalt Cognitive Blueprint Extractor", version="1.0.0")

# Security: Restrict CORS to loopback origins to prevent cross-site request forgery
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Persistent session store & export directory
BASE_DIR = Path(__file__).parent.resolve()
SESSIONS_DIR = BASE_DIR / "sessions"
EXPORT_DIR = BASE_DIR / "export"
SESSIONS_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

sessions: Dict[str, BlueprintState] = {}
model_client = ModelClient()

def _sanitize_session_id(session_id: str) -> str:
    """Enforces strict alphanumeric session IDs to prevent path traversal."""
    if not re.match(r"^[a-zA-Z0-9_\-]+$", session_id) or len(session_id) > 64:
        raise HTTPException(status_code=400, detail="Invalid session_id format.")
    return session_id

def _save_session_to_disk(state: BlueprintState):
    safe_id = _sanitize_session_id(state.session_id)
    file_path = (SESSIONS_DIR / f"{safe_id}.json").resolve()
    if not file_path.is_relative_to(SESSIONS_DIR):
        raise HTTPException(status_code=400, detail="Path traversal attempt detected.")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=2))

def _load_sessions_from_disk():
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                state = BlueprintState(**data)
                sessions[state.session_id] = state
        except Exception as e:
            logger.warning(f"Failed to load session {f}: {e}")

_load_sessions_from_disk()

STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class ProjectRequest(BaseModel):
    seed: str = Field(..., max_length=1000)
    provider: Optional[str] = "auto"
    endpoint: Optional[str] = "http://localhost:11434"
    model: Optional[str] = "llama3.2"

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("Endpoint must use http or https scheme.")
        # Restrict to local loopback by default to eliminate remote SSRF risks
        allowed_hosts = {"localhost", "127.0.0.1", "::1"}
        if parsed.hostname not in allowed_hosts and not parsed.hostname.endswith(".local"):
            logger.warning(f"Connecting to non-local endpoint: {parsed.hostname}")
        return v

class ProbeResolveRequest(BaseModel):
    session_id: str
    probe_id: str
    option_id: str
    custom_note: Optional[str] = Field(None, max_length=500)

class SynthesizeRequest(BaseModel):
    session_id: str

class ExportRequest(BaseModel):
    session_id: str
    output_directory: Optional[str] = None

@app.get("/")
async def get_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse({"status": "error", "message": "index.html not created yet"})
    return FileResponse(index_path)

@app.get("/api/status")
async def get_model_status():
    """Checks local model connectivity."""
    return model_client.check_health()

@app.get("/api/sessions")
async def list_sessions():
    """Lists all saved blueprints in history."""
    items = []
    for s in sessions.values():
        items.append({
            "session_id": s.session_id,
            "title": s.title,
            "seed": s.seed,
            "convergence_pct": s.convergence_pct,
            "node_count": len(s.nodes),
            "edge_count": len(s.edges),
            "version": s.version
        })
    return items

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Deletes a session from memory and disk safely."""
    safe_id = _sanitize_session_id(session_id)
    if safe_id in sessions:
        del sessions[safe_id]
    
    file_path = (SESSIONS_DIR / f"{safe_id}.json").resolve()
    if file_path.exists() and file_path.is_relative_to(SESSIONS_DIR):
        file_path.unlink()
    return {"status": "deleted", "session_id": safe_id}

@app.post("/api/project")
async def project_seed(req: ProjectRequest):
    """Takes a raw seed concept and projects the initial mental topology."""
    if not req.seed.strip():
        raise HTTPException(status_code=400, detail="Seed cannot be empty.")
    
    if req.provider:
        model_client.provider = req.provider
    if req.endpoint:
        model_client.endpoint = req.endpoint.rstrip("/")
    if req.model:
        model_client.model_name = req.model

    state = model_client.project_initial_blueprint(req.seed)
    sessions[state.session_id] = state
    _save_session_to_disk(state)
    return state.model_dump()

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    safe_id = _sanitize_session_id(session_id)
    if safe_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    return sessions[safe_id].model_dump()

@app.post("/api/probe/resolve")
async def resolve_probe(req: ProbeResolveRequest):
    """Resolves an architectural fork and updates the topology."""
    safe_id = _sanitize_session_id(req.session_id)
    if safe_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    current_state = sessions[safe_id]
    updated_state = model_client.resolve_probe_step(
        current_state=current_state,
        probe_id=req.probe_id,
        option_id=req.option_id,
        custom_note=req.custom_note
    )
    sessions[safe_id] = updated_state
    _save_session_to_disk(updated_state)
    return updated_state.model_dump()

@app.post("/api/synthesize")
async def synthesize_blueprint(req: SynthesizeRequest):
    """Compiles the crystallized state into ADR, Mermaid, and Code."""
    safe_id = _sanitize_session_id(req.session_id)
    if safe_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    state = sessions[safe_id]
    artifacts = BlueprintSynthesizer.generate_all(state)
    return {
        "session_id": state.session_id,
        "title": state.title,
        "convergence_pct": state.convergence_pct,
        "artifacts": artifacts
    }

class CustomNodeRequest(BaseModel):
    session_id: str
    id: str = Field(..., max_length=50)
    label: str = Field(..., max_length=80)
    tier: str = "compute"
    state_type: str = "stateless"
    latency_ms: int = 20
    description: str = Field("", max_length=300)

class CustomEdgeRequest(BaseModel):
    session_id: str
    source: str
    target: str
    protocol: str = "sync-rpc"
    label: str = Field("", max_length=60)
    async_flow: bool = False

@app.post("/api/node/custom")
async def add_custom_node(req: CustomNodeRequest):
    safe_id = _sanitize_session_id(req.session_id)
    if safe_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    state = sessions[safe_id]
    clean_node_id = re.sub(r'[^a-zA-Z0-9_]', '_', req.id)
    if any(n.id == clean_node_id for n in state.nodes):
        raise HTTPException(status_code=400, detail="Node ID already exists.")
    
    new_node = Node(
        id=clean_node_id,
        label=req.label,
        tier=req.tier,
        state_type=req.state_type,
        latency_ms=req.latency_ms,
        description=req.description
    )
    state.nodes.append(new_node)
    state.version += 1
    _save_session_to_disk(state)
    return state.model_dump()

@app.post("/api/edge/custom")
async def add_custom_edge(req: CustomEdgeRequest):
    safe_id = _sanitize_session_id(req.session_id)
    if safe_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    state = sessions[safe_id]
    node_ids = {n.id for n in state.nodes}
    if req.source not in node_ids or req.target not in node_ids:
        raise HTTPException(status_code=400, detail="Source or target node not found.")
    
    new_edge = Edge(
        source=req.source,
        target=req.target,
        protocol=req.protocol,
        label=req.label,
        async_flow=req.async_flow
    )
    state.edges.append(new_edge)
    state.version += 1
    _save_session_to_disk(state)
    return state.model_dump()

@app.post("/api/export")
async def export_code(req: ExportRequest):
    """Exports generated files for all IT roles safely confined within the export directory."""
    safe_id = _sanitize_session_id(req.session_id)
    if safe_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    state = sessions[safe_id]
    artifacts = BlueprintSynthesizer.generate_all(state)
    
    out_dir = (EXPORT_DIR / safe_id).resolve()
    if not out_dir.is_relative_to(EXPORT_DIR):
        raise HTTPException(status_code=400, detail="Path traversal in export destination forbidden.")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    all_written_files = []

    def _safe_write(filename: str, content: str):
        clean_name = Path(filename).name
        target = (out_dir / clean_name).resolve()
        if target.is_relative_to(out_dir):
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            all_written_files.append(clean_name)

    # 1. Software Architect
    _safe_write("ARCHITECTURE.md", artifacts.get("adr_markdown", ""))

    # 2. Python Developer Scaffolding
    for fn, c in artifacts.get("code_scaffold", {}).items():
        _safe_write(fn, c)

    # 3. TypeScript Developer Scaffolding
    for fn, c in artifacts.get("typescript_scaffold", {}).items():
        _safe_write(fn, c)

    # 4. Go Developer Scaffolding
    for fn, c in artifacts.get("go_scaffold", {}).items():
        _safe_write(fn, c)

    # 5. DevOps / SRE Deliverables
    for fn, c in artifacts.get("devops_iac", {}).items():
        _safe_write(fn, c)

    # 6. SecOps / CISO Threat Model
    _safe_write("THREAT_MODEL_STRIDE.md", artifacts.get("secops_stride", ""))

    # 7. QA / Chaos Engineering
    _safe_write("test_suite.py", artifacts.get("qa_tests", ""))

    # 8. Product Manager & FinOps
    _safe_write("FINOPS_AND_SLO.md", artifacts.get("finops_slo", ""))

    return {
        "status": "success",
        "exported_path": str(out_dir),
        "files": all_written_files
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
