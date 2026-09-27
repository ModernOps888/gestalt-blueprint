"""
Comprehensive Hardware Profiling and Multi-Platform Stress Testing Suite for Gestalt.
Validates multi-platform detection (Windows, Linux, macOS), multi-GPU topologies,
factual VRAM model fit evaluation, dynamic eccentric raw prompt projections,
synthesizer hardware injection, and high-concurrency stress workloads.
"""

import os
import platform
import pytest
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from engine.hardware import HardwareSpecProfiler, GPUDevice, HardwareProfile
from engine.topology import BlueprintState, Node, Edge, Invariant
from engine.model_client import ModelClient
from engine.synthesizer import BlueprintSynthesizer


class TestHardwareDetection:
    """Verifies factual detection on the live host environment."""

    def test_live_host_hardware_detection(self):
        profile = HardwareSpecProfiler.get_profile(force_refresh=True)
        assert profile is not None
        assert profile.os_name in ["Windows", "Linux", "Darwin"]
        assert profile.cpu_physical_cores > 0
        assert profile.cpu_logical_cores >= profile.cpu_physical_cores
        assert profile.total_ram_gb > 0
        assert profile.spec_tier in ["edge_cpu", "entry_gpu", "mid_gpu", "high_gpu", "ultra_multigpu"]
        
        summary = profile.to_summary_dict()
        assert "os" in summary
        assert "cpu" in summary
        assert "ram" in summary
        assert "spec_tier" in summary
        assert "recommended_parameter_scale" in summary

        # Host-specific assertions (Windows with NVIDIA GPU)
        if platform.system() == "Windows" and profile.gpus:
            primary_gpu = profile.gpus[0]
            assert primary_gpu.total_vram_mb > 0
            assert primary_gpu.vendor == "nvidia"
            assert profile.docker_gpu_runtime == "nvidia"


class TestCrossPlatformMocking:
    """Simulates hardware architectures across Linux ROCm, Multi-GPU rig, and macOS Metal."""

    def test_linux_multigpu_rig(self):
        mock_gpus = [
            GPUDevice(index=0, name="NVIDIA A100-SXM4-80GB", vendor="nvidia", total_vram_mb=81920, free_vram_mb=80000),
            GPUDevice(index=1, name="NVIDIA A100-SXM4-80GB", vendor="nvidia", total_vram_mb=81920, free_vram_mb=80000),
            GPUDevice(index=2, name="NVIDIA A100-SXM4-80GB", vendor="nvidia", total_vram_mb=81920, free_vram_mb=80000),
            GPUDevice(index=3, name="NVIDIA A100-SXM4-80GB", vendor="nvidia", total_vram_mb=81920, free_vram_mb=80000),
        ]
        tier, label, scale, ctx, quant, strat, docker = HardwareSpecProfiler._classify_tier(
            os_name="Linux",
            total_vram_gb=320.0,
            gpus=mock_gpus,
            total_ram_gb=512.0
        )
        assert tier == "ultra_multigpu"
        assert strat == "tensor_parallel_split"
        assert docker == "nvidia"
        assert ctx >= 32768

    def test_linux_amd_rocm(self):
        mock_gpus = [
            GPUDevice(index=0, name="AMD Instinct MI300X", vendor="amd", total_vram_mb=196608, free_vram_mb=190000)
        ]
        tier, label, scale, ctx, quant, strat, docker = HardwareSpecProfiler._classify_tier(
            os_name="Linux",
            total_vram_gb=192.0,
            gpus=mock_gpus,
            total_ram_gb=256.0
        )
        assert tier == "high_gpu"
        assert "High-End Discrete GPU" in label
        assert docker is None  # Native ROCm rather than nvidia docker runtime

    def test_macos_metal_unified(self):
        mock_gpus = [
            GPUDevice(index=0, name="Apple Silicon (Metal Unified Architecture)", vendor="apple", total_vram_mb=36864, free_vram_mb=30000, compute_capability="Metal 3")
        ]
        tier, label, scale, ctx, quant, strat, docker = HardwareSpecProfiler._classify_tier(
            os_name="Darwin",
            total_vram_gb=36.0,
            gpus=mock_gpus,
            total_ram_gb=48.0
        )
        assert tier == "high_gpu"
        assert "High-End Discrete GPU" in label

    def test_edge_cpu_tier(self):
        mock_gpus = []
        tier, label, scale, ctx, quant, strat, docker = HardwareSpecProfiler._classify_tier(
            os_name="Linux",
            total_vram_gb=0.0,
            gpus=mock_gpus,
            total_ram_gb=3.8
        )
        assert tier == "edge_cpu"
        assert "CPU-Only" in label
        assert strat == "cpu_multithread"
        assert quant == "Q4_0"


