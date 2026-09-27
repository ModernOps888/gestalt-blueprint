"""
End-to-End Test for Gestalt Engine and API.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from engine import ModelClient, BlueprintSynthesizer

def run_test():
    print("1. Initializing ModelClient...")
    client = ModelClient(provider="heuristic")
    health = client.check_health()
    print(f"   Health check: {health['status']} | Provider: {health['provider']}")

    print("\n2. Projecting seed: 'Autonomous multi-agent swarm with hierarchical supervisor'...")
    state = client.project_initial_blueprint("Autonomous multi-agent swarm with hierarchical supervisor")
    print(f"   Projected: '{state.title}'")
    print(f"   Nodes ({len(state.nodes)}): {[n.label for n in state.nodes]}")
    print(f"   Edges ({len(state.edges)}): {len(state.edges)} directed channels")
    print(f"   Invariants ({len(state.invariants)}): {[inv.statement for inv in state.invariants]}")
    print(f"   Active Probes: {len(state.active_probes)}")

    assert len(state.nodes) > 0, "No nodes projected"
    assert len(state.active_probes) > 0, "No probes generated"
    first_probe = state.active_probes[0]
    print(f"\n3. Resolving Socratic Probe: '{first_probe.dimension}'...")
    chosen_opt = first_probe.options[0]
    print(f"   Selecting Option: '{chosen_opt.label}'")

    updated_state = client.resolve_probe_step(
        current_state=state,
        probe_id=first_probe.id,
        option_id=chosen_opt.id
    )
    print(f"   New Convergence: {updated_state.convergence_pct}% (was {state.convergence_pct}%)")
    print(f"   Resolved Decisions: {len(updated_state.resolved_decisions)}")

    print("\n4. Synthesizing Deliverables (ADR + Mermaid + Code)...")
    artifacts = BlueprintSynthesizer.generate_all(updated_state)
    print(f"   ADR Length: {len(artifacts['adr_markdown'])} chars")
    print(f"   Mermaid lines: {len(artifacts['mermaid_diagram'].splitlines())} lines")
    print(f"   Code Files: {list(artifacts['code_scaffold'].keys())}")

    # Verify code syntax and execution
    code_files = artifacts['code_scaffold']
    assert "main.py" in code_files
    assert "invariants.py" in code_files

    test_out = Path(__file__).parent / "test_run"
    test_out.mkdir(exist_ok=True)
    with open(test_out / "invariants.py", "w", encoding="utf-8") as f:
        f.write(code_files["invariants.py"])
    with open(test_out / "main.py", "w", encoding="utf-8") as f:
        f.write(code_files["main.py"])

    print(f"   Wrote test execution files to {test_out}")
    print("\n5. Executing synthesized architecture...")
    import subprocess
    res = subprocess.run([sys.executable, str(test_out / "main.py")], capture_output=True, text=True)
    print("   Subprocess stdout:")
    print("   " + "\n   ".join(res.stdout.strip().splitlines()[:10]))
    assert res.returncode == 0, f"Execution failed: {res.stderr}"

    print("\n>>> ALL TESTS PASSED! Gestalt pipeline is verified and fully functional! <<<")

if __name__ == "__main__":
    run_test()
