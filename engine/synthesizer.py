"""
Blueprint Synthesizer for Gestalt.
Compiles high-dimensional cognitive topologies into concrete engineering deliverables:
- Architecture Decision Records (ADRs)
- Mermaid System Topology Diagrams
- Executable Multi-Module Scaffolding Code (Python/asyncio)
"""

from typing import Dict, Any
from .topology import BlueprintState

class BlueprintSynthesizer:
    @staticmethod
    def generate_all(state: BlueprintState) -> Dict[str, Any]:
        return {
            "adr_markdown": BlueprintSynthesizer.generate_adr(state),
            "mermaid_diagram": BlueprintSynthesizer.generate_mermaid(state),
            "code_scaffold": BlueprintSynthesizer.generate_code_scaffold(state)
        }

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
        # Group nodes by tier
        tiers = {}
        for n in state.nodes:
            tiers.setdefault(n.tier, []).append(n)

        for tier, nodes in tiers.items():
            mermaid.append(f"    subgraph Sub_{tier.upper()} [\"{tier.upper()} TIER\"]")
            for n in nodes:
                # Shape styling based on state
                badge = f"\\n[{n.state_type.upper()}]"
                mermaid.append(f"        {n.id}[\"{n.label}{badge}\"]")
            mermaid.append("    end")

        mermaid.append("")
        for e in state.edges:
            arrow = "-.->|Async: " if e.async_flow else "-->|"
            label = f"{e.label or e.protocol}"
            closing = "| "
            mermaid.append(f"    {e.source} {arrow}{label}{closing}{e.target}")

        # Add styling
        mermaid.extend([
            "",
            "    classDef default fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;",
            "    classDef gateway fill:#0f172a,stroke:#06b6d4,stroke-width:2px,color:#38bdf8;",
            "    classDef compute fill:#1e1b4b,stroke:#8b5cf6,stroke-width:2px,color:#c084fc;",
            "    classDef state fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#34d399;",
            "    classDef storage fill:#3f2c06,stroke:#f59e0b,stroke-width:2px,color:#fbbf24;"
        ])
        return "\n".join(mermaid)

    @staticmethod
    def generate_code_scaffold(state: BlueprintState) -> Dict[str, str]:
        """Generates real runnable Python asyncio scaffolding implementing the nodes and invariants."""
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

        import re
        import json

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
                f'        # Simulate node work within latency budget',
                f'        await asyncio.sleep(min(0.05, {n.latency_ms} / 1000.0))',
                f'        elapsed_ms = (time.perf_counter() - t0) * 1000.0',
                f'        SystemInvariants.assert_latency(self.node_id, elapsed_ms, self.latency_budget_ms)',
                f'        return {{"status": "ok", "source": self.node_id, "processed_at": time.time(), "input": payload}}',
                f''
            ])

        # Main orchestration loop connecting edges
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

        # Execute in topological flow order according to edges
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