class TestModelVRAMFitEvaluation:
    """Verifies accurate calculation of model memory requirements and offload status."""

    def test_fit_on_mid_gpu_8gb(self):
        profile = HardwareProfile(
            os_name="Windows",
            os_version="11",
            architecture="AMD64",
            cpu_model="Test CPU",
            cpu_physical_cores=8,
            cpu_logical_cores=16,
            total_ram_gb=32.0,
            available_ram_gb=24.0,
            gpus=[GPUDevice(index=0, name="RTX 5060", vendor="nvidia", total_vram_mb=8192, free_vram_mb=7900)],
            total_vram_gb=8.0,
            primary_compute_device="cuda:0",
            spec_tier="mid_gpu",
            spec_tier_label="Mid-Range Performance GPU"
        )

        fit_1b = profile.evaluate_model_fit("llama3.2:1b")
        assert fit_1b["fit_status"] == "optimal"
        assert fit_1b["can_run_full_speed"] is True
        assert fit_1b["offload_percentage"] == 100

        fit_3b = profile.evaluate_model_fit("llama3.2:latest")
        assert fit_3b["fit_status"] == "optimal"
        assert fit_3b["can_run_full_speed"] is True

        fit_7b = profile.evaluate_model_fit("qwen2.5-coder:7b")
        assert fit_7b["fit_status"] == "optimal"
        assert fit_7b["can_run_full_speed"] is True

        fit_14b = profile.evaluate_model_fit("qwen2.5:14b")
        assert fit_14b["fit_status"] == "hybrid"
        assert fit_14b["can_run_full_speed"] is False
        assert 0 < fit_14b["offload_percentage"] < 100

        fit_70b = profile.evaluate_model_fit("llama3.3:70b")
        # 70B requires ~53.7GB VRAM; total available (8GB + 24GB RAM) = 32GB < 53.7*1.2
        assert fit_70b["fit_status"] == "exceeds"
        assert fit_70b["can_run_full_speed"] is False

    def test_fit_on_multigpu_rig(self):
        profile = HardwareProfile(
            os_name="Linux",
            os_version="6.8",
            architecture="x86_64",
            cpu_model="AMD EPYC",
            cpu_physical_cores=64,
            cpu_logical_cores=128,
            total_ram_gb=512.0,
            available_ram_gb=400.0,
            gpus=[
                GPUDevice(index=0, name="A100", vendor="nvidia", total_vram_mb=81920),
                GPUDevice(index=1, name="A100", vendor="nvidia", total_vram_mb=81920)
            ],
            total_vram_gb=160.0,
            primary_compute_device="cuda:0-1",
            multi_gpu_enabled=True,
            spec_tier="ultra_multigpu",
            spec_tier_label="Multi-GPU Rig"
        )
        fit_70b = profile.evaluate_model_fit("llama3.3:70b")
        assert fit_70b["fit_status"] == "optimal"
        assert fit_70b["can_run_full_speed"] is True
        assert fit_70b["offload_percentage"] == 100


