"""
Topology Data Structures for the Gestalt Blueprint Extractor.
Represents high-dimensional mental models: Nodes, Edges, Invariants, and Socratic Probes.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import uuid

class Node(BaseModel):
    id: str
    label: str
    tier: str = "compute"  # edge, gateway, compute, state, storage, security, presentation
    state_type: str = "stateless"  # stateless, in-memory, persistent, crdt, append-only
    latency_ms: Optional[int] = 50
    description: str = ""
    pinned: bool = False
    x: Optional[float] = None
    y: Optional[float] = None

class Edge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str
    target: str
    protocol: str = "sync-rpc"  # grpc, websocket, event-stream, sync-rpc, shared-mem, p2p
    label: str = ""
    async_flow: bool = False

class Invariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    statement: str
    category: str = "architecture"  # consistency, security, performance, fault-tolerance
    severity: str = "critical"  # critical, desired, invariant

class ProbeOption(BaseModel):
    id: str
    label: str
    description: str
    tradeoff: str
    added_nodes: List[Dict[str, Any]] = []
    removed_nodes: List[str] = []
    added_edges: List[Dict[str, Any]] = []
    added_invariants: List[str] = []

class ProbeFork(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    dimension: str  # e.g. "State Authority", "Event Ordering", "Network Topology"
    question: str
    cognitive_tension: str  # Why this choice bifurcates the architecture
    options: List[ProbeOption]

class BlueprintState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    seed: str = ""
    title: str = "Emergent Architecture"
    convergence_pct: int = 15  # starts at low convergence (high entropy)
    nodes: List[Node] = []
    edges: List[Edge] = []
    invariants: List[Invariant] = []
    active_probes: List[ProbeFork] = []
    resolved_decisions: List[Dict[str, Any]] = []
    version: int = 1
