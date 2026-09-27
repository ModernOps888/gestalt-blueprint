/**
 * GESTALT // Cognitive Topology & Socratic Blueprint Extractor
 * Client Application Logic & Interactive Canvas Engine
 */

let currentState = null;
let selectedNode = null;
let animationRunning = true;
let animFrameId = null;
let particles = [];

// DOM Elements
const seedInput = document.getElementById('seed-input');
const btnProject = document.getElementById('btn-project');
const probesContainer = document.getElementById('probes-container');
const convergenceFill = document.getElementById('convergence-fill');
const convergenceText = document.getElementById('convergence-text');
const blueprintTitle = document.getElementById('blueprint-title');
const nodeCountEl = document.getElementById('node-count');
const edgeCountEl = document.getElementById('edge-count');
const invariantCountEl = document.getElementById('invariant-count');
const decisionsCountEl = document.getElementById('decisions-count');
const decisionsBody = document.getElementById('decisions-body');
const engineNameEl = document.getElementById('engine-name');

// Canvas Elements
const canvas = document.getElementById('topology-canvas');
const ctx = canvas.getContext('2d');
const viewport = document.getElementById('canvas-viewport');

// Inspector Elements
const nodeInspector = document.getElementById('node-inspector');
const inspectTier = document.getElementById('inspect-tier');
const inspectLabel = document.getElementById('inspect-label');
const inspectState = document.getElementById('inspect-state');
const inspectLatency = document.getElementById('inspect-latency');
const inspectDesc = document.getElementById('inspect-desc');
const btnCloseInspect = document.getElementById('btn-close-inspect');

// Deliverables & Tabs
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');
const adrMarkdown = document.getElementById('adr-markdown');
const codeContent = document.getElementById('code-content');
const invariantsContainer = document.getElementById('invariants-container');
const btnExportDisk = document.getElementById('btn-export-disk');
const btnCopyCode = document.getElementById('btn-copy-code');

// Tier Color Palette
const TIER_COLORS = {
  edge: '#38bdf8',
  presentation: '#38bdf8',
  gateway: '#06b6d4',
  compute: '#8b5cf6',
  state: '#10b981',
  storage: '#f59e0b',
  security: '#f43f5e'
};

// --- INITIALIZATION ---
window.addEventListener('DOMContentLoaded', () => {
  initCanvas();
  checkEngineStatus();
  updateHistoryCount();
  setupEventListeners();
  startCanvasLoop();
});

function setupEventListeners() {
  // Preset Chips
  document.querySelectorAll('.preset-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      seedInput.value = chip.dataset.seed;
      triggerProjection(chip.dataset.seed);
    });
  });

  // Project Button
  btnProject.addEventListener('click', () => {
    const seed = seedInput.value.trim();
    if (seed) triggerProjection(seed);
  });

  // Tab Switching
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetPane = document.getElementById(`pane-${btn.dataset.tab}`);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // Close Inspector
  btnCloseInspect.addEventListener('click', () => {
    nodeInspector.classList.add('hidden');
    selectedNode = null;
  });

  // Canvas Flow Toggle
  const btnToggleFlow = document.getElementById('btn-toggle-flow');
  btnToggleFlow.addEventListener('click', () => {
    animationRunning = !animationRunning;
    btnToggleFlow.classList.toggle('active', animationRunning);
  });

  // Canvas Reset View / Layout
  document.getElementById('btn-fit').addEventListener('click', () => {
    if (currentState && currentState.nodes) {
      applyLayout(currentState.nodes);
    }
  });

  // Export to disk
  btnExportDisk.addEventListener('click', exportProject);

  // Copy code
  btnCopyCode.addEventListener('click', () => {
    navigator.clipboard.writeText(codeContent.innerText);
    btnCopyCode.innerText = 'Copied!';
    setTimeout(() => { btnCopyCode.innerText = 'Copy Code'; }, 1800);
  });

  // Decisions Toggle
  document.getElementById('decisions-toggle').addEventListener('click', () => {
    const body = document.getElementById('decisions-body');
    body.style.display = body.style.display === 'none' ? 'flex' : 'none';
  });

  // New Blueprint / Clear Canvas
  const btnNewBlueprint = document.getElementById('btn-new-blueprint');
  if (btnNewBlueprint) {
    btnNewBlueprint.addEventListener('click', clearCanvas);
  }

  // History Modal
  const btnHistory = document.getElementById('btn-history');
  const historyModal = document.getElementById('history-modal');
  const btnCloseHistory = document.getElementById('btn-close-history');

  if (btnHistory) {
    btnHistory.addEventListener('click', openHistoryModal);
  }
  if (btnCloseHistory) {
    btnCloseHistory.addEventListener('click', () => historyModal.classList.add('hidden'));
  }

  // Settings Modal
  const modal = document.getElementById('settings-modal');
  document.getElementById('btn-settings').addEventListener('click', () => modal.classList.remove('hidden'));
  document.getElementById('btn-close-modal').addEventListener('click', () => modal.classList.add('hidden'));
  document.getElementById('btn-save-settings').addEventListener('click', () => {
    modal.classList.add('hidden');
    checkEngineStatus();
  });
}

