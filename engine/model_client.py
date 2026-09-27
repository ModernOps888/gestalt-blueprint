"""
Local LLM and Heuristic Cognitive Engine for Gestalt.
Interfaces with Ollama, LM Studio, or local OpenAI-compatible endpoints,
with an intelligent fallback engine that generates dynamic architectural topologies.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional, List
from .topology import BlueprintState, Node, Edge, Invariant, ProbeFork, ProbeOption
from .domain_knowledge import DomainKnowledge

logger = logging.getLogger("gestalt.model_client")

class ModelClient:
    def __init__(
        self,
        provider: str = "auto",  # "auto", "ollama", "lmstudio", "heuristic"
        endpoint: str = "http://localhost:11434",
        model_name: str = "llama3.2"
    ):
        self.provider = provider
        self.endpoint = endpoint.rstrip("/")
        self.model_name = model_name

    def check_health(self) -> Dict[str, Any]:
        """Check status of local LLM providers."""
        # 1. Test Ollama
        try:
            r = requests.get(f"{self.endpoint}/api/tags", timeout=1.5)
            if r.status_code == 200:
                data = r.json()
                models = [m.get("name") for m in data.get("models", [])]
                active_model = self.model_name if self.model_name in models else (models[0] if models else "none")
                return {
                    "status": "connected",
                    "provider": "ollama",
                    "endpoint": self.endpoint,
                    "available_models": models,
                    "active_model": active_model,
                    "latency_ms": int(r.elapsed.total_seconds() * 1000)
                }
        except Exception:
            pass

        # 2. Test LM Studio / OpenAI compatible (port 1234 or custom)
        try:
            r = requests.get(f"http://localhost:1234/v1/models", timeout=1.5)
            if r.status_code == 200:
                data = r.json()
                models = [m.get("id") for m in data.get("data", [])]
                return {
                    "status": "connected",
                    "provider": "lmstudio",
                    "endpoint": "http://localhost:1234",
                    "available_models": models,
                    "active_model": models[0] if models else "local-model",
                    "latency_ms": int(r.elapsed.total_seconds() * 1000)
                }
        except Exception:
            pass

        # 3. Fallback to Built-in Cognitive Heuristics
        return {
            "status": "ready",
            "provider": "heuristic",
            "endpoint": "built-in",
            "available_models": ["Cognitive-Topology-Engine-v1"],
            "active_model": "Cognitive-Topology-Engine-v1",
            "latency_ms": 1
        }

    def project_initial_blueprint(self, seed: str) -> BlueprintState:
        """
        Projects a raw seed fragment into a topological blueprint with nodes, edges,
        invariants, and 2-3 Socratic bifurcation probes.
        """
        health = self.check_health()
        if health["status"] == "connected" and self.provider != "heuristic":
            try:
                res = self._call_local_llm_project(seed, health)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Local LLM call failed ({e}); falling back to Cognitive Engine.")

        # Autonomous Cognitive Heuristic Engine
        return self._heuristic_project(seed)

    def resolve_probe_step(
        self,
        current_state: BlueprintState,
        probe_id: str,
        option_id: str,
        custom_note: Optional[str] = None
    ) -> BlueprintState:
        """
        Mutates the blueprint graph based on the user's Socratic choice,
        crystallizes the architecture, and increases convergence.
        """
        # Find the selected probe and option
        target_probe = None
        target_option = None
        for p in current_state.active_probes:
            if p.id == probe_id:
                target_probe = p
                for opt in p.options:
                    if opt.id == option_id:
                        target_option = opt
                        break
                break

        if not target_probe or not target_option:
            return current_state

        # Record decision
        current_state.resolved_decisions.append({
            "probe_dimension": target_probe.dimension,
            "question": target_probe.question,
            "chosen_label": target_option.label,
            "tradeoff": target_option.tradeoff,
            "custom_note": custom_note or ""
        })

        # Remove applied probe
        current_state.active_probes = [p for p in current_state.active_probes if p.id != probe_id]

        # Apply node removals
        if target_option.removed_nodes:
            current_state.nodes = [n for n in current_state.nodes if n.id not in target_option.removed_nodes]
            current_state.edges = [e for e in current_state.edges if e.source not in target_option.removed_nodes and e.target not in target_option.removed_nodes]

        # Apply node additions
        for n_data in target_option.added_nodes:
            existing_ids = {n.id for n in current_state.nodes}
            if n_data["id"] not in existing_ids:
                current_state.nodes.append(Node(**n_data))

        # Apply edge additions
        for e_data in target_option.added_edges:
            current_state.edges.append(Edge(**e_data))

        # Apply invariant additions
        for inv_text in target_option.added_invariants:
            current_state.invariants.append(Invariant(
                statement=inv_text,
                category=target_probe.dimension.lower().replace(" ", "-"),
                severity="critical"
            ))

        # Calculate new convergence %
        # Each resolved probe closes the ambiguity gap
        current_state.convergence_pct = min(95, current_state.convergence_pct + 25)
        current_state.version += 1

        # Generate next-level deeper probes if convergence < 90%
        if len(current_state.active_probes) == 0 and current_state.convergence_pct < 85:
            current_state.active_probes = self._generate_next_level_probes(current_state)

        return current_state

    # -------------------------------------------------------------------------
    # Cognitive Topology Engine (Heuristics & Knowledge Synthesizer)
    # -------------------------------------------------------------------------
    def _heuristic_project(self, seed: str) -> BlueprintState:
        """
        Projects seed through the comprehensive DomainKnowledge base
        (10+ battle-tested archetypes + dynamic compositional synthesizer).
        """
        return DomainKnowledge.match_and_project(seed)

    def _generate_next_level_probes(self, state: BlueprintState) -> List[ProbeFork]:
        """Generates fine-grained refinement probes once primary forks are answered."""
        return [
            ProbeFork(
                dimension="Fault Recovery & Circuit Breaking",
                question="When a downstream node experiences transient failure or timeouts, how should the system behave?",
                cognitive_tension="Failing fast preserves resource pools and alerts operators immediately, while fallback degradations provide graceful user experience at the cost of stale data.",
                options=[
                    ProbeOption(
                        id="fail_fast_circuit",
                        label="Strict Circuit Breaker (Fail-Fast)",
                        description="Halt downstream calls on error threshold; reject requests immediately to prevent cascade failure.",
                        tradeoff="Users see clear error states; protects cluster stability.",
                        added_invariants=["Circuit breaker trips after 5 consecutive timeouts or 20% error rate"]
                    ),
                    ProbeOption(
                        id="graceful_degrade",
                        label="Graceful Degradation (Stale-While-Revalidate)",
                        description="Serve cached snapshot or synthetic heuristic if downstream is unresponsive.",
                        tradeoff="Slightly stale data, but uptime remains uninterrupted.",
                        added_invariants=["Responses must include 'X-Degraded-Mode: true' header when operating in fallback"]
                    )
                ]
            )
        ]

    # -------------------------------------------------------------------------
    # Local LLM Integration (Ollama / LM Studio)
    # -------------------------------------------------------------------------
    def _call_local_llm_project(self, seed: str, health_info: Dict[str, Any]) -> Optional[BlueprintState]:
        """Calls Ollama or OpenAI compatible local server to extract topology JSON."""
        system_prompt = (
            "You are an Advanced Architectural Topology Extractor. "
            "The user gives you a raw, unpolished idea. Instead of generating a long text response, "
            "you must project it directly into a high-dimensional architectural graph (Nodes, Edges, Invariants, and 2 Socratic Probes). "
            "IMPORTANT: When the user provides unconventional, exotic, eccentric, or strange concepts "
            "(such as quantum physics, synthetic biology, fungal mycelium networks, pigeon postal carriers, "
            "extreme weather aerodynamics, space constellations, or clockwork mechanics), do NOT force it into "
            "generic web microservices. Ground your nodes, tiers, protocols, and invariants directly in the physical, "
            "biological, mechanical, or cryptographic realities of their specific concept! "
            "Respond ONLY with valid JSON following this exact structure:\n"
            "{\n"
            "  \"title\": \"string\",\n"
            "  \"nodes\": [{\"id\": \"string\", \"label\": \"string\", \"tier\": \"gateway|compute|state|storage|security|edge|presentation\", \"state_type\": \"stateless|in-memory|persistent|crdt\", \"latency_ms\": 10, \"description\": \"string\"}],\n"
            "  \"edges\": [{\"source\": \"node_id\", \"target\": \"node_id\", \"protocol\": \"grpc|websocket|event-stream|sync-rpc|shared-mem|p2p|optical-laser|bio-electrical|piezo-analog|can-bus\", \"label\": \"string\", \"async_flow\": true}],\n"
            "  \"invariants\": [{\"statement\": \"string\", \"category\": \"consistency|security|performance|fault-tolerance\", \"severity\": \"critical\"}],\n"
            "  \"probes\": [\n"
            "    {\n"
            "      \"dimension\": \"string\",\n"
            "      \"question\": \"string\",\n"
            "      \"cognitive_tension\": \"string\",\n"
            "      \"options\": [\n"
            "        {\"id\": \"opt_1\", \"label\": \"string\", \"description\": \"string\", \"tradeoff\": \"string\", \"added_invariants\": [\"string\"]},\n"
            "        {\"id\": \"opt_2\", \"label\": \"string\", \"description\": \"string\", \"tradeoff\": \"string\", \"added_invariants\": [\"string\"]}\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        user_content = f"Seed concept: {seed}"

        # Ollama API
        if health_info["provider"] == "ollama":
            url = f"{health_info['endpoint']}/api/generate"
            payload = {
                "model": health_info["active_model"],
                "prompt": f"{system_prompt}\n\n{user_content}\n\nJSON:",
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2}
            }
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                raw_json = json.loads(res.json().get("response", "{}"))
                return self._parse_llm_json(seed, raw_json)

        # OpenAI Compatible (LM Studio / vLLM)
        elif health_info["provider"] == "lmstudio":
            url = f"{health_info['endpoint']}/v1/chat/completions"
            payload = {
                "model": health_info["active_model"],
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                content = res.json()["choices"][0]["message"]["content"]
                raw_json = json.loads(content)
                return self._parse_llm_json(seed, raw_json)

        return None

    def _parse_llm_json(self, seed: str, data: Dict[str, Any]) -> BlueprintState:
        nodes = [Node(**n) for n in data.get("nodes", [])]
        edges = [Edge(**e) for e in data.get("edges", [])]
        invariants = [Invariant(**inv) if isinstance(inv, dict) else Invariant(statement=str(inv)) for inv in data.get("invariants", [])]
        probes = []
        for p in data.get("probes", []):
            opts = [ProbeOption(**opt) for opt in p.get("options", [])]
            probes.append(ProbeFork(
                dimension=p.get("dimension", "Architecture Fork"),
                question=p.get("question", ""),
                cognitive_tension=p.get("cognitive_tension", ""),
                options=opts
            ))

        return BlueprintState(
            seed=seed,
            title=data.get("title", "Synthesized Blueprint"),
            convergence_pct=35,
            nodes=nodes,
            edges=edges,
            invariants=invariants,
            active_probes=probes,
            version=1
        )
