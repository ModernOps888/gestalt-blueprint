/**
 * GESTALT // Cognitive Topology & Socratic Blueprint Extractor
 * Client Application Logic, Multi-Role Deliverables & Interactive Canvas Engine
 */

let currentState = null;
let selectedNode = null;
let animationRunning = true;
let animFrameId = null;
let particles = [];
let latestArtifacts = null;
let activeLanguage = 'python';
let activeDevopsTab = 'compose';

// Canvas Zoom & Pan
let zoomLevel = 1.0;
let panX = 0;
let panY = 0;

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
const devopsContent = document.getElementById('devops-content');
const secopsMarkdown = document.getElementById('secops-markdown');
const qaContent = document.getElementById('qa-content');
const finopsMarkdown = document.getElementById('finops-markdown');
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

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

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
      document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active-preset'));
      chip.classList.add('active-preset');
      seedInput.value = chip.dataset.seed;
      triggerProjection(chip.dataset.seed);
    });
  });

  // Project Button
  btnProject.addEventListener('click', () => {
    const seed = seedInput.value.trim();
    if (seed) triggerProjection(seed);
  });

  // Main Deliverable Tab Switching
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const targetPane = document.getElementById(`pane-${btn.dataset.tab}`);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  // Polyglot Language Sub-tabs
  document.querySelectorAll('[data-lang]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-lang]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeLanguage = btn.dataset.lang;
      renderActiveCode();
    });
  });

  // DevOps Sub-tabs
  document.querySelectorAll('[data-devops]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-devops]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeDevopsTab = btn.dataset.devops;
      renderActiveDevops();
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

  // Canvas Zoom Controls
  document.getElementById('btn-zoom-in').addEventListener('click', () => {
    zoomLevel = Math.min(2.5, zoomLevel + 0.15);
  });
  document.getElementById('btn-zoom-out').addEventListener('click', () => {
    zoomLevel = Math.max(0.4, zoomLevel - 0.15);
  });
  document.getElementById('btn-fit').addEventListener('click', () => {
    zoomLevel = 1.0;
    panX = 0;
    panY = 0;
    if (currentState && currentState.nodes) {
      applyLayout(currentState.nodes);
    }
  });

  // Export Canvas as PNG
  document.getElementById('btn-export-png').addEventListener('click', exportCanvasImage);

  // Add Custom Node Modal
  const addNodeModal = document.getElementById('add-node-modal');
  document.getElementById('btn-add-node').addEventListener('click', () => {
    if (!currentState) {
      alert('Please project a blueprint first before adding custom nodes.');
      return;
    }
    addNodeModal.classList.remove('hidden');
  });
  document.getElementById('btn-close-node-modal').addEventListener('click', () => {
    addNodeModal.classList.add('hidden');
  });
  document.getElementById('btn-submit-add-node').addEventListener('click', submitCustomNode);

  // Copy Buttons
  btnCopyCode.addEventListener('click', () => {
    navigator.clipboard.writeText(codeContent.innerText);
    btnCopyCode.innerText = 'Copied!';
    setTimeout(() => { btnCopyCode.innerText = 'Copy Code'; }, 1500);
  });

  const btnCopyDevops = document.getElementById('btn-copy-devops');
  if (btnCopyDevops) {
    btnCopyDevops.addEventListener('click', () => {
      navigator.clipboard.writeText(devopsContent.innerText);
      btnCopyDevops.innerText = 'Copied!';
      setTimeout(() => { btnCopyDevops.innerText = 'Copy IaC'; }, 1500);
    });
  }

  const btnCopyQa = document.getElementById('btn-copy-qa');
  if (btnCopyQa) {
    btnCopyQa.addEventListener('click', () => {
      navigator.clipboard.writeText(qaContent.innerText);
      btnCopyQa.innerText = 'Copied!';
      setTimeout(() => { btnCopyQa.innerText = 'Copy Test Suite'; }, 1500);
    });
  }

  // Export to disk
  btnExportDisk.addEventListener('click', exportProject);

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
  document.getElementById('btn-settings').addEventListener('click', () => {
    modal.classList.remove('hidden');
    checkEngineStatus();
  });
  document.getElementById('btn-close-modal').addEventListener('click', () => modal.classList.add('hidden'));

  const modelSelectEl = document.getElementById('setting-model-select');
  if (modelSelectEl) {
    modelSelectEl.addEventListener('change', () => {
      document.getElementById('setting-model').value = modelSelectEl.value;
    });
  }

  const btnTestConn = document.getElementById('btn-test-connection');
  if (btnTestConn) {
    btnTestConn.addEventListener('click', async () => {
      btnTestConn.innerText = 'Checking...';
      await checkEngineStatus();
      btnTestConn.innerText = 'Checked!';
      setTimeout(() => { btnTestConn.innerText = 'Check Status'; }, 1500);
    });
  }

  document.getElementById('btn-save-settings').addEventListener('click', async () => {
    const provider = document.getElementById('setting-provider').value;
    const endpoint = document.getElementById('setting-endpoint').value;
    const selectedModel = modelSelectEl ? modelSelectEl.value : '';
    const customModel = document.getElementById('setting-model').value.trim();
    const model = customModel || selectedModel || 'llama3.2:latest';
    const apiKey = document.getElementById('setting-api-key').value;

    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, endpoint, model, api_key: apiKey || null })
      });
    } catch (e) {
      console.error('Settings save error:', e);
    }
    modal.classList.add('hidden');
    await checkEngineStatus();
  });
}