// --- CLEAR CANVAS & NEW BLUEPRINT ---
function clearCanvas() {
  currentState = null;
  selectedNode = null;
  particles = [];
  seedInput.value = '';
  convergenceFill.style.width = '0%';
  convergenceText.innerText = '0%';
  blueprintTitle.innerText = 'Emergent Topology';
  nodeCountEl.innerText = '0 Nodes';
  edgeCountEl.innerText = '0 Edges';
  invariantCountEl.innerText = '0 Invariants';
  probesContainer.innerHTML = '<div class="empty-state"><p>Project a seed idea above to generate architectural bifurcation probes.</p></div>';
  decisionsCountEl.innerText = '0';
  decisionsBody.innerHTML = '<p class="empty-text">No forks resolved yet.</p>';
  adrMarkdown.innerHTML = '<p class="empty-state">Generate a blueprint to preview the Architecture Decision Record.</p>';
  codeContent.innerText = '// Python executable scaffolding will appear here...';
  invariantsContainer.innerHTML = '<p class="empty-state">System guardrails & runtime assertions will list here.</p>';
  nodeInspector.classList.add('hidden');
}

// --- HISTORY LOGIC ---
async function updateHistoryCount() {
  try {
    const res = await fetch('/api/sessions');
    if (!res.ok) return;
    const items = await res.json();
    const countEl = document.getElementById('history-count');
    if (countEl) countEl.innerText = items.length;
  } catch (err) {
    console.error('Failed to fetch history count:', err);
  }
}

