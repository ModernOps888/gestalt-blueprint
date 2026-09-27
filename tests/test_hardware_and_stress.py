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