// --- CLEAR CANVAS & NEW BLUEPRINT ---
function clearCanvas() {
  currentState = null;
  selectedNode = null;
  particles = [];
  latestArtifacts = null;
  zoomLevel = 1.0;
  panX = 0;
  panY = 0;
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
  codeContent.innerText = '// Polyglot executable scaffolding will appear here...';
  devopsContent.innerText = '# Docker & Orchestration IaC will appear here...';
  secopsMarkdown.innerHTML = '<p class="empty-state">STRIDE threat matrix will render here.</p>';
  qaContent.innerText = '# Pytest test cases will appear here...';
  finopsMarkdown.innerHTML = '<p class="empty-state">Cloud run-rate & SLO contracts will render here.</p>';
  invariantsContainer.innerHTML = '<p class="empty-state">System guardrails & runtime assertions will list here.</p>';
  nodeInspector.classList.add('hidden');
}

// --- SUBMIT CUSTOM NODE ---
async function submitCustomNode() {
  if (!currentState) return;
  const id = document.getElementById('new-node-id').value.trim();
  const label = document.getElementById('new-node-label').value.trim();
  const tier = document.getElementById('new-node-tier').value;
  const state_type = document.getElementById('new-node-state').value;
  const latency_ms = parseInt(document.getElementById('new-node-latency').value) || 20;
  const description = document.getElementById('new-node-desc').value.trim();

  if (!id || !label) {
    alert('Please provide a valid Component ID and Label.');
    return;
  }

  try {
    const res = await fetch('/api/node/custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentState.session_id,
        id, label, tier, state_type, latency_ms, description
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to add node');
    }
    const updatedState = await res.json();
    document.getElementById('add-node-modal').classList.add('hidden');
    updateState(updatedState);
    await fetchDeliverables(updatedState.session_id);
  } catch (err) {
    alert('Error: ' + err.message);
  }
}

