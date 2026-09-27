"""
Hardware Specification and Multi-GPU Profiling Engine for Gestalt.
Provides high-precision cross-platform detection for Windows, Linux, and macOS (Darwin),
including NVIDIA (CUDA), AMD (ROCm), Apple Silicon (Metal/MPS), Intel Arc, and CPU topologies.
Calculates VRAM budgets, multi-GPU parallelism strategies, and hardware-matched model tiers.
"""

import os
import re
import sys
import time
import platform
import subprocess
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Cache profile for 15 seconds to avoid expensive subprocess calls on every request
_CACHED_PROFILE: Optional["HardwareProfile"] = None
_LAST_PROFILE_TIME: float = 0.0

class GPUDevice(BaseModel):
    index: int = 0
    name: str = "Unknown GPU"
    vendor: str = "unknown"  # "nvidia", "amd", "apple", "intel", "cpu"
    total_vram_mb: int = 0
    free_vram_mb: int = 0
    driver_version: Optional[str] = None
    pci_bus_id: Optional[str] = None
    compute_capability: Optional[str] = None

    @property
    def total_vram_gb(self) -> float:
        return round(self.total_vram_mb / 1024.0, 2)

    @property
    def free_vram_gb(self) -> float:
        return round(self.free_vram_mb / 1024.0, 2)

class HardwareProfile(BaseModel):
    os_name: str
    os_version: str
    architecture: str
    cpu_model: str
    cpu_physical_cores: int
    cpu_logical_cores: int
    total_ram_gb: float
    available_ram_gb: float
    gpus: List[GPUDevice] = Field(default_factory=list)
    total_vram_gb: float = 0.0
    primary_compute_device: str = "cpu"
    multi_gpu_enabled: bool = False
    spec_tier: str = "edge_cpu"
    spec_tier_label: str = "CPU-Only / Edge Topology"
    recommended_parameter_scale: str = "1B to 3B parameters"
    recommended_context_window: int = 4096
    recommended_quantization: str = "Q4_K_M"
    multi_gpu_strategy: str = "single_device"
    docker_gpu_runtime: Optional[str] = None
    detected_at: float = Field(default_factory=time.time)

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "os": f"{self.os_name} {self.os_version} ({self.architecture})",
            "cpu": f"{self.cpu_model} ({self.cpu_physical_cores}c/{self.cpu_logical_cores}t)",
            "ram": f"{self.total_ram_gb} GB Total ({self.available_ram_gb} GB Free)",
            "gpu_count": len(self.gpus),
            "gpus": [f"[{g.index}] {g.name} ({g.total_vram_gb} GB VRAM, {g.vendor.upper()})" for g in self.gpus],
            "total_vram_gb": self.total_vram_gb,
            "primary_compute_device": self.primary_compute_device,
            "spec_tier": self.spec_tier,
            "spec_tier_label": self.spec_tier_label,
            "recommended_parameter_scale": self.recommended_parameter_scale,
            "multi_gpu_enabled": self.multi_gpu_enabled,
            "multi_gpu_strategy": self.multi_gpu_strategy
        }

    def evaluate_model_fit(self, model_name: str) -> Dict[str, Any]:
        """
        Calculates factual VRAM fit percentage and execution mode
        (100% VRAM offload vs Hybrid CPU/RAM vs Out-of-Memory) for any model name.
        """
        name_lower = model_name.lower()

        # Surgical parameter scale extraction (e.g. 1b, 1.5b, 3.2, 7b, 14b, 70b)
        param_b = 3.0
        match = re.search(r'[:_\-](\d+(?:\.\d+)?)b', name_lower)
        if not match:
            match = re.search(r'(\d+(?:\.\d+)?)b', name_lower)

        if match:
            param_b = float(match.group(1))
        elif "3.2" in name_lower:
            param_b = 3.2
        elif "3.3" in name_lower:
            param_b = 70.0
        elif "mini" in name_lower:
            param_b = 3.8

        # Memory required at standard 4-bit quant (Q4_K_M) + 4k context (~0.7 GB per billion params + 1.2GB context)
        required_vram_gb = round((param_b * 0.75) + 1.2, 2)
        available_vram = self.total_vram_gb

        if available_vram >= required_vram_gb:
            return {
                "model": model_name,
                "param_scale": f"{param_b}B",
                "required_vram_gb": required_vram_gb,
                "fit_status": "optimal",
                "fit_label": "100% GPU VRAM Offload",
                "can_run_full_speed": True,
                "offload_percentage": 100
            }
        elif (available_vram + self.available_ram_gb) >= (required_vram_gb * 1.2):
            offload_pct = int(min(90, (available_vram / required_vram_gb) * 100)) if available_vram > 0 else 0
            return {
                "model": model_name,
                "param_scale": f"{param_b}B",
                "required_vram_gb": required_vram_gb,
                "fit_status": "hybrid",
                "fit_label": f"Hybrid ({offload_pct}% VRAM, {100 - offload_pct}% System RAM)",
                "can_run_full_speed": False,
                "offload_percentage": offload_pct
            }
        else:
            return {
                "model": model_name,
                "param_scale": f"{param_b}B",
                "required_vram_gb": required_vram_gb,
                "fit_status": "exceeds",
                "fit_label": "Exceeds Hardware Capacity",
                "can_run_full_speed": False,
                "offload_percentage": 0
            }