async function openHistoryModal() {
  const historyModal = document.getElementById('history-modal');
  const historyItemsList = document.getElementById('history-items-list');
  historyModal.classList.remove('hidden');
  historyItemsList.innerHTML = '<p class="empty-state">Loading saved blueprints...</p>';

  try {
    const res = await fetch('/api/sessions');
    if (!res.ok) throw new Error('Failed to load sessions');
    const items = await res.json();

    if (!items || items.length === 0) {
      historyItemsList.innerHTML = '<p class="empty-state">No saved blueprints found. Project an idea to save it automatically!</p>';
      return;
    }

    historyItemsList.innerHTML = items.map(s => `
      <div class="history-card">
        <div class="history-info">
          <div class="history-title">${s.title}</div>
          <div class="history-seed">"${s.seed}"</div>
          <div class="history-meta">
            <span>Convergence: ${s.convergence_pct}%</span>
            <span>•</span>
            <span>${s.node_count} Nodes</span>
            <span>•</span>
            <span>${s.edge_count} Edges</span>
            <span>•</span>
            <span>v${s.version}</span>
          </div>
        </div>
        <div class="history-actions">
          <button class="btn btn-sm btn-primary" onclick="loadSession('${s.session_id}')">Open</button>
          <button class="btn-danger-sm" onclick="deleteSession('${s.session_id}')">Delete</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    historyItemsList.innerHTML = `<p class="empty-state" style="color:var(--accent-rose);">Error: ${err.message}</p>`;
  }
}

window.loadSession = async function(sessionId) {
  try {
    const res = await fetch(`/api/session/${sessionId}`);
    if (!res.ok) throw new Error('Session not found');
    const state = await res.json();
    updateState(state);
    seedInput.value = state.seed || '';
    await fetchDeliverables(state.session_id);
    document.getElementById('history-modal').classList.add('hidden');
  } catch (err) {
    alert('Failed to load blueprint: ' + err.message);
  }
};

window.deleteSession = async function(sessionId) {
  if (!confirm('Are you sure you want to delete this blueprint?')) return;
  try {
    await fetch(`/api/session/${sessionId}`, { method: 'DELETE' });
    openHistoryModal();
    updateHistoryCount();
  } catch (err) {
    alert('Failed to delete session: ' + err.message);
  }
};

// --- ENGINE STATUS ---
async function checkEngineStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.provider === 'ollama') {
      engineNameEl.innerText = `Ollama (${data.active_model})`;
    } else if (data.provider === 'lmstudio') {
      engineNameEl.innerText = `LM Studio (${data.active_model})`;
    } else {
      engineNameEl.innerText = 'Built-in Cognitive Heuristics';
    }
  } catch (err) {
    engineNameEl.innerText = 'Cognitive Engine (Local Mode)';
  }
}

// --- TOPOLOGY PROJECTION ---
async function triggerProjection(seed) {
  btnProject.disabled = true;
  btnProject.innerHTML = `<span>Synthesizing Topology...</span>`;
  
  try {
    const res = await fetch('/api/project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seed })
    });
    
    if (!res.ok) throw new Error('Projection request failed');
    const state = await res.json();
    updateState(state);
    await fetchDeliverables(state.session_id);
  } catch (err) {
    alert('Failed to project topology: ' + err.message);
  } finally {
    btnProject.disabled = false;
    btnProject.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      Project Mental Topology
    `;
  }
}

// --- UPDATE STATE & UI ---
function updateState(state) {
  currentState = state;

  // Header metrics
  convergenceFill.style.width = `${state.convergence_pct}%`;
  convergenceText.innerText = `${state.convergence_pct}%`;
  blueprintTitle.innerText = state.title || 'Emergent Topology';
  nodeCountEl.innerText = `${state.nodes.length} Nodes`;
  edgeCountEl.innerText = `${state.edges.length} Edges`;
  invariantCountEl.innerText = `${state.invariants.length} Invariants`;

  // Apply layout coordinates to nodes
  applyLayout(state.nodes);

  // Re-seed edge animation particles
  initParticles(state);

  // Render Socratic Probes
  renderProbes(state.active_probes);

  // Render Decisions Log
  renderDecisions(state.resolved_decisions);

  // Render Invariants Tab
  renderInvariants(state.invariants);
}

// --- SOCRATIC BIFURCATION PROBES ---
function renderProbes(probes) {
  if (!probes || probes.length === 0) {
    probesContainer.innerHTML = `
      <div class="empty-state">
        <p>✓ All primary architectural forks resolved!</p>
        <p style="font-size:0.7rem; margin-top:6px; color: var(--accent-emerald);">
          Blueprint crystallized at ${currentState.convergence_pct}% convergence. Ready for code generation.
        </p>
      </div>
    `;
    return;
  }

  probesContainer.innerHTML = probes.map(p => `
    <div class="probe-card" data-probe-id="${p.id}">
      <div class="probe-dim">${p.dimension}</div>
      <div class="probe-question">${p.question}</div>
      <div class="probe-tension">" ${p.cognitive_tension} "</div>
      <div class="probe-options">
        ${p.options.map(opt => `
          <button class="probe-option-btn" onclick="resolveProbe('${p.id}', '${opt.id}')">
            <div class="opt-title">
              <span>${opt.label}</span>
              <span style="font-size:0.75rem; color:var(--accent-blue);">Select ➔</span>
            </div>
            <div class="opt-desc">${opt.description}</div>
            <div class="opt-tradeoff">⚡ Tradeoff: ${opt.tradeoff}</div>
          </button>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// --- RESOLVE PROBE STEP ---
window.resolveProbe = async function(probeId, optionId) {
  if (!currentState) return;

  try {
    const res = await fetch('/api/probe/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentState.session_id,
        probe_id: probeId,
        option_id: optionId
      })
    });

    if (!res.ok) throw new Error('Failed to resolve probe');
    const updatedState = await res.json();
    updateState(updatedState);
    await fetchDeliverables(updatedState.session_id);
  } catch (err) {
    console.error(err);
  }
};