// --- EXPORT CANVAS AS PNG ---
function exportCanvasImage() {
  const link = document.createElement('a');
  link.download = `gestalt-${currentState ? currentState.session_id : 'topology'}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
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
          <div class="history-title">${escapeHtml(s.title)}</div>
          <div class="history-seed">"${escapeHtml(s.seed)}"</div>
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
    historyItemsList.innerHTML = `<p class="empty-state" style="color:var(--accent-rose);">Error: ${escapeHtml(err.message)}</p>`;
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
    const dotEl = document.querySelector('.status-dot');

    if (data.status === 'connected' && data.is_local) {
      if (dotEl) { dotEl.className = 'status-dot green'; }
      engineNameEl.innerText = `Local LLM: ${data.active_model} (${data.latency_ms}ms)`;
    } else if (data.status === 'connected' && !data.is_local) {
      if (dotEl) { dotEl.className = 'status-dot blue'; }
      engineNameEl.innerText = `Cloud LLM: ${data.active_model}`;
    } else {
      if (dotEl) { dotEl.className = 'status-dot purple'; }
      engineNameEl.innerText = 'Cognitive Heuristics (Instant)';
    }

    // Populate model select in settings modal
    const modelSelect = document.getElementById('setting-model-select');
    if (modelSelect && data.available_models && data.available_models.length > 0) {
      modelSelect.innerHTML = data.available_models.map(m =>
        `<option value="${m}" ${m === data.active_model ? 'selected' : ''}>${m} (Local)</option>`
      ).join('');
    }

    const customModelInput = document.getElementById('setting-model');
    if (customModelInput && data.active_model && !customModelInput.value) {
      customModelInput.value = data.active_model;
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
    updateHistoryCount();
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

  convergenceFill.style.width = `${state.convergence_pct}%`;
  convergenceText.innerText = `${state.convergence_pct}%`;
  blueprintTitle.innerText = state.title || 'Emergent Topology';
  nodeCountEl.innerText = `${state.nodes.length} Nodes`;
  edgeCountEl.innerText = `${state.edges.length} Edges`;
  invariantCountEl.innerText = `${state.invariants.length} Invariants`;

  applyLayout(state.nodes);
  initParticles(state);
  renderProbes(state.active_probes);
  renderDecisions(state.resolved_decisions);
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
      <div class="probe-dim">${escapeHtml(p.dimension)}</div>
      <div class="probe-question">${escapeHtml(p.question)}</div>
      <div class="probe-tension">" ${escapeHtml(p.cognitive_tension)} "</div>

      <div class="probe-options">
        ${p.options.map(opt => `
          <button class="probe-option-btn" onclick="resolveProbe('${p.id}', '${opt.id}')">
            <div class="opt-title">
              <span>${escapeHtml(opt.label)}</span>
              <span style="font-size:0.75rem; color:var(--accent-blue);">Select ➔</span>
            </div>
            <div class="opt-desc">${escapeHtml(opt.description)}</div>
            <div class="opt-tradeoff">⚡ Tradeoff: ${escapeHtml(opt.tradeoff)}</div>
          </button>
        `).join('')}
      </div>

      <div class="probe-note-wrap" style="margin-top: 10px;">
        <input type="text" id="note-${p.id}" class="form-input" style="font-size: 0.75rem; padding: 6px 10px; background: rgba(15, 23, 42, 0.6);" placeholder="Optional custom note/constraint (e.g. 'must support sub-zero permafrost')...">
      </div>
    </div>
  `).join('');
}

// --- RESOLVE PROBE STEP ---
window.resolveProbe = async function(probeId, optionId) {
  if (!currentState) return;

  const noteInput = document.getElementById(`note-${probeId}`);
  const customNote = noteInput ? noteInput.value.trim() : null;

  try {
    const res = await fetch('/api/probe/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentState.session_id,
        probe_id: probeId,
        option_id: optionId,
        custom_note: customNote || null
      })
    });

    if (!res.ok) throw new Error('Failed to resolve probe');
    const updatedState = await res.json();
    updateState(updatedState);
    await fetchDeliverables(updatedState.session_id);
    updateHistoryCount();
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
      <strong>${escapeHtml(d.probe_dimension)}:</strong> ${escapeHtml(d.chosen_label)}
      <div style="font-size:0.65rem; color:var(--text-muted);">${escapeHtml(d.tradeoff)}</div>
    </div>
  `).join('');
}

// --- RENDER INVARIANTS ---
function renderInvariants(invariants) {
  if (!invariants || invariants.length === 0) {
    invariantsContainer.innerHTML = `<p class="empty-state">No invariants declared.</p>`;
    return;
  }

  invariantsContainer.innerHTML = invariants.map((inv) => `
    <div style="background:var(--bg-card); border:1px solid var(--border-subtle); padding:10px; border-radius:6px; margin-bottom:8px; border-left:3px solid var(--accent-rose);">
      <div style="display:flex; justify-content:space-between; font-size:0.68rem; font-family:var(--font-mono); color:var(--accent-cyan);">
        <span>[${escapeHtml(inv.category.toUpperCase())}]</span>
        <span style="color:var(--accent-rose);">${escapeHtml(inv.severity.toUpperCase())}</span>
      </div>
      <div style="font-size:0.78rem; font-weight:600; margin-top:4px;">${escapeHtml(inv.statement)}</div>
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
    latestArtifacts = data.artifacts;

    // 1. Architect ADR
    adrMarkdown.innerHTML = renderMarkdownSimple(latestArtifacts.adr_markdown);

    // 2. Polyglot Code
    renderActiveCode();

    // 3. DevOps IaC
    renderActiveDevops();

    // 4. SecOps STRIDE
    secopsMarkdown.innerHTML = renderMarkdownSimple(latestArtifacts.secops_stride);

    // 5. QA Test Suite
    qaContent.innerText = latestArtifacts.qa_tests || '# QA Tests';

    // 6. FinOps & SLO
    finopsMarkdown.innerHTML = renderMarkdownSimple(latestArtifacts.finops_slo);

  } catch (err) {
    console.error('Failed to fetch deliverables:', err);
  }
}

