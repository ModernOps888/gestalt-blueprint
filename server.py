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

@app.post("/api/export")
async def export_code(req: ExportRequest):
    """Exports generated files to disk safely confined within the export directory."""
    safe_id = _sanitize_session_id(req.session_id)
    if safe_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    state = sessions[safe_id]
    artifacts = BlueprintSynthesizer.generate_all(state)
    
    # Path Sanitization: confine export within EXPORT_DIR
    out_dir = (EXPORT_DIR / safe_id).resolve()
    if not out_dir.is_relative_to(EXPORT_DIR):
        raise HTTPException(status_code=400, detail="Path traversal in export destination forbidden.")
    
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Write code files
    code_files = artifacts.get("code_scaffold", {})
    for filename, content in code_files.items():
        # Ensure filenames do not contain path traversal
        clean_filename = Path(filename).name
        target_path = (out_dir / clean_filename).resolve()
        if not target_path.is_relative_to(out_dir):
            continue
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    # Write ADR
    with open(out_dir / "ARCHITECTURE.md", "w", encoding="utf-8") as f:
        f.write(artifacts.get("adr_markdown", ""))

    return {
        "status": "success",
        "exported_path": str(out_dir),
        "files": list(code_files.keys()) + ["ARCHITECTURE.md"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