// --- RENDER DECISIONS ---
function renderDecisions(decisions) {
  decisionsCountEl.innerText = decisions.length;
  if (!decisions || decisions.length === 0) {
    decisionsBody.innerHTML = `<p class="empty-text">No forks resolved yet.</p>`;
    return;
  }

  decisionsBody.innerHTML = decisions.map(d => `
    <div class="decision-item">
      <strong>${d.probe_dimension}:</strong> ${d.chosen_label}
      <div style="font-size:0.65rem; color:var(--text-muted);">${d.tradeoff}</div>
    </div>
  `).join('');
}

// --- RENDER INVARIANTS ---
function renderInvariants(invariants) {
  if (!invariants || invariants.length === 0) {
    invariantsContainer.innerHTML = `<p class="empty-state">No invariants declared.</p>`;
    return;
  }

  invariantsContainer.innerHTML = invariants.map((inv, idx) => `
    <div style="background:var(--bg-card); border:1px solid var(--border-subtle); padding:10px; border-radius:6px; margin-bottom:8px; border-left:3px solid var(--accent-rose);">
      <div style="display:flex; justify-content:space-between; font-size:0.68rem; font-family:var(--font-mono); color:var(--accent-cyan);">
        <span>[${inv.category.toUpperCase()}]</span>
        <span style="color:var(--accent-rose);">${inv.severity.toUpperCase()}</span>
      </div>
      <div style="font-size:0.78rem; font-weight:600; margin-top:4px;">${inv.statement}</div>
    </div>
  `).join('');
}