function renderActiveCode() {
  if (!latestArtifacts) return;
  if (activeLanguage === 'python') {
    codeContent.innerText = latestArtifacts.code_scaffold?.['main.py'] || '# Python code';
  } else if (activeLanguage === 'typescript') {
    codeContent.innerText = latestArtifacts.typescript_scaffold?.['index.ts'] || '// TypeScript code';
  } else if (activeLanguage === 'go') {
    codeContent.innerText = latestArtifacts.go_scaffold?.['main.go'] || '// Go code';
  }
}

function renderActiveDevops() {
  if (!latestArtifacts || !latestArtifacts.devops_iac) return;
  if (activeDevopsTab === 'compose') {
    devopsContent.innerText = latestArtifacts.devops_iac['docker-compose.yml'] || '# Docker compose';
  } else if (activeDevopsTab === 'dockerfile') {
    devopsContent.innerText = latestArtifacts.devops_iac['Dockerfile'] || '# Dockerfile';
  }
}

// Markdown formatter with table rendering
function renderMarkdownSimple(md) {
  if (!md) return '';
  
  // Format tables
  let processed = md.replace(/\|(.+)\|/gim, (match) => {
    const cells = match.split('|').filter(c => c.trim().length > 0);
    if (match.includes(':---')) return '';
    const isHeader = match.includes('Component ID') || match.includes('Threat Category') || match.includes('Resource Dimension');
    const tag = isHeader ? 'th' : 'td';
    return '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
  });

  processed = processed
    .replace(/^# (.*$)/gim, '<h2 style="font-size:1.1rem; color:#fff; margin-top:8px;">$1</h2>')
    .replace(/^## (.*$)/gim, '<h3 style="font-size:0.95rem; color:var(--accent-blue); margin-top:14px;">$1</h3>')
    .replace(/^### (.*$)/gim, '<h4 style="font-size:0.85rem; color:#fff; margin-top:10px;">$1</h4>')
    .replace(/^> (.*$)/gim, '<blockquote style="border-left:2px solid var(--accent-emerald); padding-left:8px; color:var(--text-muted); font-size:0.75rem; margin:6px 0;">$1</blockquote>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code style="background:var(--bg-card); padding:2px 4px; border-radius:3px; font-family:var(--font-mono); font-size:0.72rem; color:var(--accent-cyan);">$1</code>')
    .replace(/\n\n/gim, '<br/><br/>');

  return processed;
}

// --- EXPORT TO LOCAL DISK ---
async function exportProject() {
  if (!currentState) {
    alert('Please project a blueprint first!');
    return;
  }

  btnExportDisk.disabled = true;
  btnExportDisk.innerText = 'Exporting All Deliverables to Disk...';

  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentState.session_id })
    });
    const result = await res.json();
    alert(`✓ Full IT Deliverables Successfully Exported!\n\nPath: ${result.exported_path}\nFiles:\n• ${result.files.join('\n• ')}\n\nIncludes Python, TypeScript, Go, Docker, STRIDE Threat Model, Pytest Suite, and FinOps SLA contracts!`);
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
      Export All IT Deliverables to Disk
    `;
  }
}

// --- CANVAS & TOPOLOGY GRAPH ENGINE (With Zoom & Pan) ---
function initCanvas() {
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  let draggingNode = null;
  let dragOffset = { x: 0, y: 0 };
  let isPanning = false;
  let panStart = { x: 0, y: 0 };

  // Mouse wheel zoom
  viewport.addEventListener('wheel', (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    zoomLevel = Math.max(0.35, Math.min(2.5, zoomLevel * zoomFactor));
  }, { passive: false });

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = (e.clientX - rect.left - panX) / zoomLevel;
    const mouseY = (e.clientY - rect.top - panY) / zoomLevel;

    if (!currentState || !currentState.nodes) return;

    let clickedNode = null;
    for (let n of currentState.nodes) {
      const dx = mouseX - n.x;
      const dy = mouseY - n.y;
      if (Math.sqrt(dx * dx + dy * dy) < 45) {
        clickedNode = n;
        break;
      }
    }

    if (clickedNode) {
      draggingNode = clickedNode;
      dragOffset = { x: mouseX - clickedNode.x, y: mouseY - clickedNode.y };
      selectNode(clickedNode);
    } else {
      isPanning = true;
      panStart = { x: e.clientX - panX, y: e.clientY - panY };
    }
  });

  window.addEventListener('mousemove', (e) => {
    if (draggingNode) {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - panX) / zoomLevel;
      const mouseY = (e.clientY - rect.top - panY) / zoomLevel;
      draggingNode.x = mouseX - dragOffset.x;
      draggingNode.y = mouseY - dragOffset.y;
    } else if (isPanning) {
      panX = e.clientX - panStart.x;
      panY = e.clientY - panStart.y;
    }
  });

  window.addEventListener('mouseup', () => {
    draggingNode = null;
    isPanning = false;
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

    ctx.save();
    ctx.translate(panX, panY);
    ctx.scale(zoomLevel, zoomLevel);

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

    ctx.restore();
    animFrameId = requestAnimationFrame(render);
  }

  animFrameId = requestAnimationFrame(render);
}

function drawGrid() {
  ctx.strokeStyle = 'rgba(30, 41, 59, 0.4)';
  ctx.lineWidth = 1;
  const step = 40;
  const W = (canvas.width / zoomLevel) * 2;
  const H = (canvas.height / zoomLevel) * 2;

  for (let x = -W; x < W * 2; x += step) {
    ctx.beginPath();
    ctx.moveTo(x, -H);
    ctx.lineTo(x, H * 2);
    ctx.stroke();
  }
  for (let y = -H; y < H * 2; y += step) {
    ctx.beginPath();
    ctx.moveTo(-W, y);
    ctx.lineTo(W * 2, y);
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

  if (isSelected) {
    ctx.shadowColor = color;
    ctx.shadowBlur = 16;
  }

  ctx.fillStyle = '#111726';
  ctx.beginPath();
  ctx.roundRect(x, y, width, height, radius);
  ctx.fill();

  ctx.strokeStyle = isSelected ? color : '#1e293b';
  ctx.lineWidth = isSelected ? 2 : 1;
  ctx.stroke();
  ctx.shadowBlur = 0;

  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.roundRect(x, y, width, 4, [radius, radius, 0, 0]);
  ctx.fill();

  ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.fillRect(x + 10, y + 10, 52, 14);
  ctx.fillStyle = color;
  ctx.font = '8px Fira Code';
  ctx.textAlign = 'left';
  ctx.fillText(node.tier.toUpperCase(), x + 14, y + 20);

  ctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.fillRect(x + width - 48, y + 10, 38, 14);
  ctx.fillStyle = '#94a3b8';
  ctx.font = '8px Fira Code';
  ctx.textAlign = 'right';
  ctx.fillText(`${node.latency_ms}ms`, x + width - 14, y + 20);

  ctx.fillStyle = '#ffffff';
  ctx.font = '600 11px Plus Jakarta Sans';
  ctx.textAlign = 'left';
  const truncatedLabel = node.label.length > 20 ? node.label.slice(0, 18) + '...' : node.label;
  ctx.fillText(truncatedLabel, x + 10, y + 42);

  ctx.fillStyle = '#64748b';
  ctx.font = '9px Fira Code';
  ctx.fillText(`[${node.state_type}]`, x + 10, y + 54);
}
