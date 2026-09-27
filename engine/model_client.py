"""
Local LLM and Dynamic Cognitive Engine for Gestalt.
Prioritizes zero-setup Local LLMs (Ollama, LM Studio, vLLM) with zero API keys required,
supports optional cloud endpoints, and seamlessly falls back to the high-fidelity
DomainKnowledge synthesizer when offline.
"""

import os
import re
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
        provider: str = "auto",  # "auto", "ollama", "lmstudio", "openrouter", "openai", "heuristic"
        endpoint: str = "http://localhost:11434",
        model_name: str = "llama3.2:latest",
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.endpoint = endpoint.rstrip("/")
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

    @staticmethod
    def _resolve_model_name(requested_name: str, available_models: List[str]) -> str:
        if not available_models:
            return requested_name
        if requested_name in available_models:
            return requested_name
        # Match prefix or suffix (e.g. 'llama3.2' matches 'llama3.2:latest', 'qwen2.5' matches 'qwen2.5:7b')
        for m in available_models:
            if m.startswith(f"{requested_name}:") or m == f"{requested_name}:latest":
                return m
        for m in available_models:
            if requested_name in m:
                return m
        return available_models[0]

    def check_health(self) -> Dict[str, Any]:
        """Check status of LLM providers. Local LLMs are prioritized with zero API keys required."""
        # 1. Test Local Ollama (Default port 11434)
        if self.provider in ["auto", "ollama"]:
            candidates = [self.endpoint]
            if "127.0.0.1" not in self.endpoint:
                candidates.append("http://127.0.0.1:11434")
            for host in candidates:
                try:
                    r = requests.get(f"{host}/api/tags", timeout=1.2)
                    if r.status_code == 200:
                        data = r.json()
                        models = [m.get("name") for m in data.get("models", [])]
                        active_model = self._resolve_model_name(self.model_name, models)
                        self.endpoint = host
                        return {
                            "status": "connected",
                            "provider": "ollama",
                            "endpoint": host,
                            "available_models": models,
                            "active_model": active_model,
                            "latency_ms": int(r.elapsed.total_seconds() * 1000),
                            "is_local": True
                        }
                except Exception:
                    pass

        # 2. Test Local LM Studio / OpenAI-compatible local server (Default port 1234)
        if self.provider in ["auto", "lmstudio"]:
            try:
                r = requests.get("http://localhost:1234/v1/models", timeout=1.5)
                if r.status_code == 200:
                    data = r.json()
                    models = [m.get("id") for m in data.get("data", [])]
                    active_model = self.model_name if self.model_name in models else (models[0] if models else "local-model")
                    return {
                        "status": "connected",
                        "provider": "lmstudio",
                        "endpoint": "http://localhost:1234",
                        "available_models": models,
                        "active_model": active_model,
                        "latency_ms": int(r.elapsed.total_seconds() * 1000),
                        "is_local": True
                    }
            except Exception:
                pass

        # 3. Optional Cloud Fallback (OpenRouter / OpenAI) - only if key configured
        cloud_key = self.api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if self.provider in ["openrouter", "openai"] or (self.provider == "auto" and cloud_key):
            target_endpoint = "https://openrouter.ai/api/v1" if (self.provider == "openrouter" or "OPENROUTER_API_KEY" in os.environ) else "https://api.openai.com/v1"
            if cloud_key:
                return {
                    "status": "connected",
                    "provider": "openrouter" if "openrouter" in target_endpoint else "openai",
                    "endpoint": target_endpoint,
                    "available_models": ["deepseek/deepseek-chat", "meta-llama/llama-3.3-70b-instruct", "gpt-4o-mini"],
                    "active_model": self.model_name if self.model_name != "llama3.2:latest" else "deepseek/deepseek-chat",
                    "latency_ms": 150,
                    "is_local": False
                }

        # 4. Built-in Cognitive Heuristics Engine (Offline, Instant, Zero Dependency)
        return {
            "status": "ready",
            "provider": "heuristic",
            "endpoint": "built-in",
            "available_models": ["Cognitive-Topology-Engine-v2"],
            "active_model": "Cognitive-Topology-Engine-v2",
            "latency_ms": 1,
            "is_local": True
        }

    def project_initial_blueprint(self, seed: str) -> BlueprintState:
        """
        Projects a raw seed fragment into a topological blueprint.
        Leverages local or configured LLMs when available; falls back to domain knowledge.
        """
        health = self.check_health()
        if health["status"] == "connected" and self.provider != "heuristic":
            try:
                res = self._call_llm_project(seed, health)
                if res and len(res.nodes) >= 3:
                    return res
            except Exception as e:
                logger.warning(f"Local LLM projection failed ({e}); falling back to Cognitive Knowledge Synthesizer.")

        # Autonomous Cognitive Heuristic & Dynamic Concept Synthesizer
        return self._heuristic_project(seed)

    def resolve_probe_step(
        self,
        current_state: BlueprintState,
        probe_id: str,
        option_id: str,
        custom_note: Optional[str] = None
    ) -> BlueprintState:
        """
        Mutates the blueprint graph based on the user's Socratic choice.
        If an LLM is active, performs dynamic architectural evolution;
        otherwise applies high-fidelity heuristic mutations.
        """
        target_probe = None
        target_option = None
        for p in current_state.active_probes:
            if p.id == probe_id or p.dimension == probe_id:
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

        # Remove answered probe
        current_state.active_probes = [p for p in current_state.active_probes if p.id != target_probe.id]

        # 1. Try Dynamic LLM Architectural Evolution
        health = self.check_health()
        if health["status"] == "connected" and self.provider != "heuristic":
            try:
                dynamic_state = self._call_llm_resolve_probe(current_state, target_probe, target_option, custom_note, health)
                if dynamic_state:
                    return dynamic_state
            except Exception as e:
                logger.warning(f"Dynamic LLM probe evolution failed ({e}); using heuristic mutation.")

        # 2. Heuristic Mutation Fallback
        if target_option.removed_nodes:
            current_state.nodes = [n for n in current_state.nodes if n.id not in target_option.removed_nodes]
            current_state.edges = [e for e in current_state.edges if e.source not in target_option.removed_nodes and e.target not in target_option.removed_nodes]

        for n_data in target_option.added_nodes:
            existing_ids = {n.id for n in current_state.nodes}
            if n_data["id"] not in existing_ids:
                current_state.nodes.append(Node(**n_data))

        for e_data in target_option.added_edges:
            current_state.edges.append(Edge(**e_data))

        for inv_text in target_option.added_invariants:
            current_state.invariants.append(Invariant(
                statement=inv_text,
                category=target_probe.dimension.lower().replace(" ", "-"),
                severity="critical"
            ))

        current_state.convergence_pct = min(95, current_state.convergence_pct + 25)
        current_state.version += 1

        if len(current_state.active_probes) == 0 and current_state.convergence_pct < 85:
            current_state.active_probes = self._generate_next_level_probes(current_state)

        return current_state

    # -------------------------------------------------------------------------
    # Cognitive Topology Engine (Heuristics & Knowledge Synthesizer)
    # -------------------------------------------------------------------------
    def _heuristic_project(self, seed: str) -> BlueprintState:
        return DomainKnowledge.match_and_project(seed)

    def _generate_next_level_probes(self, state: BlueprintState) -> List[ProbeFork]:
        return [
            ProbeFork(
                dimension="Fault Isolation & Degradation Policy",
                question="When an upstream dependency suffers severe congestion or timeout surges, how should the topology protect itself?",
                cognitive_tension="Strict Circuit Breaking aborts early to preserve cluster integrity, while Graceful Stale Fallback serves degraded heuristics to maintain continuous uptime.",
                options=[
                    ProbeOption(
                        id="strict_circuit_breaker",
                        label="Strict Fail-Fast Circuit Breaker",
                        description="Halt downstream calls instantly when error rate exceeds 5%; reject new requests to protect core nodes.",
                        tradeoff="Clients receive immediate explicit errors; prevents cascading cluster outages.",
                        added_invariants=["Circuit breaker trips after 3 consecutive timeouts or 5% error surge"]
                    ),
                    ProbeOption(
                        id="graceful_stale_fallback",
                        label="Graceful Stale Heuristic Fallback",
                        description="Serve cached snapshot or synthetic heuristic if downstream nodes are unresponsive.",
                        tradeoff="Maintains uninterrupted availability; data may temporarily reflect slightly stale state.",
                        added_invariants=["Degraded responses must explicitly set 'X-Degraded-Fallback: true' header"]
                    )
                ]
            )
        ]

    # -------------------------------------------------------------------------
    # LLM Interaction Methods
    # -------------------------------------------------------------------------
    def _call_llm_project(self, seed: str, health_info: Dict[str, Any]) -> Optional[BlueprintState]:
        """Calls local LLM (Ollama / LM Studio) or optional cloud endpoint to extract topology JSON."""
        system_prompt = (
            "You are an Advanced Architectural Topology Extractor. "
            "The user gives you a raw, unpolished idea. Instead of generating a long conversational essay, "
            "you must project it directly into a high-dimensional architectural graph. "
            "You MUST generate between 5 and 7 comprehensive components across distinct tiers "
            "(gateway, compute, state, storage, security, edge, presentation) with realistic latency budgets (ms), "
            "5 to 7 specific protocol communication edges, 3 critical invariants, and 2 high-entropy Socratic bifurcation probes. "
            "IMPORTANT: When the user provides unconventional, exotic, eccentric, or strange concepts "
            "(such as quantum physics, synthetic biology, fungal mycelium networks, pigeon postal carriers, "
            "extreme weather aerodynamics, space constellations, or clockwork mechanics), do NOT force it into "
            "generic web microservices. Ground your nodes, tiers, protocols, and invariants directly in the physical, "
            "biological, mechanical, or cryptographic realities of their specific concept! "
            "Respond ONLY with valid JSON following this exact structure:\n"
            "{\n"
            "  \"title\": \"string\",\n"
            "  \"nodes\": [{\"id\": \"string\", \"label\": \"string\", \"tier\": \"gateway|compute|state|storage|security|edge|presentation\", \"state_type\": \"stateless|in-memory|persistent|crdt\", \"latency_ms\": 10, \"description\": \"string\"}],\n"
            "  \"edges\": [{\"source\": \"node_id\", \"target\": \"node_id\", \"protocol\": \"string\", \"label\": \"string\", \"async_flow\": true}],\n"
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
        raw_json_str = self._dispatch_llm_request(system_prompt, user_content, health_info)
        if raw_json_str:
            data = self._clean_and_parse_json(raw_json_str)
            if data and "nodes" in data:
                return self._parse_llm_json(seed, data)
        return None

    def _call_llm_resolve_probe(
        self,
        state: BlueprintState,
        probe: ProbeFork,
        option: ProbeOption,
        custom_note: Optional[str],
        health_info: Dict[str, Any]
    ) -> Optional[BlueprintState]:
        """Dynamically evolves the architecture graph using the local/configured LLM based on user choice."""
        system_prompt = (
            "You are an Advanced Architectural Evolution Engine for Gestalt. "
            "The user has resolved an architectural trade-off fork in their system graph. "
            "Your job is to evolve and mutate the architecture based on their exact decision and custom notes: "
            "add necessary specialized components, add communication edges, establish new invariants, "
            "and synthesize ONE new high-entropy Socratic bifurcation probe that questions the next logical trade-off.\n"
            "Respond ONLY with valid JSON following this exact structure:\n"
            "{\n"
            "  \"added_nodes\": [{\"id\": \"string\", \"label\": \"string\", \"tier\": \"gateway|compute|state|storage|security|edge|presentation\", \"state_type\": \"stateless|in-memory|persistent|crdt\", \"latency_ms\": 10, \"description\": \"string\"}],\n"
            "  \"added_edges\": [{\"source\": \"string\", \"target\": \"string\", \"protocol\": \"string\", \"label\": \"string\", \"async_flow\": true}],\n"
            "  \"added_invariants\": [\"string\"],\n"
            "  \"next_probe\": {\n"
            "    \"dimension\": \"string\",\n"
            "    \"question\": \"string\",\n"
            "    \"cognitive_tension\": \"string\",\n"
            "    \"options\": [\n"
            "      {\"id\": \"opt_1\", \"label\": \"string\", \"description\": \"string\", \"tradeoff\": \"string\", \"added_invariants\": [\"string\"]},\n"
            "      {\"id\": \"opt_2\", \"label\": \"string\", \"description\": \"string\", \"tradeoff\": \"string\", \"added_invariants\": [\"string\"]}\n"
            "    ]\n"
            "  }\n"
            "}"
        )

        nodes_summary = ", ".join([f"{n.id} ({n.label}, {n.tier})" for n in state.nodes[:8]])
        user_content = (
            f"System Seed: {state.seed}\n"
            f"Active Components: {nodes_summary}\n"
            f"Bifurcation Fork Resolved: {probe.dimension}: {probe.question}\n"
            f"User Chosen Option: {option.label}\n"
            f"Accepted Trade-Off: {option.tradeoff}\n"
            f"User Custom Design Note: {custom_note or 'Standard implementation'}\n\n"
            f"Evolve the graph and provide the next probe in JSON:"
        )

        raw_json_str = self._dispatch_llm_request(system_prompt, user_content, health_info)
        if not raw_json_str:
            return None

        data = self._clean_and_parse_json(raw_json_str)
        if not data:
            return None

        # Apply LLM evolved nodes
        existing_node_ids = {n.id for n in state.nodes}
        for n_raw in data.get("added_nodes", []):
            if isinstance(n_raw, dict) and "id" in n_raw:
                clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', n_raw["id"])
                if clean_id not in existing_node_ids:
                    n_raw["id"] = clean_id
                    state.nodes.append(Node(**n_raw))
                    existing_node_ids.add(clean_id)

        # Apply LLM evolved edges
        for e_raw in data.get("added_edges", []):
            if isinstance(e_raw, dict) and "source" in e_raw and "target" in e_raw:
                e_raw["source"] = re.sub(r'[^a-zA-Z0-9_]', '_', e_raw["source"])
                e_raw["target"] = re.sub(r'[^a-zA-Z0-9_]', '_', e_raw["target"])
                state.edges.append(Edge(**e_raw))

        # Apply LLM evolved invariants
        for inv in data.get("added_invariants", []):
            state.invariants.append(Invariant(
                statement=str(inv),
                category=probe.dimension.lower().replace(" ", "-"),
                severity="critical"
            ))

        # Apply next probe if present
        next_p = data.get("next_probe")
        if isinstance(next_p, dict) and "dimension" in next_p and "options" in next_p:
            opts = [ProbeOption(**opt) for opt in next_p.get("options", []) if isinstance(opt, dict)]
            if len(opts) >= 2:
                state.active_probes.append(ProbeFork(
                    dimension=next_p.get("dimension", "Next Architectural Fork"),
                    question=next_p.get("question", "How should this subsystem be optimized?"),
                    cognitive_tension=next_p.get("cognitive_tension", ""),
                    options=opts
                ))

        state.convergence_pct = min(95, state.convergence_pct + 25)
        state.version += 1
        return state

    def _dispatch_llm_request(self, system_prompt: str, user_content: str, health_info: Dict[str, Any]) -> Optional[str]:
        """Dispatches an LLM request to Ollama, LM Studio, or an OpenAI-compatible cloud endpoint."""
        provider = health_info.get("provider", "ollama")
        active_model = health_info.get("active_model", "llama3.2:latest")

        # 1. Ollama Native API (Local - Zero Key)
        if provider == "ollama":
            url = f"{health_info.get('endpoint', self.endpoint)}/api/generate"
            payload = {
                "model": active_model,
                "prompt": f"{system_prompt}\n\n{user_content}\n\nJSON:",
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2}
            }
            res = requests.post(url, json=payload, timeout=60)
            if res.status_code == 200:
                return res.json().get("response")

        # 2. LM Studio / OpenAI-Compatible (Local or Cloud)
        elif provider in ["lmstudio", "openai", "openrouter"]:
            base_url = health_info.get("endpoint", "http://localhost:1234")
            url = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url
            if not url.startswith("http"):
                url = f"http://{url}"

            headers = {"Content-Type": "application/json"}
            cloud_key = self.api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
            if cloud_key:
                headers["Authorization"] = f"Bearer {cloud_key}"

            payload = {
                "model": active_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            res = requests.post(url, headers=headers, json=payload, timeout=60)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]

        return None

    def _clean_and_parse_json(self, raw_str: str) -> Optional[Dict[str, Any]]:
        """Strips markdown code fences and cleans JSON output from LLM responses."""
        if not raw_str or not raw_str.strip():
            return None
        text = raw_str.strip()
        # Strip ```json ... ```
        if "```" in text:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
            else:
                text = re.sub(r'```(?:json)?', '', text).replace('```', '').strip()

        try:
            return json.loads(text)
        except Exception:
            # Fallback: extract first outer curly bracket block
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return None

    def _parse_llm_json(self, seed: str, data: Dict[str, Any]) -> BlueprintState:
        """Constructs a validated BlueprintState from LLM JSON response."""
        nodes = []
        for n in data.get("nodes", []):
            if isinstance(n, dict) and "id" in n:
                n["id"] = re.sub(r'[^a-zA-Z0-9_]', '_', str(n["id"]))
                if "label" not in n:
                    n["label"] = n["id"].replace("_", " ").title()
                if "tier" not in n:
                    n["tier"] = "compute"
                if "state_type" not in n:
                    n["state_type"] = "stateless"
                if "latency_ms" not in n:
                    n["latency_ms"] = 20
                if "description" not in n:
                    n["description"] = f"Component handling {n['label']}"
                nodes.append(Node(**n))

        edges = []
        for e in data.get("edges", []):
            if isinstance(e, dict) and "source" in e and "target" in e:
                e["source"] = re.sub(r'[^a-zA-Z0-9_]', '_', str(e["source"]))
                e["target"] = re.sub(r'[^a-zA-Z0-9_]', '_', str(e["target"]))
                if "protocol" not in e:
                    e["protocol"] = "sync-rpc"
                if "label" not in e:
                    e["label"] = f"{e['source']} to {e['target']}"
                edges.append(Edge(**e))

        invariants = []
        for inv in data.get("invariants", []):
            if isinstance(inv, dict) and "statement" in inv:
                invariants.append(Invariant(**inv))
            else:
                invariants.append(Invariant(statement=str(inv), category="performance", severity="critical"))

        probes = []
        for p in data.get("probes", []):
            if isinstance(p, dict):
                opts = []
                for opt in p.get("options", []):
                    if isinstance(opt, dict) and "id" in opt and "label" in opt:
                        opts.append(ProbeOption(**opt))
                if len(opts) >= 2:
                    probes.append(ProbeFork(
                        dimension=p.get("dimension", "Architectural Bifurcation"),
                        question=p.get("question", "How should this component be coordinated?"),
                        cognitive_tension=p.get("cognitive_tension", ""),
                        options=opts
                    ))

        return BlueprintState(
            seed=seed,
            title=data.get("title", f"{seed[:30].strip().title()} Cognitive Topology"),
            convergence_pct=35,
            nodes=nodes,
            edges=edges,
            invariants=invariants,
            active_probes=probes,
            version=1
        )