// --- DELIVERABLES & SYNTHESIS ---
async function fetchDeliverables(sessionId) {
  try {
    const res = await fetch('/api/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });
    if (!res.ok) return;

    const data = await res.json();
    const artifacts = data.artifacts;

    // 1. ADR Markdown
    adrMarkdown.innerHTML = renderMarkdownSimple(artifacts.adr_markdown);

    // 2. Code Scaffold
    if (artifacts.code_scaffold && artifacts.code_scaffold['main.py']) {
      codeContent.innerText = artifacts.code_scaffold['main.py'];
    }
  } catch (err) {
    console.error('Failed to fetch deliverables:', err);
  }
}

// Simple markdown formatter for ADR preview
function renderMarkdownSimple(md) {
  if (!md) return '';
  return md
    .replace(/^# (.*$)/gim, '<h2 style="font-size:1.1rem; color:#fff; margin-top:8px;">$1</h2>')
    .replace(/^## (.*$)/gim, '<h3 style="font-size:0.95rem; color:var(--accent-blue); margin-top:14px;">$1</h3>')
    .replace(/^### (.*$)/gim, '<h4 style="font-size:0.85rem; color:#fff; margin-top:10px;">$1</h4>')
    .replace(/^> (.*$)/gim, '<blockquote style="border-left:2px solid var(--accent-emerald); padding-left:8px; color:var(--text-muted); font-size:0.75rem; margin:6px 0;">$1</blockquote>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code style="background:var(--bg-card); padding:2px 4px; border-radius:3px; font-family:var(--font-mono); font-size:0.72rem; color:var(--accent-cyan);">$1</code>')
    .replace(/\n\n/gim, '<br/><br/>');
}

// --- EXPORT TO LOCAL DISK ---
async function exportProject() {
  if (!currentState) {
    alert('Please project a blueprint first!');
    return;
  }

  btnExportDisk.disabled = true;
  btnExportDisk.innerText = 'Exporting Files to Disk...';

  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentState.session_id })
    });
    const result = await res.json();
    alert(`✓ Project Successfully Exported to Disk!\n\nPath: ${result.exported_path}\nFiles: ${result.files.join(', ')}\n\nYou can run 'python main.py' directly from that directory!`);
  } catch (err) {
    alert('Export failed: ' + err.message);
  } finally {
    btnExportDisk.disabled = false;
    btnExportDisk.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      Export Project to Disk
    `;
  }
}

// --- CANVAS & TOPOLOGY GRAPH ENGINE ---
function initCanvas() {
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  // Mouse interaction
  let draggingNode = null;
  let dragOffset = { x: 0, y: 0 };

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (!currentState || !currentState.nodes) return;

    for (let n of currentState.nodes) {
      const dx = mouseX - n.x;
      const dy = mouseY - n.y;
      if (Math.sqrt(dx * dx + dy * dy) < 40) {
        draggingNode = n;
        dragOffset = { x: dx, y: dy };
        selectNode(n);
        break;
      }
    }
  });

  window.addEventListener('mousemove', (e) => {
    if (draggingNode) {
      const rect = canvas.getBoundingClientRect();
      draggingNode.x = e.clientX - rect.left - dragOffset.x;
      draggingNode.y = e.clientY - rect.top - dragOffset.y;
    }
  });

  window.addEventListener('mouseup', () => {
    draggingNode = null;
  });
}

function resizeCanvas() {
  const rect = viewport.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  if (currentState && currentState.nodes) {
    applyLayout(currentState.nodes);
  }
}

function selectNode(node) {
  selectedNode = node;
  inspectTier.innerText = node.tier.toUpperCase();
  inspectTier.style.background = TIER_COLORS[node.tier] || '#3b82f6';
  inspectLabel.innerText = node.label;
  inspectState.innerText = node.state_type;
  inspectLatency.innerText = `~${node.latency_ms}ms`;
  inspectDesc.innerText = node.description || 'No additional details.';
  nodeInspector.classList.remove('hidden');
}

function applyLayout(nodes) {
  const W = canvas.width || 800;
  const H = canvas.height || 600;

  // Tier vertical stratification
  const tierLevels = {
    presentation: 0.15,
    edge: 0.20,
    gateway: 0.35,
    compute: 0.55,
    state: 0.75,
    storage: 0.88,
    security: 0.55
  };

  const tierGroups = {};
  nodes.forEach(n => {
    tierGroups[n.tier] = tierGroups[n.tier] || [];
    tierGroups[n.tier].push(n);
  });

  Object.keys(tierGroups).forEach(tier => {
    const list = tierGroups[tier];
    const yRatio = tierLevels[tier] || 0.5;
    const y = H * yRatio;
    const spacing = W / (list.length + 1);

    list.forEach((n, idx) => {
      if (n.x === undefined || n.x === null) {
        n.x = spacing * (idx + 1);
        n.y = y;
      }
    });
  });
}

function initParticles(state) {
  particles = [];
  if (!state.edges) return;
  state.edges.forEach(edge => {
    for (let i = 0; i < 3; i++) {
      particles.push({
        edge: edge,
        t: Math.random(),
        speed: 0.006 + Math.random() * 0.005
      });
    }
  });
}

function startCanvasLoop() {
  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw background grid
    drawGrid();

    if (currentState && currentState.nodes) {
      const nodeMap = {};
      currentState.nodes.forEach(n => { nodeMap[n.id] = n; });

      // 1. Draw Edges
      currentState.edges.forEach(e => {
        const src = nodeMap[e.source];
        const tgt = nodeMap[e.target];
        if (src && tgt) {
          drawEdge(src, tgt, e);
        }
      });

      // 2. Draw animated flow particles
      if (animationRunning) {
        particles.forEach(p => {
          const src = nodeMap[p.edge.source];
          const tgt = nodeMap[p.edge.target];
          if (src && tgt) {
            p.t += p.speed;
            if (p.t > 1) p.t = 0;

            const px = src.x + (tgt.x - src.x) * p.t;
            const py = src.y + (tgt.y - src.y) * p.t;

            ctx.fillStyle = p.edge.async_flow ? '#f59e0b' : '#06b6d4';
            ctx.shadowColor = ctx.fillStyle;
            ctx.shadowBlur = 8;
            ctx.beginPath();
            ctx.arc(px, py, 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.shadowBlur = 0;
          }
        });
      }

      // 3. Draw Nodes
      currentState.nodes.forEach(n => {
        drawNode(n, n === selectedNode);
      });
    }

    animFrameId = requestAnimationFrame(render);
  }

  animFrameId = requestAnimationFrame(render);
}

function drawGrid() {
  ctx.strokeStyle = 'rgba(30, 41, 59, 0.4)';
  ctx.lineWidth = 1;
  const step = 40;
  for (let x = 0; x < canvas.width; x += step) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += step) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }
}

function drawEdge(src, tgt, edge) {
  ctx.strokeStyle = edge.async_flow ? 'rgba(245, 158, 11, 0.5)' : 'rgba(59, 130, 246, 0.5)';
  ctx.lineWidth = 2;
  if (edge.async_flow) {
    ctx.setLineDash([4, 4]);
  } else {
    ctx.setLineDash([]);
  }

  ctx.beginPath();
  ctx.moveTo(src.x, src.y);
  ctx.lineTo(tgt.x, tgt.y);
  ctx.stroke();
  ctx.setLineDash([]);

  // Edge label pill
  const midX = (src.x + tgt.x) / 2;
  const midY = (src.y + tgt.y) / 2;
  ctx.fillStyle = '#0f172a';
  ctx.fillRect(midX - 35, midY - 9, 70, 18);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  ctx.strokeRect(midX - 35, midY - 9, 70, 18);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '9px Fira Code';
  ctx.textAlign = 'center';
  ctx.fillText(edge.protocol || 'sync', midX, midY + 3);
}

function drawNode(node, isSelected) {
  const color = TIER_COLORS[node.tier] || '#3b82f6';
  const width = 160;
  const height = 64;
  const x = node.x - width / 2;
  const y = node.y - height / 2;
  const radius = 8;

  // Glow if selected
  if (isSelected) {
    ctx.shadowColor = color;
    ctx.shadowBlur = 16;
  }

  // Card background
  ctx.fillStyle = '#111726';
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
  ctx.fill();

  // Border
  ctx.strokeStyle = isSelected ? color : '#1e293b';
  ctx.lineWidth = isSelected ? 2 : 1;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Tier color accent bar on top
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.roundRect(x, y, width, 4, [radius, radius, 0, 0]);
  ctx.fill();

  // Tier pill
  ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.fillRect(x + 10, y + 10, 52, 14);
  ctx.fillStyle = color;
  ctx.font = '8px Fira Code';
  ctx.textAlign = 'left';
  ctx.fillText(node.tier.toUpperCase(), x + 14, y + 20);

  // Latency pill
  ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.fillRect(x + width - 48, y + 10, 38, 14);
  ctx.fillStyle = '#94a3b8';
  ctx.font = '8px Fira Code';
  ctx.textAlign = 'right';
  ctx.fillText(`${node.latency_ms}ms`, x + width - 14, y + 20);

  // Node label
  ctx.fillStyle = '#ffffff';
  ctx.font = '600 11px Plus Jakarta Sans';
  ctx.textAlign = 'left';
  const truncatedLabel = node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label;
  ctx.fillText(truncatedLabel, x + 10, y + 42);

  // State model badge
  ctx.fillStyle = '#64748b';
  ctx.font = '9px Fira Code';
  ctx.fillText(`[${node.state_type}]`, x + 10, y + 54);
}
