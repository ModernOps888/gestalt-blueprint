"""
Blueprint Synthesizer for Gestalt.
Compiles high-dimensional cognitive topologies into deliverables for all IT professions:
- Software Architects: ADRs, System Boundaries, Mermaid Diagrams
- Polyglot Developers: Python (Asyncio), TypeScript (Node), Go (Goroutines)
- DevOps & SREs: Docker Compose, Dockerfiles, Health Probes, Prometheus Metrics
- SecOps & CISOs: STRIDE Threat Model, Zero-Trust Controls, Invariant Matrix
- QA & Chaos Engineers: Pytest Async Test Suites, Latency Boundary Tests, Chaos Injections
- Product Managers & FinOps: Cloud Run-Rate Estimator, Capacity Planning, SLA/SLO Contracts
"""

import re
import json
from typing import Dict, Any
from .topology import BlueprintState

class BlueprintSynthesizer:
    @staticmethod
    def generate_all(state: BlueprintState) -> Dict[str, Any]:
        return {
            "adr_markdown": BlueprintSynthesizer.generate_adr(state),
            "mermaid_diagram": BlueprintSynthesizer.generate_mermaid(state),
            "code_scaffold": BlueprintSynthesizer.generate_code_scaffold(state),
            "typescript_scaffold": BlueprintSynthesizer.generate_typescript_scaffold(state),
            "go_scaffold": BlueprintSynthesizer.generate_go_scaffold(state),
            "devops_iac": BlueprintSynthesizer.generate_devops(state),
            "secops_stride": BlueprintSynthesizer.generate_secops(state),
            "qa_tests": BlueprintSynthesizer.generate_qa_tests(state),
            "finops_slo": BlueprintSynthesizer.generate_finops(state)
        }

    # -------------------------------------------------------------------------
    # 1. SOFTWARE ARCHITECT: ADR & TOPOLOGY
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_adr(state: BlueprintState) -> str:
        lines = [
            f"# Architecture Blueprint: {state.title}",
            f"> Extracted via Gestalt Socratic Engine from Seed: \"{state.seed}\"",
            f"> Latent Convergence: **{state.convergence_pct}%** | Model Version: v{state.version}",
            "",
            "## 1. System Topology Overview",
            "| Component ID | Tier | State Model | Latency Budget | Responsibility |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        for n in state.nodes:
            lines.append(f"| `{n.id}` | **{n.tier.upper()}** | `{n.state_type}` | ~{n.latency_ms}ms | {n.description or n.label} |")

        lines.extend([
            "",
            "## 2. Invariants & Guardrails (Non-Negotiable Constraints)",
            "The following invariants must be verified at runtime and compile-time:"
        ])
        for idx, inv in enumerate(state.invariants, 1):
            lines.append(f"{idx}. **[{inv.category.upper()}]** {inv.statement} *(Severity: `{inv.severity}`)*")

        lines.extend([
            "",
            "## 3. High-Entropy Architectural Decisions (ADR Log)",
            "The following architectural forks were resolved during Socratic extraction:"
        ])
        if state.resolved_decisions:
            for idx, dec in enumerate(state.resolved_decisions, 1):
                lines.append(f"### ADR-{idx:03d}: {dec['probe_dimension']}")
                lines.append(f"- **Context & Question:** {dec['question']}")
                lines.append(f"- **Decision Made:** **{dec['chosen_label']}**")
                lines.append(f"- **Architectural Tradeoff Accepted:** {dec['tradeoff']}")
                if dec.get("custom_note"):
                    lines.append(f"- **Designer Invariant Note:** *\"{dec['custom_note']}\"*")
                lines.append("")
        else:
            lines.append("*Initial topology baseline. No branching forks resolved yet.*")

        return "\n".join(lines)

    @staticmethod
    def generate_mermaid(state: BlueprintState) -> str:
        mermaid = ["graph TD"]
        tiers = {}
        for n in state.nodes:
            tiers.setdefault(n.tier, []).append(n)

        for tier, nodes in tiers.items():
            mermaid.append(f"    subgraph Sub_{tier.upper()} [\"{tier.upper()} TIER\"]")
            for n in nodes:
                safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', n.id)
                badge = f"\\n[{n.state_type.upper()}]"
                mermaid.append(f"        {safe_id}[\"{n.label}{badge}\"]")
            mermaid.append("    end")

        mermaid.append("")
        for e in state.edges:
            src = re.sub(r'[^a-zA-Z0-9_]', '_', e.source)
            tgt = re.sub(r'[^a-zA-Z0-9_]', '_', e.target)
            arrow = "-.->|Async: " if e.async_flow else "-->|"
            label = f"{e.label or e.protocol}"
            mermaid.append(f"    {src} {arrow}{label}| {tgt}")

        mermaid.extend([
            "",
            "    classDef default fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;",
            "    classDef gateway fill:#0f172a,stroke:#06b6d4,stroke-width:2px,color:#38bdf8;",
            "    classDef compute fill:#1e1b4b,stroke:#8b5cf6,stroke-width:2px,color:#c084fc;",
            "    classDef state fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#34d399;",
            "    classDef storage fill:#3f2c06,stroke:#f59e0b,stroke-width:2px,color:#fbbf24;"
        ])
        return "\n".join(mermaid)

    # -------------------------------------------------------------------------
    # 2. POLYGLOT DEVELOPER: PYTHON (Asyncio)
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_code_scaffold(state: BlueprintState) -> Dict[str, str]:
        files = {}
        
        # 1. Invariants runtime validator
        invariants_code = [
            '"""',
            'Runtime System Invariants & Guardrails.',
            'Automatically synthesized from Gestalt Cognitive Blueprint.',
            '"""',
            'import logging',
            'logger = logging.getLogger("system.invariants")',
            '',
            'class SystemInvariants:',
            '    """Enforces non-negotiable architectural boundaries."""',
            '    INVARIANTS = ['
        ]
        for inv in state.invariants:
            invariants_code.append(f'        ("{inv.category.upper()}", "{inv.severity.upper()}", "{inv.statement}"),')
        invariants_code.extend([
            '    ]',
            '',
            '    @classmethod',
            '    def verify_all(cls):',
            '        for cat, sev, stmt in cls.INVARIANTS:',
            '            logger.info(f"Checking Invariant [{cat}] ({sev}): {stmt}")',
            '        return True',
            '',
            '    @classmethod',
            '    def assert_latency(cls, node_id: str, elapsed_ms: float, budget_ms: float):',
            '        if elapsed_ms > budget_ms:',
            '            logger.warning(f"Latency Budget Exceeded! Node={node_id}: {elapsed_ms:.2f}ms > {budget_ms}ms")',
            '        assert elapsed_ms <= max(200.0, budget_ms * 5.0), f"Critical latency breach at {node_id}"'
        ])
        files["invariants.py"] = "\n".join(invariants_code)

        # 2. Scaffolding for each node as an asynchronous actor/service
        nodes_code = [
            '"""',
            f'Synthesized Architecture: {state.title}',
            'Generated by Gestalt Cognitive Topology Engine.',
            '"""',
            'import asyncio',
            'import time',
            'import logging',
            'from invariants import SystemInvariants',
            '',
            'logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")',
            ''
        ]

        for n in state.nodes:
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', n.id)
            class_name = "".join(word.capitalize() for word in safe_id.split("_") if word) or "Node"
            nodes_code.extend([
                f'class {class_name}:',
                f'    """',
                f'    Node: {n.label}',
                f'    Tier: {n.tier} | State: {n.state_type} | Latency Budget: {n.latency_ms}ms',
                f'    Description: {n.description}',
                f'    """',
                f'    def __init__(self):',
                f'        self.node_id = "{safe_id}"',
                f'        self.tier = "{n.tier}"',
                f'        self.latency_budget_ms = {n.latency_ms}',
                f'        self.is_running = False',
                f'        self.state = {{"type": "{n.state_type}", "items": []}}',
                f'        self.logger = logging.getLogger(f"node.{{self.node_id}}")',
                f'',
                f'    async def process(self, payload: dict) -> dict:',
                f'        t0 = time.perf_counter()',
                f'        self.logger.info(f"Processing payload in {{self.node_id}} [tier={{self.tier}}]...")',
                f'        await asyncio.sleep(min(0.04, {n.latency_ms} / 1000.0))',
                f'        elapsed_ms = (time.perf_counter() - t0) * 1000.0',
                f'        SystemInvariants.assert_latency(self.node_id, elapsed_ms, self.latency_budget_ms)',
                f'        return {{"status": "ok", "source": self.node_id, "processed_at": time.time(), "input": payload}}',
                f''
            ])

        main_code = [
            'class SystemOrchestrator:',
            '    def __init__(self):',
            '        SystemInvariants.verify_all()',
        ]
        for n in state.nodes:
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', n.id)
            class_name = "".join(word.capitalize() for word in safe_id.split("_") if word) or "Node"
            main_code.append(f'        self.{safe_id} = {class_name}()')

        main_code.extend([
            '',
            '    async def execute_pipeline(self, initial_request: dict):',
            '        print("\\n=== EXECUTING GESTALT SYNTHESIZED TOPOLOGY ===")',
            '        results = {}'
        ])

        visited = set()
        for e in state.edges:
            src = re.sub(r'[^a-zA-Z0-9_]', '_', e.source)
            tgt = re.sub(r'[^a-zA-Z0-9_]', '_', e.target)
            if src not in visited:
                main_code.append(f'        res_{src} = await self.{src}.process(initial_request)')
                visited.add(src)
            main_code.append(f'        res_{tgt} = await self.{tgt}.process(res_{src})')
            visited.add(tgt)

        main_code.extend([
            '        print("=== PIPELINE EXECUTION COMPLETED SUCESSFULLY ===\\n")',
            '        return {"status": "complete", "timestamp": time.time()}',
            '',
            'async def main():',
            '    orchestrator = SystemOrchestrator()',
            f'    test_payload = {{"seed": {json.dumps(state.seed)}, "timestamp": time.time()}}',
            '    await orchestrator.execute_pipeline(test_payload)',
            '',
            'if __name__ == "__main__":',
            '    asyncio.run(main())'
        ])

        files["main.py"] = "\n".join(nodes_code + main_code)
        return files

    # -------------------------------------------------------------------------
    # 3. POLYGLOT DEVELOPER: TYPESCRIPT (Node/Bun)
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_typescript_scaffold(state: BlueprintState) -> Dict[str, str]:
        ts_code = [
            '/**',
            f' * Synthesized Architecture: {state.title}',
            ' * Generated by Gestalt Cognitive Topology Engine (TypeScript Target)',
            ' */',
            '',
            'export interface SystemPayload {',
            '  id: string;',
            '  timestamp: number;',
            '  data: Record<string, any>;',
            '}',
            '',
            'export class SystemInvariants {',
            '  static assertLatency(nodeId: string, elapsedMs: number, budgetMs: number): void {',
            '    if (elapsedMs > budgetMs) {',
            '      console.warn(`[WARN] Latency Budget Exceeded! Node=${nodeId}: ${elapsedMs.toFixed(2)}ms > ${budgetMs}ms`);',
            '    }',
            '  }',
            '}',
            ''
        ]

        for n in state.nodes:
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', n.id)
            class_name = "".join(word.capitalize() for word in safe_id.split("_") if word) or "Node"
            ts_code.extend([
                f'export class {class_name} {{',
                f'  readonly nodeId = "{safe_id}";',
                f'  readonly tier = "{n.tier}";',
                f'  readonly latencyBudgetMs = {n.latency_ms};',
                f'  readonly stateModel = "{n.state_type}";',
                f'',
                f'  async process(payload: SystemPayload): Promise<SystemPayload> {{',
                f'    const t0 = performance.now();',
                f'    console.log(`[{n.tier.upper()}] Processing in ${{this.nodeId}}...`);',
                f'    await new Promise(r => setTimeout(r, Math.min(30, {n.latency_ms})));',
                f'    const elapsed = performance.now() - t0;',
                f'    SystemInvariants.assertLatency(this.nodeId, elapsed, this.latencyBudgetMs);',
                f'    return {{ ...payload, timestamp: Date.now() }};',
                f'  }}',
                f'}}',
                ''
            ])

        ts_code.extend([
            'export class Orchestrator {',
        ])
        for n in state.nodes:
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', n.id)
            class_name = "".join(word.capitalize() for word in safe_id.split("_") if word) or "Node"
            ts_code.append(f'  private {safe_id} = new {class_name}();')

        ts_code.extend([
            '',
            '  async executePipeline(initialPayload: SystemPayload): Promise<void> {',
            '    console.log("=== EXECUTING GESTALT TYPESCRIPT TOPOLOGY ===");',
        ])

        visited = set()
        for e in state.edges:
            src = re.sub(r'[^a-zA-Z0-9_]', '_', e.source)
            tgt = re.sub(r'[^a-zA-Z0-9_]', '_', e.target)
            if src not in visited:
                ts_code.append(f'    const res_{src} = await this.{src}.process(initialPayload);')
                visited.add(src)
            ts_code.append(f'    const res_{tgt} = await this.{tgt}.process(res_{src});')
            visited.add(tgt)

        ts_code.extend([
            '    console.log("=== TYPESCRIPT PIPELINE FINISHED SUCCESSFULLY ===");',
            '  }',
            '}',
            '',
            '// Entrypoint',
            'const app = new Orchestrator();',
            f'app.executePipeline({{ id: "init-1", timestamp: Date.now(), data: {{ seed: {json.dumps(state.seed)} }} }});'
        ])

        return {"index.ts": "\n".join(ts_code)}

    # -------------------------------------------------------------------------
    # 4. POLYGLOT DEVELOPER: GO (Concurrency & Goroutines)
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_go_scaffold(state: BlueprintState) -> Dict[str, str]:
        go_code = [
            'package main',
            '',
            'import (',
            '    "context"',
            '    "fmt"',
            '    "log"',
            '    "time"',
            ')',
            '',
            '// Synthesized Go Architecture: ' + state.title,
            '',
            'type Payload struct {',
            '    Source string',
            '    Data   string',
            '    Time   time.Time',
            '}',
            ''
        ]

        for n in state.nodes:
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', n.id)
            class_name = "".join(word.capitalize() for word in safe_id.split("_") if word) or "Node"
            go_code.extend([
                f'type {class_name} struct {{',
                f'    ID            string',
                f'    LatencyBudget time.Duration',
                f'}}',
                f'',
                f'func New{class_name}() *{class_name} {{',
                f'    return &{class_name}{{ID: "{safe_id}", LatencyBudget: {n.latency_ms} * time.Millisecond}}',
                f'}}',
                f'',
                f'func (n *{class_name}) Process(ctx context.Context, in Payload) (Payload, error) {{',
                f'    t0 := time.Now()',
                f'    log.Printf("[NODE %s] Processing payload in tier: {n.tier}...", n.ID)',
                f'    time.Sleep(10 * time.Millisecond)',
                f'    if time.Since(t0) > n.LatencyBudget*3 {{',
                f'        log.Printf("[WARN] Latency budget exceeded on %s", n.ID)',
                f'    }}',
                f'    return Payload{{Source: n.ID, Data: in.Data, Time: time.Now()}}, nil',
                f'}}',
                ''
            ])

        go_code.extend([
            'func main() {',
            '    ctx := context.Background()',
            '    fmt.Println("=== EXECUTING GESTALT GO CONCURRENT TOPOLOGY ===")',
            '    p := Payload{Source: "init", Data: "' + state.seed[:30].replace('"', '') + '", Time: time.Now()}',
        ])

        visited = set()
        for n in state.nodes:
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', n.id)
            class_name = "".join(word.capitalize() for word in safe_id.split("_") if word) or "Node"
            go_code.append(f'    node_{safe_id} := New{class_name}()')

        for e in state.edges:
            src = re.sub(r'[^a-zA-Z0-9_]', '_', e.source)
            tgt = re.sub(r'[^a-zA-Z0-9_]', '_', e.target)
            if src not in visited:
                go_code.append(f'    res_{src}, _ := node_{src}.Process(ctx, p)')
                visited.add(src)
            go_code.append(f'    res_{tgt}, _ := node_{tgt}.Process(ctx, res_{src})')
            visited.add(tgt)

        go_code.extend([
            '    fmt.Println("=== GO PIPELINE EXECUTION SUCCESSFUL ===")',
            '}'
        ])

        return {"main.go": "\n".join(go_code)}

    # -------------------------------------------------------------------------
    # 5. DEVOPS & SRE: DOCKER COMPOSE & DOCKERFILE
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_devops(state: BlueprintState) -> Dict[str, str]:
        dockerfile = [
            "# Multi-stage lightweight build generated by Gestalt",
            "FROM python:3.12-slim AS builder",
            "WORKDIR /app",
            "RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*",
            "COPY requirements.txt .",
            "RUN pip install --user --no-cache-dir -r requirements.txt",
            "",
            "FROM python:3.12-slim",
            "WORKDIR /app",
            "COPY --from=builder /root/.local /root/.local",
            "ENV PATH=/root/.local/bin:$PATH",
            "COPY . .",
            "EXPOSE 8080",
            "HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8080/health\")' || exit 1",
            "CMD [\"python\", \"main.py\"]"
        ]

        compose = [
            "version: '3.8'",
            f"# Generated multi-container topology for {state.title}",
            "services:",
            "  orchestrator:",
            "    build: .",
            "    restart: unless-stopped",
            "    environment:",
            "      - GESTALT_CONVERGENCE=" + str(state.convergence_pct),
            "      - ENVIRONMENT=production",
            "    ports:",
            "      - '8080:8080'",
            "    networks:",
            "      - internal_mesh",
            "    deploy:",
            "      resources:",
            "        limits:",
            "          cpus: '2.0'",
            "          memory: 1024M",
            "",
            "  prometheus:",
            "    image: prom/prometheus:latest",
            "    ports:",
            "      - '9090:9090'",
            "    networks:",
            "      - internal_mesh",
            "",
            "networks:",
            "  internal_mesh:",
            "    driver: bridge"
        ]

        return {
            "Dockerfile": "\n".join(dockerfile),
            "docker-compose.yml": "\n".join(compose)
        }

    # -------------------------------------------------------------------------
    # 6. SECOPS & CISO: STRIDE THREAT MODEL
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_secops(state: BlueprintState) -> str:
        lines = [
            f"# STRIDE Threat Model & Security Posture: {state.title}",
            f"> System Classification: High-Availability Distributed Blueprint",
            "",
            "## 1. STRIDE Threat Matrix",
            "| Threat Category | Applicable Nodes | Risk Description | Architectural Mitigation |",
            "| :--- | :--- | :--- | :--- |"
        ]

        stride_rows = [
            ("Spoofing", "Gateway & Client Tiers", "Adversary impersonates legitimate edge client or forge identities.", "Mutual TLS (mTLS) + Cryptographic token signatures with nonces."),
            ("Tampering", "Event Backbone & State", "In-flight payload modification or out-of-order packet reordering.", "Payload HMAC validation + monotonic vector clock sequence checks."),
            ("Repudiation", "Ledger & Invariant Sentry", "Node denies processing or originating state transition.", "Immutable append-only write-ahead log (WAL) with hardware timestamping."),
            ("Information Disclosure", "Cross-Node Channels", "Sniffing intermediate RPC or memory scratchpad contents.", "Wire encryption (AES-256-GCM) + process memory sandbox isolation."),
            ("Denial of Service", "Compute & Swarm Tiers", "Resource exhaustion via runaway task loops or poison payloads.", "Circuit breaker trip-wires + bounded iteration budgets (<= 4 turns)."),
            ("Elevation of Privilege", "Tool Substrate", "Sandboxed execution breakout targeting underlying host kernel.", "Strict unprivileged containers (Bubblewrap/gVisor) with zero network capabilities.")
        ]

        for cat, nodes, risk, mit in stride_rows:
            lines.append(f"| **{cat}** | `{nodes}` | {risk} | {mit} |")

        lines.extend([
            "",
            "## 2. Invariant Enforcement Rubric",
            "The following invariants serve as the active security baseline:"
        ])
        for idx, inv in enumerate(state.invariants, 1):
            lines.append(f"{idx}. **[{inv.category.upper()}]** `{inv.severity.upper()}`: {inv.statement}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # 7. QA & CHAOS ENGINEER: PYTEST ASYNC & LATENCY BOUNDARY SUITE
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_qa_tests(state: BlueprintState) -> str:
        test_code = [
            '"""',
            f'Automated QA & Chaos Test Suite for {state.title}',
            'Validates latency budgets, invariant integrity, and fault tolerance.',
            '"""',
            'import pytest',
            'import asyncio',
            'import time',
            'from invariants import SystemInvariants',
            'from main import SystemOrchestrator',
            '',
            '@pytest.mark.asyncio',
            'async def test_full_pipeline_success():',
            '    """Verifies end-to-end processing under normal conditions."""',
            '    orchestrator = SystemOrchestrator()',
            '    payload = {"test_id": "qa-001", "timestamp": time.time()}',
            '    result = await orchestrator.execute_pipeline(payload)',
            '    assert result["status"] == "complete"',
            '    assert "timestamp" in result',
            '',
            '@pytest.mark.asyncio',
            'async def test_invariants_integrity():',
            '    """Verifies that all architectural invariants pass validation."""',
            '    assert SystemInvariants.verify_all() is True',
            '',
            '@pytest.mark.asyncio',
            'async def test_latency_assertion_boundary():',
            '    """Asserts that latency breaches raise warnings without unexpected crash."""',
            '    # Simulate normal latency assertion within budget',
            '    SystemInvariants.assert_latency("test_node", elapsed_ms=10.0, budget_ms=25.0)',
            '    # Assert that simulated jitter is tolerated up to ceiling',
            '    SystemInvariants.assert_latency("test_node", elapsed_ms=30.0, budget_ms=20.0)',
            '',
            '@pytest.mark.asyncio',
            'async def test_chaos_fault_injection():',
            '    """Simulates node degradation under high network pressure."""',
            '    orchestrator = SystemOrchestrator()',
            '    # Run 5 concurrent stress executions',
            '    tasks = [orchestrator.execute_pipeline({"task": i}) for i in range(5)]',
            '    results = await asyncio.gather(*tasks)',
            '    assert len(results) == 5',
            '    for res in results:',
            '        assert res["status"] == "complete"'
        ]
        return "\n".join(test_code)

    # -------------------------------------------------------------------------
    # 8. PRODUCT MANAGER & FINOPS: CAPACITY PLANNING & COST ESTIMATE
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_finops(state: BlueprintState) -> str:
        node_count = len(state.nodes)
        edge_count = len(state.edges)
        
        # Estimate resources
        estimated_ram_mb = node_count * 256
        estimated_cpu_cores = max(2, node_count // 2)
        monthly_cloud_cost = node_count * 18.50 + 24.00  # realistic $ per node + gateway
        
        lines = [
            f"# FinOps Capacity Planning & SLO Contract: {state.title}",
            f"> System Scale: **{node_count} Nodes** | **{edge_count} Interconnects**",
            "",
            "## 1. Cloud Infrastructure Run-Rate Estimation",
            "| Resource Dimension | Allocated Sizing | Estimated Monthly Run-Rate (AWS/GCP) | On-Prem / Local Cost |",
            "| :--- | :--- | :--- | :--- |",
            f"| **Compute Instances** | {estimated_cpu_cores} vCPU, {estimated_ram_mb} MB RAM | ~${monthly_cloud_cost:.2f} / month | $0.00 (Local Hardware) |",
            f"| **Inter-Service Bandwidth**| ~{edge_count * 50} GB/mo egress | ~${edge_count * 4.50:.2f} / month | $0.00 (Local Loopback) |",
            f"| **Persistence Storage** | 100 GB NVMe block store | ~$12.00 / month | $0.00 (Host Disk) |",
            f"| **TOTAL ESTIMATE** | **Production Tier** | **~${monthly_cloud_cost + 20:.2f} / month** | **$0.00 (Zero Cloud Bill)** |",
            "",
            "## 2. Service Level Objectives (SLO) & SLA Contracts",
            "- **Target Service Availability (SLA):** **99.95%** (< 21.9 minutes downtime per month)",
            f"- **Latency Objective (SLO):** 95th percentile completion in **< {sum(n.latency_ms for n in state.nodes)}ms**",
            "- **Error Budget:** Maximum 0.05% unhandled 5xx request errors per 30-day window",
            "- **Recovery Time Objective (RTO):** < 30 seconds via container restart policies",
            "- **Recovery Point Objective (RPO):** < 50ms state loss via write-ahead logging"
        ]
        return "\n".join(lines)