class TestDynamicEccentricRawPrompts:
    """Verifies that arbitrary, odd, custom, or frontier raw prompts generate valid calibrated topologies."""

    ECCENTRIC_SEEDS = [
        "Sub-surface tectonic neutrino tomography with ultra-deep borehole acoustic sensors and seismic Kalman filter",
        "Decentralized space debris collision avoidance mesh with cold-gas thruster coordination and orbital tracking",
        "Cryptographic zero-knowledge proof Dutch auction engine for commercial orbital launch windows",
        "Synthetic pheromone delivery network for precision agricultural drone swarms with soil biosensors",
        "Autonomous deep-sea underwater glider mesh using acoustic modems and thermocline buoyancy engines"
    ]

    @pytest.mark.parametrize("seed", ECCENTRIC_SEEDS)
    def test_eccentric_seed_projection(self, seed):
        client = ModelClient(provider="heuristic")
        state = client.project_initial_blueprint(seed)

        assert isinstance(state, BlueprintState)
        assert len(state.nodes) >= 4, f"Failed for seed: {seed}"
        assert len(state.edges) >= 3, f"Failed for seed: {seed}"
        assert len(state.invariants) >= 2, f"Failed for seed: {seed}"
        assert len(state.active_probes) >= 1, f"Failed for seed: {seed}"
        
        # Verify hardware calibration attachment
        assert state.hardware_profile is not None
        assert "spec_tier" in state.hardware_profile
        
        hw_invariants = [inv for inv in state.invariants if inv.category == "hardware-spec"]
        assert len(hw_invariants) >= 1
        assert "Hardware Profile" in hw_invariants[0].statement

    def test_socratic_fork_resolution_on_eccentric_blueprint(self):
        client = ModelClient(provider="heuristic")
        state = client.project_initial_blueprint(self.ECCENTRIC_SEEDS[0])
        initial_nodes_count = len(state.nodes)
        initial_convergence = state.convergence_pct

        probe = state.active_probes[0]
        option = probe.options[0]

        updated_state = client.resolve_probe_step(
            current_state=state,
            probe_id=probe.id,
            option_id=option.id,
            custom_note="Strict sub-50ms latency ceiling across borehole sensor ring"
        )

        assert updated_state.convergence_pct > initial_convergence
        assert len(updated_state.resolved_decisions) == 1
        assert updated_state.resolved_decisions[0]["chosen_label"] == option.label
        assert updated_state.resolved_decisions[0]["custom_note"] == "Strict sub-50ms latency ceiling across borehole sensor ring"


class TestSynthesizerHardwareEnrichment:
    """Verifies that deliverables contain hardware and GPU calibrations."""

    def test_synthesizer_devops_and_finops(self):
        client = ModelClient(provider="heuristic")
        state = client.project_initial_blueprint("High-throughput distributed vector search engine with HNSW indexing")
        artifacts = BlueprintSynthesizer.generate_all(state)

        # Check DevOps
        devops = artifacts["devops_iac"]
        assert "docker-compose.yml" in devops
        compose = devops["docker-compose.yml"]
        assert "HARDWARE_SPEC_TIER=" in compose

        # If running on machine with NVIDIA GPU, reservations must be present
        profile = HardwareSpecProfiler.get_profile()
        if profile.docker_gpu_runtime == "nvidia" or any(g.vendor == "nvidia" for g in profile.gpus):
            assert "reservations:" in compose
            assert "driver: nvidia" in compose
            assert "capabilities: [gpu]" in compose

        # Check FinOps
        finops = artifacts["finops_slo"]
        assert "## 2. Local Hardware Acceleration Economics" in finops
        assert "Operating Platform" in finops
        assert "Zero Cloud Bill" in finops
        assert "Annualized FinOps Savings" in finops


class TestConcurrencyAndStress:
    """Stress tests concurrent blueprint projections and synthesis under load."""

    def test_concurrent_projections(self):
        client = ModelClient(provider="heuristic")
        seeds = [
            f"Edge IoT sensor node {i} with low-power LoRaWAN telemetry and local anomaly ring buffer"
            for i in range(12)
        ]

        def _run_projection(s):
            res = client.project_initial_blueprint(s)
            arts = BlueprintSynthesizer.generate_all(res)
            return len(res.nodes), len(arts)

        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(_run_projection, seeds))

        assert len(results) == 12
        for node_count, art_count in results:
            assert node_count >= 4
            assert art_count == 9  # All 9 multi-role deliverables synthesized cleanly


class TestFastAPIIntegration:
    """Verifies end-to-end FastAPI HTTP endpoints with hardware and export workflows."""

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_get_hardware_endpoint(self, client):
        res = client.get("/api/hardware")
        assert res.status_code == 200
        data = res.json()
        assert "spec_tier" in data
        assert "primary_compute_device" in data
        assert "cpu_physical_cores" in data
        assert "total_ram_gb" in data

    def test_get_status_endpoint_with_hardware(self, client):
        res = client.get("/api/status")
        assert res.status_code == 200
        data = res.json()
        assert "hardware" in data
        assert "model_fits" in data
        assert "spec_tier" in data["hardware"]

    def test_project_and_synthesize_pipeline(self, client):
        # 1. Project an eccentric seed via HTTP
        proj_res = client.post("/api/project", json={
            "seed": "Sub-surface tectonic neutrino tomography with ultra-deep seismic sensors",
            "provider": "heuristic"
        })
        assert proj_res.status_code == 200
        state_data = proj_res.json()
        session_id = state_data["session_id"]
        assert len(state_data["nodes"]) >= 4
        assert state_data["hardware_profile"] is not None

        # 2. Synthesize all IT deliverables
        synth_res = client.post("/api/synthesize", json={"session_id": session_id})
        assert synth_res.status_code == 200
        synth_data = synth_res.json()
        artifacts = synth_data["artifacts"]
        assert "adr_markdown" in artifacts
        assert "devops_iac" in artifacts
        assert "finops_slo" in artifacts

        # 3. Export all files safely to disk
        export_res = client.post("/api/export", json={"session_id": session_id})
        assert export_res.status_code == 200
        export_data = export_res.json()
        assert export_data["status"] == "success"
        assert len(export_data["files"]) >= 7