class HardwareSpecProfiler:
    """
    Surgically inspects local hardware across Windows, Linux, and macOS.
    Discovers GPU accelerators, calculates VRAM boundaries, and sets model execution parameters.
    """

    @classmethod
    def get_profile(cls, force_refresh: bool = False) -> HardwareProfile:
        global _CACHED_PROFILE, _LAST_PROFILE_TIME
        now = time.time()
        if not force_refresh and _CACHED_PROFILE is not None and (now - _LAST_PROFILE_TIME) < 15.0:
            return _CACHED_PROFILE

        os_name = platform.system()
        os_version = platform.release()
        architecture = platform.machine()

        cpu_model, cpu_phys, cpu_log = cls._detect_cpu()
        total_ram_gb, avail_ram_gb = cls._detect_ram()
        gpus = cls._detect_gpus(os_name)

        total_vram_mb = sum(g.total_vram_mb for g in gpus)
        total_vram_gb = round(total_vram_mb / 1024.0, 2)
        multi_gpu = len(gpus) > 1

        # Classify hardware spec tier
        tier, tier_label, param_scale, ctx_window, quant, multi_strat, docker_runtime = cls._classify_tier(
            os_name=os_name,
            total_vram_gb=total_vram_gb,
            gpus=gpus,
            total_ram_gb=total_ram_gb
        )

        primary_device = "cpu"
        if gpus:
            if gpus[0].vendor == "nvidia":
                primary_device = "cuda:0" if not multi_gpu else f"cuda:0-{len(gpus)-1}"
            elif gpus[0].vendor == "amd":
                primary_device = "rocm:0"
            elif gpus[0].vendor == "apple":
                primary_device = "mps"
            elif gpus[0].vendor == "intel":
                primary_device = "oneapi:0"

        profile = HardwareProfile(
            os_name=os_name,
            os_version=os_version,
            architecture=architecture,
            cpu_model=cpu_model,
            cpu_physical_cores=cpu_phys,
            cpu_logical_cores=cpu_log,
            total_ram_gb=total_ram_gb,
            available_ram_gb=avail_ram_gb,
            gpus=gpus,
            total_vram_gb=total_vram_gb,
            primary_compute_device=primary_device,
            multi_gpu_enabled=multi_gpu,
            spec_tier=tier,
            spec_tier_label=tier_label,
            recommended_parameter_scale=param_scale,
            recommended_context_window=ctx_window,
            recommended_quantization=quant,
            multi_gpu_strategy=multi_strat,
            docker_gpu_runtime=docker_runtime,
            detected_at=now
        )

        _CACHED_PROFILE = profile
        _LAST_PROFILE_TIME = now
        return profile

    @classmethod
    def _detect_cpu(cls) -> tuple:
        """Detects CPU model name, physical cores, and logical cores."""
        cpu_phys = os.cpu_count() or 4
        cpu_log = os.cpu_count() or 4
        cpu_model = platform.processor() or "Modern Multi-Core Processor"

        try:
            import psutil
            cpu_phys = psutil.cpu_count(logical=False) or cpu_phys
            cpu_log = psutil.cpu_count(logical=True) or cpu_log
        except Exception:
            pass

        if platform.system() == "Windows":
            try:
                out = subprocess.check_output(
                    ["wmic", "cpu", "get", "name"],
                    stderr=subprocess.DEVNULL,
                    encoding="utf-8"
                )
                lines = [l.strip() for l in out.splitlines() if l.strip() and "Name" not in l]
                if lines:
                    cpu_model = lines[0]
            except Exception:
                pass
        elif platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            cpu_model = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
        elif platform.system() == "Darwin":
            try:
                out = subprocess.check_output(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    stderr=subprocess.DEVNULL,
                    encoding="utf-8"
                )
                if out.strip():
                    cpu_model = out.strip()
            except Exception:
                pass

        return cpu_model, cpu_phys, cpu_log

    @classmethod
    def _detect_ram(cls) -> tuple:
        """Detects system total RAM and available RAM in GB."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return round(mem.total / (1024**3), 2), round(mem.available / (1024**3), 2)
        except Exception:
            pass

        # Fallback estimation
        return 16.0, 8.0

    @classmethod
    def _detect_gpus(cls, os_name: str) -> List[GPUDevice]:
        """Cross-platform multi-GPU detection with vendor classification."""
        devices: List[GPUDevice] = []

        # 1. Try NVIDIA SMI (Works on Windows and Linux)
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.free,driver_version,pci.bus_id", "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL,
                encoding="utf-8"
            )
            for line in out.strip().splitlines():
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    idx = int(parts[0]) if parts[0].isdigit() else 0
                    name = parts[1]
                    tot_mb = int(float(parts[2])) if parts[2].replace('.', '', 1).isdigit() else 0
                    free_mb = int(float(parts[3])) if parts[3].replace('.', '', 1).isdigit() else 0
                    driver = parts[4] if len(parts) > 4 else None
                    pci = parts[5] if len(parts) > 5 else None
                    devices.append(GPUDevice(
                        index=idx,
                        name=name,
                        vendor="nvidia",
                        total_vram_mb=tot_mb,
                        free_vram_mb=free_mb,
                        driver_version=driver,
                        pci_bus_id=pci
                    ))
            if devices:
                return devices
        except Exception:
            pass

        # 2. Try AMD ROCm SMI (Linux)
        if os_name == "Linux":
            try:
                out = subprocess.check_output(
                    ["rocm-smi", "--showmeminfo", "vram", "--showproductname", "--json"],
                    stderr=subprocess.DEVNULL,
                    encoding="utf-8"
                )
                import json
                data = json.loads(out)
                for k, v in data.items():
                    if "card" in k.lower():
                        name = v.get("Card Series", "AMD Radeon / Instinct")
                        vram_total = int(v.get("VRAM Total Memory (B)", 0)) // (1024 * 1024)
                        vram_free = int(v.get("VRAM Total Used Memory (B)", 0)) // (1024 * 1024)
                        devices.append(GPUDevice(
                            index=len(devices),
                            name=name,
                            vendor="amd",
                            total_vram_mb=vram_total,
                            free_vram_mb=max(0, vram_total - vram_free)
                        ))
                if devices:
                    return devices
            except Exception:
                pass

        # 3. Try Apple Silicon (Darwin / macOS Metal Unified Memory)
        if os_name == "Darwin":
            try:
                out = subprocess.check_output(
                    ["system_profiler", "SPDisplaysDataType"],
                    stderr=subprocess.DEVNULL,
                    encoding="utf-8"
                )
                if "Apple" in out:
                    # Apple Silicon shares unified memory
                    total_ram_gb, _ = cls._detect_ram()
                    # Unified memory makes ~75% accessible to Metal GPU
                    metal_vram_mb = int(total_ram_gb * 0.75 * 1024)
                    devices.append(GPUDevice(
                        index=0,
                        name="Apple Silicon (Metal Unified Architecture)",
                        vendor="apple",
                        total_vram_mb=metal_vram_mb,
                        free_vram_mb=int(metal_vram_mb * 0.7),
                        compute_capability="Metal 3"
                    ))
                    return devices
            except Exception:
                pass

        # 4. Fallback on Windows WMI for general video controller detection
        if os_name == "Windows" and not devices:
            try:
                out = subprocess.check_output(
                    ["wmic", "path", "win32_VideoController", "get", "name,adapterram"],
                    stderr=subprocess.DEVNULL,
                    encoding="utf-8"
                )
                for line in out.strip().splitlines():
                    if "Name" in line or not line.strip():
                        continue
                    parts = line.strip().rsplit(None, 1)
                    if len(parts) >= 1:
                        name = parts[0].strip()
                        ram_b = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                        vram_mb = ram_b // (1024 * 1024)
                        vendor = "intel" if "intel" in name.lower() else ("amd" if "amd" in name.lower() or "radeon" in name.lower() else "unknown")
                        devices.append(GPUDevice(
                            index=len(devices),
                            name=name,
                            vendor=vendor,
                            total_vram_mb=vram_mb,
                            free_vram_mb=vram_mb // 2
                        ))
                if devices:
                    return devices
            except Exception:
                pass

        return devices

    @classmethod
    def _classify_tier(cls, os_name: str, total_vram_gb: float, gpus: List[GPUDevice], total_ram_gb: float) -> tuple:
        """Categorizes hardware into architectural spec tiers with exact model guidance."""
        has_nvidia = any(g.vendor == "nvidia" for g in gpus)
        docker_runtime = "nvidia" if has_nvidia else None

        if len(gpus) > 1 and total_vram_gb >= 24.0:
            return (
                "ultra_multigpu",
                f"Multi-GPU Rig ({len(gpus)}x GPUs, {total_vram_gb} GB Combined VRAM)",
                "32B to 70B parameters (Tensor/Pipeline Parallelism)",
                32768,
                "Q4_K_M / Q5_K_M",
                "tensor_parallel_split",
                docker_runtime
            )
        elif total_vram_gb >= 16.0:
            return (
                "high_gpu",
                f"High-End Discrete GPU ({total_vram_gb} GB VRAM)",
                "14B to 32B parameters (Full VRAM Offload)",
                16384,
                "Q5_K_M / Q8_0",
                "single_device",
                docker_runtime
            )
        elif total_vram_gb >= 6.5:
            # 8GB VRAM cards like RTX 5060, RTX 4060, RTX 3070
            return (
                "mid_gpu",
                f"Mid-Range Performance GPU ({total_vram_gb} GB VRAM)",
                "3B to 8B parameters (Full VRAM Offload at 150+ tokens/s)",
                8192,
                "Q4_K_M / FP16",
                "single_device",
                docker_runtime
            )
        elif total_vram_gb >= 3.5:
            return (
                "entry_gpu",
                f"Entry Discrete GPU ({total_vram_gb} GB VRAM)",
                "1B to 3B parameters (Full VRAM Offload)",
                4096,
                "Q4_K_M",
                "single_device",
                docker_runtime
            )
        else:
            # CPU or integrated GPU
            ram_guidance = "1B to 3B parameters" if total_ram_gb >= 8.0 else "1B parameters"
            return (
                "edge_cpu",
                f"CPU-Only / Edge Topology ({total_ram_gb} GB RAM)",
                f"{ram_guidance} (Quantized CPU Inference)",
                2048,
                "Q4_0",
                "cpu_multithread",
                None
            )
