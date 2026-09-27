"""
Domain Knowledge Base & Architectural Archetypes for Gestalt.
Provides high-fidelity, production-grade topologies for 10+ engineering paradigms,
plus a dynamic compositional synthesizer for arbitrary user seed concepts.
"""

import re
from typing import Dict, Any, List, Optional
from .topology import BlueprintState, Node, Edge, Invariant, ProbeFork, ProbeOption

class DomainKnowledge:
    @classmethod
    def match_and_project(cls, seed: str) -> Optional[BlueprintState]:
        s = seed.lower()

        # 1. AI Agents & Autonomous Swarms
        if any(k in s for k in ["swarm", "agent", "multi-agent", "autonomous", "reasoning", "orchestrat", "rag", "bot"]):
            return cls._archetype_agent_swarm(seed)

        # 2. Local-First / P2P / CRDT
        if any(k in s for k in ["p2p", "mesh", "decentral", "crdt", "local-first", "offline", "sync"]):
            return cls._archetype_p2p_crdt(seed)

        # 3. High-Frequency Trading & Low-Latency FinTech
        if any(k in s for k in ["trad", "market", "order", "exchange", "arbitrage", "financial", "crypto", "signal", "matching"]):
            return cls._archetype_trading_engine(seed)

        # 4. Multiplayer Games & Physics Simulation
        if any(k in s for k in ["game", "multiplayer", "physics", "simulation", "ecs", "tick", "world"]):
            return cls._archetype_game_server(seed)

        # 5. Computer Vision & Real-Time Multimodal Pipelines
        if any(k in s for k in ["vision", "camera", "video", "rtsp", "image", "detection", "yolo", "tracking", "stream"]):
            return cls._archetype_computer_vision(seed)

        # 6. IoT Sensors & Edge Telemetry
        if any(k in s for k in ["iot", "sensor", "telemetry", "mqtt", "hardware", "device", "edge"]):
            return cls._archetype_iot_edge(seed)

        # 7. Cybersecurity, Zero-Trust & SIEM
        if any(k in s for k in ["security", "zero-trust", "firewall", "siem", "threat", "ebpf", "quarantine", "audit"]):
            return cls._archetype_cybersecurity(seed)

        # 8. Autonomous Robotics & Drones
        if any(k in s for k in ["robot", "drone", "lidar", "slam", "ros", "motor", "autopilot", "navigation"]):
            return cls._archetype_robotics(seed)

        # 9. Developer Tools, Compilers & Code Synthesis
        if any(k in s for k in ["compiler", "devtool", "ast", "code", "ide", "syntax", "lsp", "linter"]):
            return cls._archetype_devtools(seed)

        # 10. Real-Time Media & Social Streaming
        if any(k in s for k in ["social", "feed", "webrtc", "sfu", "live", "chat", "presence", "broadcast"]):
            return cls._archetype_media_streaming(seed)

        # 11. Dynamic Compositional Synthesizer (Catches ANY arbitrary concept)
        return cls._dynamic_compositional_synthesizer(seed)

    # -------------------------------------------------------------------------
    # 1. AI AGENT SWARM ARCHETYPE
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_agent_swarm(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="user_intent_canvas", label="Multimodal Intent Ingestion", tier="presentation", state_type="stateless", latency_ms=10, description="Spatial & voice prompt ingestion surface"),
            Node(id="swarm_supervisor", label="Metacognitive Swarm Supervisor", tier="compute", state_type="in-memory", latency_ms=120, description="Task decomposition, dynamic budget allocation, and DAG synthesis"),
            Node(id="specialist_workers", label="Parallel Domain Specialists", tier="compute", state_type="stateless", latency_ms=350, description="Specialized worker pool (Code, Research, Synthesis, Tool-Execution)"),
            Node(id="episodic_memory_graph", label="Episodic Vector & Knowledge Graph", tier="state", state_type="persistent", latency_ms=25, description="Hybrid vector embedding + semantic relationship store"),
            Node(id="tool_sandbox_substrate", label="Sandboxed Tool Substrate", tier="gateway", state_type="stateless", latency_ms=40, description="gRPC/MCP sandboxed runtime for shell and API execution"),
            Node(id="adversarial_auditor", label="Adversarial Verification Gate", tier="security", state_type="stateless", latency_ms=150, description="Pre-flight formal invariant and contract validator")
        ]
        edges = [
            Edge(source="user_intent_canvas", target="swarm_supervisor", protocol="websocket", label="Intent Stream"),
            Edge(source="swarm_supervisor", target="episodic_memory_graph", protocol="sync-rpc", label="Prior Context Recall"),
            Edge(source="swarm_supervisor", target="specialist_workers", protocol="event-stream", label="DAG Sub-task Dispatch", async_flow=True),
            Edge(source="specialist_workers", target="tool_sandbox_substrate", protocol="grpc", label="MCP Tool Invocation"),
            Edge(source="specialist_workers", target="adversarial_auditor", protocol="sync-rpc", label="Candidate Output"),
            Edge(source="adversarial_auditor", target="swarm_supervisor", protocol="sync-rpc", label="Pass/Fail Audit Loop")
        ]
        invariants = [
            Invariant(statement="All tool executions outside the sandbox boundary are forbidden", category="security", severity="critical"),
            Invariant(statement="Self-correction loops must terminate within bounded iteration budget (<= 4 turns)", category="fault-tolerance", severity="critical"),
            Invariant(statement="No intermediate unverified agent hallucinatory output may cross into presentation tier", category="security", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Swarm Coordination Topology",
                question="How should specialist agents communicate and share intermediate findings?",
                cognitive_tension="Centralized Hierarchical routing prevents agent confusion and looping, while a Reactive Shared Blackboard maximizes emergent collective intelligence.",
                options=[
                    ProbeOption(
                        id="hierarchical_supervisor",
                        label="Hierarchical Supervisor with Verification Gate",
                        description="Supervisor owns task tree; workers cannot communicate horizontally without supervisor review.",
                        tradeoff="Eliminates hallucination cascades and runaway token spend; adds slight supervisor coordination latency.",
                        added_invariants=["Horizontal peer-to-peer agent messages are restricted; all state passes through supervisor"]
                    ),
                    ProbeOption(
                        id="shared_reactive_blackboard",
                        label="Decentralized Reactive Blackboard (CRDT Scratchpad)",
                        description="Agents concurrently append thoughts, critiques, and partial solutions to an in-memory blackboard.",
                        tradeoff="Higher throughput and collaborative synthesis; requires explicit conflict resolution on blackboard edits.",
                        added_nodes=[
                            {"id": "crdt_blackboard", "label": "Reactive State Blackboard", "tier": "state", "state_type": "crdt", "latency_ms": 5, "description": "High-throughput shared scratchpad"}
                        ],
                        added_edges=[
                            {"source": "specialist_workers", "target": "crdt_blackboard", "protocol": "event-stream", "label": "Blackboard Deltas", "async_flow": True}
                        ],
                        added_invariants=["Blackboard mutations must resolve deterministically via CRDT delta rules"]
                    )
                ]
            ),
            ProbeFork(
                dimension="Memory Retrieval Paradigm",
                question="How does the swarm retain context across sessions and multi-step plans?",
                cognitive_tension="Vector RAG is fast to index, while a Structured Entity-Relation Graph maintains exact causal truth.",
                options=[
                    ProbeOption(
                        id="entity_relation_graph",
                        label="Dynamic Entity-Relation Knowledge Graph",
                        description="Maintains typed nodes, edges, and causal relations. Zero hallucination on entity attributes.",
                        tradeoff="Requires entity extraction pass on write; slower ingestion.",
                        added_invariants=["All factual deductions must link to verified entity graph nodes"]
                    ),
                    ProbeOption(
                        id="hybrid_sparse_dense_rag",
                        label="Hybrid Sparse-Dense RAG (BM25 + Dense Embeddings)",
                        description="Fast lexical and semantic retrieval with reciprocal rank fusion.",
                        tradeoff="Lower computational overhead; occasional fuzzy semantic drift.",
                        added_invariants=["Context retrieval must be filtered by minimum cosine similarity threshold"]
                    )
                ]
            )
        ]
        return BlueprintState(
            seed=seed,
            title="Autonomous Multi-Agent Cognitive Swarm",
            convergence_pct=30,
            nodes=nodes,
            edges=edges,
            invariants=invariants,
            active_probes=probes,
            version=1
        )

    # -------------------------------------------------------------------------
    # 2. LOCAL-FIRST / P2P / CRDT
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_p2p_crdt(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="edge_client", label="Local Edge Client", tier="edge", state_type="in-memory", latency_ms=4, description="Local replica running in client memory"),
            Node(id="crdt_engine", label="Delta-CRDT Engine", tier="state", state_type="crdt", latency_ms=2, description="State-based and operation-based conflict-free store"),
            Node(id="gossip_transport", label="Gossip Transport (WebRTC/libp2p)", tier="gateway", state_type="stateless", latency_ms=35, description="Direct peer-to-peer gossip dissemination"),
            Node(id="relay_witness", label="Stateless Relay & Turn Witness", tier="compute", state_type="stateless", latency_ms=20, description="NAT puncture coordinator and offline stash")
        ]
        edges = [
            Edge(source="edge_client", target="crdt_engine", protocol="sync-rpc", label="Local Mutate"),
            Edge(source="crdt_engine", target="gossip_transport", protocol="event-stream", label="Delta State Diffs", async_flow=True),
            Edge(source="gossip_transport", target="relay_witness", protocol="p2p", label="Gossip Broadcast", async_flow=True)
        ]
        invariants = [
            Invariant(statement="Offline operations must succeed without remote consensus", category="consistency", severity="critical"),
            Invariant(statement="State merges must be strictly commutative, associative, and idempotent", category="consistency", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Conflict Resolution Strategy",
                question="How should simultaneous conflicting modifications be resolved across peers?",
                cognitive_tension="Pure CRDT mathematical convergence guarantees deterministic state without authority, while operational transform allows intent-preserving textual merges.",
                options=[
                    ProbeOption(
                        id="pure_delta_crdt",
                        label="Delta-CRDT (Last-Write-Wins + Vector Clocks)",
                        description="Mathematical determinism. Zero coordinator intervention. Perfect offline merge.",
                        tradeoff="Requires strict monotonic timestamping or Lamport clocks; slight metadata overhead per field.",
                        added_nodes=[
                            {"id": "clock_tracker", "label": "Vector Clock Sentry", "tier": "compute", "state_type": "in-memory", "latency_ms": 1, "description": "Causal history and tombstone garbage collector"}
                        ],
                        added_edges=[
                            {"source": "crdt_engine", "target": "clock_tracker", "protocol": "sync-rpc", "label": "Causal Verification"}
                        ],
                        added_invariants=["Tombstones must be pruned via coordinated stable watermarks"]
                    ),
                    ProbeOption(
                        id="optimistic_peer_consensus",
                        label="Optimistic Peer-Consensus (Dynamic Raft Quorum)",
                        description="Peers propose changes; an elected peer validates business logic before final commit.",
                        tradeoff="Higher latency for finality; requires network quorum, degrading pure offline isolation.",
                        added_nodes=[
                            {"id": "quorum_leader", "label": "Dynamic Quorum Leader", "tier": "compute", "state_type": "persistent", "latency_ms": 25, "description": "Ephemeral elected peer ordering mutations"}
                        ],
                        added_edges=[
                            {"source": "gossip_transport", "target": "quorum_leader", "protocol": "grpc", "label": "Commit Proposal", "async_flow": False}
                        ],
                        added_invariants=["No transaction finality until >= 51% peer quorum ack"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Zero-Trust Local-First Mesh Architecture", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 3. HIGH-FREQUENCY TRADING / LOW-LATENCY FINTECH
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_trading_engine(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="market_feed", label="Market Ingress (Kernel Bypass)", tier="gateway", state_type="stateless", latency_ms=1, description="Solarflare EF_VI / DPDK raw packet parser"),
            Node(id="disruptor_ring", label="LMAX Disruptor Ring Buffer", tier="compute", state_type="in-memory", latency_ms=0, description="Single-writer lockless ring buffer across CPU cores"),
            Node(id="pre_trade_risk", label="Hardware Pre-Trade Risk Filter", tier="security", state_type="in-memory", latency_ms=1, description="Strict position limits, margin checks, and fat-finger aborts"),
            Node(id="order_matcher", label="Matching & Execution Engine", tier="compute", state_type="in-memory", latency_ms=2, description="Price-time priority deterministic limit order book"),
            Node(id="dma_outbound", label="DMA Outbound Gateway", tier="gateway", state_type="stateless", latency_ms=2, description="Direct Market Access binary FIX/ITCH outbound gateway")
        ]
        edges = [
            Edge(source="market_feed", target="disruptor_ring", protocol="shared-mem", label="Zero-Copy Ticks"),
            Edge(source="disruptor_ring", target="pre_trade_risk", protocol="shared-mem", label="Pre-Order Tick"),
            Edge(source="pre_trade_risk", target="order_matcher", protocol="shared-mem", label="Risk-Cleared Intent"),
            Edge(source="order_matcher", target="dma_outbound", protocol="sync-rpc", label="Signed Execution Order")
        ]
        invariants = [
            Invariant(statement="Zero heap allocations on the hot execution path (zero GC pause)", category="performance", severity="critical"),
            Invariant(statement="Pre-trade risk invariant must execute prior to network packet dispatch", category="security", severity="critical"),
            Invariant(statement="End-to-end 99th percentile processing latency must remain sub-50 microseconds", category="performance", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Audit Durability & Journaling",
                question="When does an execution order get committed to durable storage?",
                cognitive_tension="Synchronous NVMe Direct-IO guarantees zero record loss on power failure, while an Asynchronous Mapped Ring Buffer keeps the hot execution path sub-microsecond.",
                options=[
                    ProbeOption(
                        id="async_mmap_journal",
                        label="Async Memory-Mapped Ring Buffer (Sub-Microsecond)",
                        description="Hot thread logs to kernel memory pages; background thread flushes to disk.",
                        tradeoff="Microsecond risk of losing uncommitted log frames during immediate hardware kernel panic.",
                        added_nodes=[
                            {"id": "mmap_journal_logger", "label": "Kernel Mapped Journaler", "tier": "storage", "state_type": "append-only", "latency_ms": 5, "description": "Batched disk flusher"}
                        ],
                        added_edges=[
                            {"source": "order_matcher", "target": "mmap_journal_logger", "protocol": "shared-mem", "label": "Async Journal", "async_flow": True}
                        ],
                        added_invariants=["Hot thread execution loop must never block on OS page faults or disk writes"]
                    ),
                    ProbeOption(
                        id="sync_nvme_barrier",
                        label="Synchronous Hardware NVMe Commit Barrier",
                        description="Every execution decision is written to high-speed NVMe block storage before outbound wire dispatch.",
                        tradeoff="Adds 50-120 microseconds to trade cycle; guarantees zero lost records.",
                        added_nodes=[
                            {"id": "nvme_sync_barrier", "label": "Hardware DirectIO Journal", "tier": "storage", "state_type": "persistent", "latency_ms": 1, "description": "Synchronous block storage ack"}
                        ],
                        added_edges=[
                            {"source": "order_matcher", "target": "nvme_sync_barrier", "protocol": "sync-rpc", "label": "Sync Barrier Ack"}
                        ],
                        added_invariants=["Order outbound packet cannot leave network card without storage ACK"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Ultra-Low-Latency Order & Signal Pipeline", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 4. MULTIPLAYER GAME SERVER & PHYSICS SIMULATION
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_game_server(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="client_renderer", label="Client Game Client & Prediction", tier="presentation", state_type="in-memory", latency_ms=16, description="Client-side prediction, input sampling, and render loop (60/120 FPS)"),
            Node(id="packet_serializer", label="UDP/WebTransport Protocol Gateway", tier="gateway", state_type="stateless", latency_ms=5, description="Unreliable sequenced UDP socket handling delta compression"),
            Node(id="authoritative_world", label="Authoritative ECS Simulation Core", tier="compute", state_type="in-memory", latency_ms=15, description="Entity Component System world state running at fixed 64Hz/128Hz tick"),
            Node(id="spatial_hash_grid", label="Spatial Partitioning Grid (BVH)", tier="compute", state_type="in-memory", latency_ms=2, description="Broad-phase collision detection and interest management"),
            Node(id="lag_compensator", label="Rewind & Lag Compensation Engine", tier="compute", state_type="in-memory", latency_ms=5, description="Historical tick buffer for hit-scan client reconciliation")
        ]
        edges = [
            Edge(source="client_renderer", target="packet_serializer", protocol="p2p", label="Client Input Packets"),
            Edge(source="packet_serializer", target="authoritative_world", protocol="shared-mem", label="Normalized Input Buffer"),
            Edge(source="authoritative_world", target="spatial_hash_grid", protocol="sync-rpc", label="Query Relevant Entities"),
            Edge(source="authoritative_world", target="lag_compensator", protocol="sync-rpc", label="Tick History Buffer"),
            Edge(source="authoritative_world", target="packet_serializer", protocol="event-stream", label="State Snapshots Diffs", async_flow=True)
        ]
        invariants = [
            Invariant(statement="Server world simulation tick rate must maintain fixed step interval without frame drift", category="performance", severity="critical"),
            Invariant(statement="Client inputs must be validated against physics boundaries to prevent speed and teleport cheats", category="security", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="World Synchronization Paradigm",
                question="How should entity state snapshots be transmitted to clients with variable ping?",
                cognitive_tension="Lockstep Determinism saves massive network bandwidth, while Server-Authoritative Delta Snapshots allow instant join and smooth recovery.",
                options=[
                    ProbeOption(
                        id="server_authoritative_snapshots",
                        label="Server-Authoritative Delta Snapshots + Entity Interpolation",
                        description="Server broadcasts compressed delta states; client interpolates render positions.",
                        tradeoff="Requires higher outbound bandwidth; guarantees zero desynchronization glitches.",
                        added_invariants=["Delta snapshots must be compressed with bit-packing and dictionary encoders"]
                    ),
                    ProbeOption(
                        id="deterministic_rollback",
                        label="Deterministic Rollback (GGPO / Lockstep Netcode)",
                        description="Clients run deterministic simulation; roll back and re-simulate when late inputs arrive.",
                        tradeoff="Simulations must be 100% bit-exact (no floating-point non-determinism); perfect for low-entity counts.",
                        added_invariants=["All mathematical operations must strictly use fixed-point arithmetic"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Authoritative Real-Time Game Server & ECS World", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 5. COMPUTER VISION & MULTIMODAL PIPELINES
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_computer_vision(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="rtsp_frame_grabber", label="RTSP Camera Ingest (Zero-Copy)", tier="gateway", state_type="stateless", latency_ms=5, description="Hardware accelerated video decoding (NVDEC/VAAPI)"),
            Node(id="gpu_batch_inference", label="TensorRT Neural Inference Engine", tier="compute", state_type="in-memory", latency_ms=18, description="Batched INT8/FP16 object detection (YOLO/RT-DETR)"),
            Node(id="spatial_tracker", label="Multi-Object Spatial Tracker (ByteTrack)", tier="compute", state_type="in-memory", latency_ms=6, description="Kalman filter and Hungarian matching for tracklet continuity"),
            Node(id="event_classifier", label="Spatial Rules & Anomaly Detector", tier="compute", state_type="stateless", latency_ms=10, description="Zone intrusion, boundary crossing, and gesture classification"),
            Node(id="alert_dispatcher", label="Real-Time Event & Webhook Dispatcher", tier="presentation", state_type="stateless", latency_ms=15, description="Low-latency WebSocket alert stream and video clip clip archiving")
        ]
        edges = [
            Edge(source="rtsp_frame_grabber", target="gpu_batch_inference", protocol="shared-mem", label="Decoded GPU Frames"),
            Edge(source="gpu_batch_inference", target="spatial_tracker", protocol="sync-rpc", label="Bounding Boxes & Confidence"),
            Edge(source="spatial_tracker", target="event_classifier", protocol="sync-rpc", label="Tracklet Trajectories"),
            Edge(source="event_classifier", target="alert_dispatcher", protocol="event-stream", label="Triggered Alert Events", async_flow=True)
        ]
        invariants = [
            Invariant(statement="Decoded video frames must remain in GPU VRAM without roundtrips to system RAM", category="performance", severity="critical"),
            Invariant(statement="Inference queue must drop stale non-key frames under backpressure to avoid frame lag", category="fault-tolerance", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Edge vs Cloud Inference Distribution",
                question="Where should the deep neural inference run?",
                cognitive_tension="Full Edge Inference guarantees zero bandwidth costs and data privacy, while Hybrid Cloud Offload enables ultra-large foundation vision models.",
                options=[
                    ProbeOption(
                        id="pure_edge_tensorrt",
                        label="Pure Edge Accelerated Inference (Jetson / NPU)",
                        description="All neural weights run locally on hardware accelerators. Completely air-gapped.",
                        tradeoff="Constrained to quantized models (< 10GB VRAM); zero recurring cloud server bills.",
                        added_invariants=["Local inference engine must maintain >= 30 FPS per camera stream"]
                    ),
                    ProbeOption(
                        id="hybrid_cloud_offload",
                        label="Hybrid Cloud Offload (Edge Filter + Cloud VLM)",
                        description="Edge detects motion/candidates; cloud VLM performs deep contextual reasoning.",
                        tradeoff="Requires active internet uplink; enables rich natural language reasoning.",
                        added_nodes=[
                            {"id": "cloud_vlm_reasoner", "label": "Cloud Vision-Language Reasoner", "tier": "compute", "state_type": "stateless", "latency_ms": 350, "description": "Deep foundation model for semantic scene description"}
                        ],
                        added_edges=[
                            {"source": "event_classifier", "target": "cloud_vlm_reasoner", "protocol": "grpc", "label": "Keyframe Upload", "async_flow": True}
                        ]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Real-Time Computer Vision & Spatial Analytics Pipeline", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 6. IOT SENSOR & EDGE TELEMETRY
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_iot_edge(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="sensor_bus", label="Edge Sensor Bus (I2C/SPI/CAN)", tier="edge", state_type="stateless", latency_ms=2, description="Microcontroller hardware sensor sampling"),
            Node(id="mqtt_broker", label="Lightweight Embedded MQTT/CoAP Broker", tier="gateway", state_type="stateless", latency_ms=8, description="QoS 0/1 sensor message ingestion"),
            Node(id="stream_compressor", label="Time-Series Delta Compressor", tier="compute", state_type="in-memory", latency_ms=5, description="Gorilla / snappy floating point time-series compression"),
            Node(id="edge_anomaly_sentry", label="Edge Anomaly & Threshold Sentry", tier="compute", state_type="in-memory", latency_ms=4, description="Local statistical Z-score and threshold trip-wire"),
            Node(id="cellular_uplink", label="Adaptive Cellular/Satellite Uplink", tier="gateway", state_type="persistent", latency_ms=80, description="Store-and-forward batch telemetry transmitter")
        ]
        edges = [
            Edge(source="sensor_bus", target="mqtt_broker", protocol="sync-rpc", label="Raw Telemetry"),
            Edge(source="mqtt_broker", target="stream_compressor", protocol="event-stream", label="Sensor Stream", async_flow=True),
            Edge(source="stream_compressor", target="edge_anomaly_sentry", protocol="shared-mem", label="Normalized Samples"),
            Edge(source="edge_anomaly_sentry", target="cellular_uplink", protocol="event-stream", label="Compressed Batches", async_flow=True)
        ]
        invariants = [
            Invariant(statement="Sensor data must be stored locally in persistent ring buffer when uplink is offline", category="fault-tolerance", severity="critical"),
            Invariant(statement="Critical hardware safety trip-wires must execute in < 10ms without network dependence", category="performance", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Uplink Transmission Strategy",
                question="How aggressively should telemetry be batched before wireless transmission?",
                cognitive_tension="Continuous real-time transmission drains device battery, while aggressive episodic batching saves 90% power at the cost of data freshness.",
                options=[
                    ProbeOption(
                        id="adaptive_duty_cycling",
                        label="Adaptive Duty-Cycling (Heartbeat + Anomaly Wakeup)",
                        description="Sleeps radio 99% of time; wakes up on high-frequency anomaly or hourly report.",
                        tradeoff="Extends battery life from 2 days to 3 years; routine telemetry has 1-hour latency.",
                        added_invariants=["Radio must enter deep sleep state when sensor variance is below threshold"]
                    ),
                    ProbeOption(
                        id="streaming_cellular_mqtt",
                        label="Persistent Cellular MQTT Stream (Real-Time)",
                        description="Maintains live MQTT connection; packets stream every 100ms.",
                        tradeoff="Requires wired power source or massive solar array; provides instantaneous live dashboards.",
                        added_invariants=["Connection must automatically reconnect with exponential backoff"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Autonomous IoT Edge Telemetry & Anomaly Pipeline", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 7. CYBERSECURITY, ZERO-TRUST & SIEM
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_cybersecurity(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="ebpf_probe", label="eBPF Kernel Sensor Hook", tier="edge", state_type="stateless", latency_ms=1, description="Linux kernel syscall, network socket, and file execution trace"),
            Node(id="packet_mirror", label="Flow Collector & Packet Dissector", tier="gateway", state_type="stateless", latency_ms=8, description="NetFlow/IPFIX flow aggregation and TLS handshake analyzer"),
            Node(id="behavioral_anomaly_engine", label="Behavioral Anomaly Engine", tier="compute", state_type="in-memory", latency_ms=20, description="Process lineage graph and MITRE ATT&CK correlation matrix"),
            Node(id="quarantine_enforcer", label="Zero-Trust Policy Enforcer", tier="security", state_type="stateless", latency_ms=5, description="Automated iptables, cgroups, and token revocation gate"),
            Node(id="immutable_audit_ledger", label="Append-Only Immutable Audit Log", tier="storage", state_type="append-only", latency_ms=15, description="WORM (Write Once Read Many) tamper-evident security ledger")
        ]
        edges = [
            Edge(source="ebpf_probe", target="behavioral_anomaly_engine", protocol="shared-mem", label="Kernel Telemetry"),
            Edge(source="packet_mirror", target="behavioral_anomaly_engine", protocol="event-stream", label="Network Flow Data", async_flow=True),
            Edge(source="behavioral_anomaly_engine", target="quarantine_enforcer", protocol="sync-rpc", label="Immediate Containment Directive"),
            Edge(source="behavioral_anomaly_engine", target="immutable_audit_ledger", protocol="event-stream", label="Forensic Trail", async_flow=True)
        ]
        invariants = [
            Invariant(statement="Security audit events cannot be modified or deleted once appended", category="security", severity="critical"),
            Invariant(statement="Automated quarantine intervention must complete in sub-50ms upon high-confidence threat detection", category="performance", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Automated Mitigation Authority",
                question="Should the system automatically isolate compromised nodes without human confirmation?",
                cognitive_tension="Autonomous Containment stops ransomware propagation in milliseconds, but risks accidental service disruption on false positives.",
                options=[
                    ProbeOption(
                        id="autonomous_zero_delay_quarantine",
                        label="Autonomous Zero-Delay Quarantine (Kill & Isolate)",
                        description="Immediately sever network interfaces and freeze process trees on signature breach.",
                        tradeoff="Guarantees containment; risks transient downtime on false-positive alerts.",
                        added_invariants=["Quarantined nodes must dump memory core dumps to forensics vault before termination"]
                    ),
                    ProbeOption(
                        id="advisory_escalation_gate",
                        label="Tiered Escalation with Human-in-the-Loop Sign-off",
                        description="Applies non-destructive rate limiting and alerts SOC analysts via secure token.",
                        tradeoff="Slower response (~minutes); completely prevents accidental production outages.",
                        added_invariants=["High-severity events trigger dual-custody authorization prompts"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Zero-Trust eBPF Kernel Threat Detection & Quarantine", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 8. AUTONOMOUS ROBOTICS & DRONES
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_robotics(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="sensor_fusion_lidar", label="LiDAR & IMU Sensor Fusion (EKF)", tier="edge", state_type="in-memory", latency_ms=3, description="Extended Kalman Filter fusing IMU gyro, wheel odometry, and LiDAR point clouds"),
            Node(id="slam_occupancy_grid", label="Real-Time SLAM & 3D Occupancy Map", tier="compute", state_type="in-memory", latency_ms=20, description="Voxel grid mapping and global localization"),
            Node(id="global_path_planner", label="Dynamic Trajectory & Obstacle Planner (A*/TEB)", tier="compute", state_type="in-memory", latency_ms=30, description="Kinodynamic motion planning and reactive obstacle avoidance"),
            Node(id="motor_pid_controller", label="Hardware Actuator & PID Motor Controller", tier="compute", state_type="in-memory", latency_ms=1, description="Hard real-time closed-loop PWM actuator controller (1000Hz)"),
            Node(id="hardware_safety_watchdog", label="Hardware Interlock & Safety Watchdog", tier="security", state_type="stateless", latency_ms=1, description="Independent hardware watchdog timer with emergency e-stop relay")
        ]
        edges = [
            Edge(source="sensor_fusion_lidar", target="slam_occupancy_grid", protocol="shared-mem", label="Fused Pose & Cloud"),
            Edge(source="slam_occupancy_grid", target="global_path_planner", protocol="sync-rpc", label="Costmap Grid"),
            Edge(source="global_path_planner", target="motor_pid_controller", protocol="shared-mem", label="Velocity Commands (Twist)"),
            Edge(source="motor_pid_controller", target="hardware_safety_watchdog", protocol="sync-rpc", label="Heartbeat Pulse")
        ]
        invariants = [
            Invariant(statement="Motor actuators must immediately safe-stop if control loop misses 3 consecutive heartbeats (3ms)", category="security", severity="critical"),
            Invariant(statement="Kinodynamic velocity must not exceed physical deceleration distance to nearest obstacle", category="safety", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Safety Intervention Hierarchy",
                question="How does the robot resolve conflicting path recommendations between high-level navigation and low-level obstacle sensors?",
                cognitive_tension="Hierarchical Priority gives ultrasonic/bumper hardware absolute veto over planner commands, while Costmap Blending allows smoother navigation around dynamic crowds.",
                options=[
                    ProbeOption(
                        id="hardware_sensor_absolute_veto",
                        label="Hardware Sensor Absolute Veto (Subsumption Architecture)",
                        description="Proximity sensors bypass high-level planner and directly kill motor driver PWM.",
                        tradeoff="Guarantees 100% collision prevention; robot may freeze in cluttered environments.",
                        added_invariants=["Hardware proximity breach immediately cuts motor power without software negotiation"]
                    ),
                    ProbeOption(
                        id="dynamic_costmap_inflation",
                        label="Dynamic Costmap Inflation & Predictive Evasion",
                        description="Obstacles dynamically inflate avoidance vectors in velocity space.",
                        tradeoff="Smooth, fluid movement without sudden hard stops; requires higher compute budget.",
                        added_invariants=["Planner must reserve 30% compute headroom for dynamic trajectory re-planning"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Autonomous Robotics SLAM & Hard-Real-Time Actuation", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 9. DEVELOPER TOOLS, COMPILERS & CODE SYNTHESIZERS
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_devtools(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="lsp_interface", label="LSP Server & Editor Gateway", tier="presentation", state_type="stateless", latency_ms=10, description="Language Server Protocol handler (hover, completion, diagnostics)"),
            Node(id="incremental_ast_parser", label="Tree-Sitter Incremental AST Engine", tier="compute", state_type="in-memory", latency_ms=5, description="Sub-millisecond incremental concrete syntax tree parser"),
            Node(id="semantic_symbol_graph", label="Semantic Symbol & Call Graph Index", tier="state", state_type="in-memory", latency_ms=15, description="Type-checked symbol table, cross-references, and dependency graph"),
            Node(id="isolated_sandbox_runner", label="Isolated Container Test Runner", tier="compute", state_type="stateless", latency_ms=120, description="Bubblewrap / firejail sandbox for compiling and running test suites")
        ]
        edges = [
            Edge(source="lsp_interface", target="incremental_ast_parser", protocol="sync-rpc", label="File Buffer Edits"),
            Edge(source="incremental_ast_parser", target="semantic_symbol_graph", protocol="sync-rpc", label="AST Delta Nodes"),
            Edge(source="semantic_symbol_graph", target="isolated_sandbox_runner", protocol="grpc", label="Execute Verification Suite", async_flow=True)
        ]
        invariants = [
            Invariant(statement="Incremental AST re-parse on keystroke must finish in sub-10ms", category="performance", severity="critical"),
            Invariant(statement="Arbitrary user code compilation must execute inside unprivileged sandbox with zero network access", category="security", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Index Persistence vs In-Memory Model",
                question="How should the codebase index be maintained across IDE restarts?",
                cognitive_tension="Persistent SQLite/LMDB cache allows instant startup on million-line repositories, while Pure In-Memory avoids index corruption bugs.",
                options=[
                    ProbeOption(
                        id="sqlite_mmap_index",
                        label="Persistent SQLite/LMDB Memory-Mapped Cache",
                        description="Serializes symbol graph to disk; warm startup in sub-200ms.",
                        tradeoff="Slight risk of stale cache on external git branch checkouts.",
                        added_invariants=["Index checksums must be validated against git HEAD commit hash"]
                    ),
                    ProbeOption(
                        id="ephemeral_memory_index",
                        label="Pure In-Memory Ephemeral Graph",
                        description="Builds index on cold boot; 100% bug-free and clean.",
                        tradeoff="Takes 3-10 seconds to index very large multi-gigabyte mono-repos.",
                        added_invariants=["Indexing worker must run on background threads without blocking LSP UI thread"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="High-Performance Developer Tooling & LSP Runtime", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 10. REAL-TIME MEDIA & STREAMING
    # -------------------------------------------------------------------------
    @classmethod
    def _archetype_media_streaming(cls, seed: str) -> BlueprintState:
        nodes = [
            Node(id="webrtc_ingress", label="WebRTC Media SFU (Selective Forwarding)", tier="gateway", state_type="stateless", latency_ms=12, description="RTP packet routing with dynamic simulcast bandwidth estimation"),
            Node(id="presence_mesh", label="Distributed Ephemeral Presence Mesh", tier="compute", state_type="in-memory", latency_ms=4, description="Redis / Fly.io gossip mesh tracking participant state and cursor positions"),
            Node(id="feed_materializer", label="Real-Time Fan-Out & Feed Materializer", tier="compute", state_type="stateless", latency_ms=30, description="PubSub message queue pushing timeline updates to active subscribers"),
            Node(id="edge_cdn_cache", label="Edge CDN Segment Cache", tier="state", state_type="in-memory", latency_ms=5, description="Sub-second segment and blob caching close to clients")
        ]
        edges = [
            Edge(source="webrtc_ingress", target="edge_cdn_cache", protocol="shared-mem", label="HLS/DASH Segments", async_flow=True),
            Edge(source="webrtc_ingress", target="presence_mesh", protocol="sync-rpc", label="Participant Heartbeat"),
            Edge(source="presence_mesh", target="feed_materializer", protocol="event-stream", label="State Deltas", async_flow=True)
        ]
        invariants = [
            Invariant(statement="End-to-end media delay must not exceed 200ms for live interactive streams", category="performance", severity="critical"),
            Invariant(statement="Participant presence disconnections must propagate to all clients in < 500ms", category="performance", severity="critical")
        ]
        probes = [
            ProbeFork(
                dimension="Fan-Out Strategy Under Spike Load",
                question="How should millions of concurrent subscribers receive live updates?",
                cognitive_tension="Push-based WebSockets provide zero latency, while Pull-based HTTP/3 Server-Sent Events allow global CDN caching.",
                options=[
                    ProbeOption(
                        id="websocket_push_cluster",
                        label="Stateful WebSocket Edge Push Cluster",
                        description="Maintains persistent open bidirectional connections to all clients.",
                        tradeoff="Instantaneous sub-10ms delivery; requires managing millions of concurrent open sockets.",
                        added_invariants=["Socket nodes must gracefully shed load or drop low-priority typing events under saturation"]
                    ),
                    ProbeOption(
                        id="cdn_cached_sse_stream",
                        label="CDN-Cached HTTP/3 Server-Sent Events (SSE)",
                        description="Streams text/events through globally distributed edge caches.",
                        tradeoff="Slight latency jitter (20-50ms); scales infinitely with zero infrastructure management.",
                        added_invariants=["SSE streams must include unique event IDs for client auto-reconnection"]
                    )
                ]
            )
        ]
        return BlueprintState(seed=seed, title="Ultra-Low-Latency Media Streaming & Presence Engine", convergence_pct=30, nodes=nodes, edges=edges, invariants=invariants, active_probes=probes)

    # -------------------------------------------------------------------------
    # 11. DYNAMIC COMPOSITIONAL SYNTHESIZER (For ANY arbitrary concept)
    # -------------------------------------------------------------------------
    @classmethod
    def _dynamic_compositional_synthesizer(cls, seed: str) -> BlueprintState:
        """
        Dynamically decomposes an arbitrary user phrase into custom nodes,
        relations, and deep Socratic probes based on extracted keywords.
        """
        words = re.findall(r'\b[a-zA-Z]{3,}\b', seed)
        clean_seed = " ".join(words[:12]) if words else "Custom Distributed System"
        
        # Derive custom title
        title_subject = words[0].capitalize() if words else "Dynamic"
        title = f"{title_subject} Adaptive Architecture Engine"

        nodes = [
            Node(id="ingress_gateway", label="High-Throughput Ingestion Gateway", tier="gateway", state_type="stateless", latency_ms=8, description=f"Validates, normalizes, and routes incoming {clean_seed} intents"),
            Node(id="domain_orchestrator", label="Core Domain Orchestrator", tier="compute", state_type="in-memory", latency_ms=25, description="Maintains domain state machine, execution policies, and invariants"),
            Node(id="reactive_event_bus", label="Reactive Event Backbone", tier="compute", state_type="in-memory", latency_ms=4, description="Zero-allocation event pipeline for asynchronous task distribution"),
            Node(id="state_ledger", label="Primary State Store & Ledger", tier="state", state_type="persistent", latency_ms=18, description="Durable persistence layer guaranteeing consistency and recovery"),
            Node(id="edge_dispatcher", label="Outbound Dispatch & Presentation Layer", tier="presentation", state_type="stateless", latency_ms=12, description="Formats results and notifies clients or physical actuators")
        ]

        edges = [
            Edge(source="ingress_gateway", target="domain_orchestrator", protocol="sync-rpc", label="Validated Command"),
            Edge(source="domain_orchestrator", target="state_ledger", protocol="sync-rpc", label="State Commit"),
            Edge(source="domain_orchestrator", target="reactive_event_bus", protocol="event-stream", label="Domain Events", async_flow=True),
            Edge(source="reactive_event_bus", target="edge_dispatcher", protocol="event-stream", label="State Projections", async_flow=True)
        ]

        invariants = [
            Invariant(statement=f"Commands for {clean_seed} must pass strict input schema validation prior to processing", category="security", severity="critical"),
            Invariant(statement="End-to-end processing pipeline must execute within latency budget without starvation", category="performance", severity="critical"),
            Invariant(statement="State mutations must be replayable from durable event log during node crash recovery", category="consistency", severity="critical")
        ]

        probes = [
            ProbeFork(
                dimension="Consistency & Concurrency Model",
                question=f"How should concurrent operations in {clean_seed} be reconciled?",
                cognitive_tension="Optimistic Concurrency with automated rollback provides high throughput under light contention, while Pessimistic Lock-Free Pipelines guarantee strict ordering.",
                options=[
                    ProbeOption(
                        id="optimistic_concurrency",
                        label="Optimistic Concurrency Control (Version Vectors)",
                        description="Permits parallel processing; detects conflicting writes and triggers retry loops.",
                        tradeoff="Ultra-high throughput under normal load; higher retry churn under extreme hotspot contention.",
                        added_invariants=["Transactions must include monotonic version tag for conflict detection"]
                    ),
                    ProbeOption(
                        id="partitioned_single_writer",
                        label="Partitioned Single-Writer Ring Buffer (Deterministic)",
                        description="Pins each domain entity to an isolated CPU thread; eliminates locking entirely.",
                        tradeoff="Guarantees zero lock contention; requires predictable hash partition distribution.",
                        added_nodes=[
                            {"id": "partition_router", "label": "Key-Partitioned Router", "tier": "compute", "state_type": "in-memory", "latency_ms": 2, "description": "Consistent-hashing thread allocator"}
                        ],
                        added_edges=[
                            {"source": "ingress_gateway", "target": "partition_router", "protocol": "sync-rpc", "label": "Partition Routing"}
                        ],
                        added_invariants=["Entity operations must execute on dedicated partition thread"]
                    )
                ]
            ),
            ProbeFork(
                dimension="Failure Boundary & Degradation",
                question="When a sub-component or downstream dependency fails, how should the architecture isolate it?",
                cognitive_tension="Strict Circuit Breaking aborts early to preserve cluster integrity, while Graceful Stale Fallback serves degraded heuristics to maintain 100% uptime.",
                options=[
                    ProbeOption(
                        id="strict_circuit_breaker",
                        label="Strict Circuit Breaker (Fail-Fast Isolation)",
                        description="Halt downstream calls instantly when error rate exceeds 5%; protect remaining nodes.",
                        tradeoff="Clients receive clear immediate error; prevents cascading outages across the cluster.",
                        added_invariants=["Circuit breaker trips after 3 consecutive timeouts or 10% error threshold"]
                    ),
                    ProbeOption(
                        id="graceful_heuristic_fallback",
                        label="Graceful Heuristic Fallback (Stale-While-Revalidate)",
                        description="Serve cached snapshot or synthetic heuristic if downstream is unresponsive.",
                        tradeoff="Maintains continuous client uptime; data may temporarily reflect slightly stale state.",
                        added_invariants=["Degraded responses must explicitly set 'X-Degraded-Fallback: true'"]
                    )
                ]
            )
        ]

        return BlueprintState(
            seed=seed,
            title=title,
            convergence_pct=30,
            nodes=nodes,
            edges=edges,
            invariants=invariants,
            active_probes=probes,
            version=1
        )