class TestMultiClickAndIdempotency:
    """Verifies that rapid multi-clicks or duplicate requests never corrupt state or duplicate nodes/edges."""

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)

    def test_rapid_concurrent_probe_resolutions(self, client):
        proj_res = client.post("/api/project", json={
            "seed": "Autonomous multi-agent swarm with hierarchical supervisor",
            "provider": "heuristic"
        })
        assert proj_res.status_code == 200
        initial_state = proj_res.json()
        session_id = initial_state["session_id"]
        probe = initial_state["active_probes"][0]
        option = probe["options"][0]

        # Simulate 10 rapid concurrent clicks for the exact same probe option
        payload = {
            "session_id": session_id,
            "probe_id": probe["id"],
            "option_id": option["id"],
            "custom_note": "Rapid concurrent test note"
        }

        def _send_resolve(_):
            return client.post("/api/probe/resolve", json=payload)

        with ThreadPoolExecutor(max_workers=5) as executor:
            responses = list(executor.map(_send_resolve, range(10)))

        for r in responses:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data["nodes"], list)
            assert isinstance(data["edges"], list)

        final_state = responses[-1].json()
        
        # Verify zero decision duplicates
        matching_decisions = [
            d for d in final_state["resolved_decisions"]
            if d.get("probe_dimension") == probe["dimension"]
        ]
        assert len(matching_decisions) == 1

        # Verify zero node ID duplicates
        node_ids = [n["id"] for n in final_state["nodes"]]
        assert len(node_ids) == len(set(node_ids))

        # Verify zero edge (source, target) duplicates
        edge_pairs = [(e["source"], e["target"]) for e in final_state["edges"]]
        assert len(edge_pairs) == len(set(edge_pairs))

        # Verify zero invariant duplicates
        inv_statements = [i["statement"].strip().lower() for i in final_state["invariants"]]
        assert len(inv_statements) == len(set(inv_statements))


class TestOddPromptDecryption:
    """Verifies that eccentric, strange, fragmented, or slang prompts are decrypted and projected."""

    ECCENTRIC_IDEAS = [
        "A potato battery satellite swarm communicating with blue lasers and harvesting space plasma",
        "Smart sneaker shoe that glows green when dog barks and mines bitcoin on lightning network",
        "Adaptive neuro-fuzzy kitchen toaster regulating crumb moisture and browning curves",
        "Subsea acoustic hydrophone mesh tracking whale vocalizations and seismic tremors",
        "Bio-digital slime mold slime computer routing municipal traffic via oat flake chemo-attractants"
    ]

    @pytest.mark.parametrize("seed", ECCENTRIC_IDEAS)
    def test_eccentric_semantic_intent_decryption(self, seed):
        client = ModelClient(provider="heuristic")
        state = client.project_initial_blueprint(seed)

        assert state.decrypted_intent is not None
        assert len(state.decrypted_intent.strip()) > 10
        assert state.domain_classification is not None
        assert len(state.domain_classification.strip()) > 3

        # Nodes must reflect custom components rather than generic web services
        node_labels = [n.label.lower() for n in state.nodes]
        assert any(
            any(k in lbl for k in ["sensory", "signal", "core", "fabric", "ledger", "terminal", "sentinel"])
            for lbl in node_labels
        )

        # Must have invariants, probes, and edges
        assert len(state.nodes) >= 5
        assert len(state.edges) >= 4
        assert len(state.invariants) >= 3
        assert len(state.active_probes) >= 2

    def test_built_in_archetypes_have_intent(self):
        client = ModelClient(provider="heuristic")
        # Test built-in archetypes
        seeds = [
            "Autonomous multi-agent swarm with hierarchical supervisor",
            "Bioluminescent mushroom communication mesh with hyphal action potentials",
            "Fault-tolerant quantum key distribution with surface-code syndrome extraction"
        ]
        for s in seeds:
            state = client.project_initial_blueprint(s)
            assert state.decrypted_intent is not None
            assert state.domain_classification is not None


class TestProbeResolutionSprawlPrevention:
    """Verifies that sequential probe resolutions never cause node sprawl, duplicate stems, or invariant pollution."""

    def test_sequential_resolution_caps_and_clean_convergence(self):
        client = ModelClient(provider="heuristic")
        state = client.project_initial_blueprint("Autonomous multi-agent swarm with hierarchical supervisor")
        initial_node_count = len(state.nodes)
        assert initial_node_count <= 7

        # Resolve probe 1
        probe1 = state.active_probes[0]
        state = client.resolve_probe_step(
            current_state=state,
            probe_id=probe1.id,
            option_id=probe1.options[0].id
        )
        assert len(state.nodes) <= 8
        assert len(state.invariants) <= 6

        # If there is another active probe, resolve it
        if state.active_probes:
            probe2 = state.active_probes[0]
            state = client.resolve_probe_step(
                current_state=state,
                probe_id=probe2.id,
                option_id=probe2.options[0].id
            )
            assert len(state.nodes) <= 8
            assert len(state.invariants) <= 6

        # Check invariant statements are substantive (no single-word tags)
        for inv in state.invariants:
            assert len(inv.statement.split()) >= 4
            assert len(inv.statement) >= 20
            assert inv.statement.lower() not in ["stability", "autonomy", "agent-autonomy", "autonomy-stability"]

        # If further probe exists, resolve to completion
        while state.active_probes and state.convergence_pct < 100:
            p = state.active_probes[0]
            state = client.resolve_probe_step(
                current_state=state,
                probe_id=p.id,
                option_id=p.options[0].id
            )

        assert state.convergence_pct >= 95
        assert len(state.nodes) <= 8
        assert len(state.invariants) <= 6
        assert len(state.active_probes) == 0

    def test_llm_simulated_payload_filtering(self):
        """Simulates an LLM returning dirty/sprawling data and verifies our engine sanitizes it."""
        client = ModelClient(provider="ollama")
        state = client.project_initial_blueprint("Autonomous multi-agent swarm with hierarchical supervisor")
        probe = state.active_probes[0]
        option = probe.options[0]

        # Mock LLM response with sprawling nodes, duplicate stems, and 1-word invariants
        dirty_llm_json = {
            "added_nodes": [
                {"id": "swarm_stabilizer_alpha", "label": "Swarm Stabilizer", "tier": "compute", "state_type": "persistent", "latency_ms": 50, "description": "dup 1"},
                {"id": "swarm_stabilizer_beta", "label": "Swarm Stabilizer", "tier": "compute", "state_type": "stateless", "latency_ms": 50, "description": "dup 2"},
                {"id": "agent_autonomy_module", "label": "Agent Autonomy", "tier": "compute", "state_type": "persistent", "latency_ms": 50, "description": "dup 3"},
                {"id": "autonomy_decision_maker", "label": "Autonomy Decision", "tier": "compute", "state_type": "persistent", "latency_ms": 50, "description": "dup 4"}
            ],
            "added_edges": [
                {"source": "swarm_stabilizer_alpha", "target": "swarm_supervisor", "protocol": "sync-rpc", "label": "test", "async_flow": True}
            ],
            "added_invariants": [
                "agent-autonomy",
                "stability",
                "autonomy-stability",
                "Swarm state synchronization latency must remain strictly below 50ms across all cluster members"
            ],
            "next_probe": None
        }

        with patch.object(client, "check_health", return_value={"status": "connected", "provider": "ollama", "active_model": "llama3.2:latest", "is_local": True}):
            with patch.object(client, "_clean_and_parse_json", return_value=dirty_llm_json):
                with patch.object(client, "_dispatch_llm_request", return_value="dummy"):
                    updated_state = client.resolve_probe_step(
                        current_state=state,
                        probe_id=probe.id,
                        option_id=option.id
                    )

        # Verify only 1 node was allowed and duplicates were rejected
        assert len(updated_state.nodes) <= len(state.nodes) + 1
        assert len(updated_state.nodes) <= 8

        # Verify trivial 1-word invariants were rejected
        inv_texts = [i.statement.lower() for i in updated_state.invariants]
        assert "agent-autonomy" not in inv_texts
        assert "stability" not in inv_texts
        assert "autonomy-stability" not in inv_texts
        # The formal invariant was retained
        assert any("swarm state synchronization" in t for t in inv_texts)
