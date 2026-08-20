"""
HTML dashboard template for Fire Safety Regulations Version Comparison UI.
Supports multi-version comparison (v1 vs v2, v2 vs v3, v1 vs v3) and token-level LCS diff highlighting.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fire Safety Regulations — Multi-Version Comparison Engine</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #090D16;
      --card-bg: rgba(17, 24, 39, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --text-main: #F3F4F6;
      --text-muted: #9CA3AF;
      --accent-indigo: #6366F1;
      --accent-purple: #8B5CF6;
      --modified-color: #F59E0B;
      --modified-bg: rgba(245, 158, 11, 0.15);
      --added-color: #10B981;
      --added-bg: rgba(16, 185, 129, 0.15);
      --removed-color: #EF4444;
      --removed-bg: rgba(239, 68, 68, 0.15);
      --unchanged-color: #6B7280;
      --unchanged-bg: rgba(107, 114, 128, 0.15);
      --radius-lg: 16px;
      --radius-md: 10px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      min-height: 100vh;
      line-height: 1.5;
      background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.1) 0px, transparent 50%);
    }

    header {
      padding: 1.5rem 2rem;
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(9, 13, 22, 0.8);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--accent-indigo), var(--accent-purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.2rem;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
    }
    .brand-title {
      font-size: 1.2rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      background: linear-gradient(to right, #FFFFFF, #9CA3AF);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .badge-stage {
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 600;
      background: rgba(139, 92, 246, 0.2);
      color: #C084FC;
      border: 1px solid rgba(192, 132, 252, 0.3);
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 2rem;
    }

    /* Preset Comparison Shortcuts */
    .presets-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 1rem;
    }
    .preset-label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .preset-btn {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: var(--text-main);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 0.82rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }
    .preset-btn:hover {
      background: rgba(99, 102, 241, 0.2);
      border-color: rgba(99, 102, 241, 0.4);
      color: #FFF;
    }

    /* Controls Panel */
    .controls-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius-lg);
      padding: 1.5rem;
      backdrop-filter: blur(16px);
      margin-bottom: 2rem;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
      align-items: end;
    }

    .control-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .control-group label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    select, input {
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: var(--radius-md);
      color: var(--text-main);
      padding: 10px 14px;
      font-family: inherit;
      font-size: 0.9rem;
      outline: none;
      transition: all 0.2s;
    }
    select:focus, input:focus {
      border-color: var(--accent-indigo);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
    }

    /* Summary Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius-md);
      padding: 1.2rem;
      backdrop-filter: blur(12px);
      position: relative;
      overflow: hidden;
    }
    .stat-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 3px;
    }
    .stat-card.total::before { background: var(--accent-indigo); }
    .stat-card.modified::before { background: var(--modified-color); }
    .stat-card.added::before { background: var(--added-color); }
    .stat-card.removed::before { background: var(--removed-color); }
    .stat-card.unchanged::before { background: var(--unchanged-color); }

    .stat-label {
      font-size: 0.8rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .stat-value {
      font-size: 1.8rem;
      font-weight: 700;
      margin-top: 4px;
    }

    /* Filter Tabs & Search Bar */
    .filter-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }
    .filter-tabs {
      display: flex;
      gap: 6px;
      background: rgba(15, 23, 42, 0.6);
      padding: 4px;
      border-radius: 12px;
      border: 1px solid var(--card-border);
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-btn:hover { color: var(--text-main); }
    .tab-btn.active {
      background: var(--accent-indigo);
      color: #FFF;
      box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
    }

    .search-box {
      width: 280px;
    }

    /* Results List & Cards */
    .results-list {
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .clause-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: var(--radius-lg);
      padding: 1.5rem;
      backdrop-filter: blur(16px);
      transition: border-color 0.2s;
    }
    .clause-card:hover {
      border-color: rgba(99, 102, 241, 0.3);
    }
    .clause-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1rem;
      padding-bottom: 0.8rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .clause-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .clause-tag {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 1.1rem;
      background: rgba(255, 255, 255, 0.08);
      padding: 4px 10px;
      border-radius: 8px;
    }
    .section-title {
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    .badges-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .badge {
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .badge.modified { background: var(--modified-bg); color: var(--modified-color); border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge.added { background: var(--added-bg); color: var(--added-color); border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge.removed { background: var(--removed-bg); color: var(--removed-color); border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge.unchanged { background: var(--unchanged-bg); color: var(--unchanged-color); border: 1px solid rgba(107, 114, 128, 0.3); }

    .badge-sim {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 4px 8px;
      border-radius: 6px;
      color: #E2E8F0;
    }

    /* Side by Side Diff Grid */
    .diff-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    @media (max-width: 768px) {
      .diff-grid { grid-template-columns: 1fr; }
    }
    .diff-pane {
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: var(--radius-md);
      padding: 1rem;
      font-size: 0.9rem;
      color: #D1D5DB;
    }
    .diff-pane-header {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 8px;
      letter-spacing: 0.05em;
    }

    mark.del {
      background: rgba(239, 68, 68, 0.35);
      color: #FCA5A5;
      padding: 2px 4px;
      border-radius: 4px;
      text-decoration: line-through;
    }
    mark.add {
      background: rgba(16, 185, 129, 0.35);
      color: #6EE7B7;
      padding: 2px 4px;
      border-radius: 4px;
      font-weight: 600;
    }

    .empty-state {
      text-align: center;
      padding: 4rem;
      color: var(--text-muted);
      background: var(--card-bg);
      border-radius: var(--radius-lg);
      border: 1px solid var(--card-border);
    }
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-icon">ADB</div>
      <div>
        <div class="brand-title">Approved Document B — Multi-Version Comparison Engine</div>
      </div>
    </div>
    <div class="badge-stage">Stage 3 Semantic (SBERT + difflib)</div>
  </header>

  <div class="container">
    
    <!-- Presets Bar -->
    <div class="presets-bar">
      <span class="preset-label">Comparison Presets:</span>
      <button class="preset-btn" onclick="setPreset(1, 2)">2019 vs 2020 Amendments (v1 → v2)</button>
      <button class="preset-btn" onclick="setPreset(2, 3)">2020 vs 2022 Amendments (v2 → v3)</button>
      <button class="preset-btn" onclick="setPreset(1, 3)">2019 vs 2022 Full Evolution (v1 → v3)</button>
    </div>

    <!-- Controls Panel -->
    <div class="controls-panel">
      <div class="control-group">
        <label>Regulation Document</label>
        <select id="select-doc"></select>
      </div>
      <div class="control-group">
        <label>Version A (Base)</label>
        <select id="select-v1"></select>
      </div>
      <div class="control-group">
        <label>Version B (Comparison)</label>
        <select id="select-v2"></select>
      </div>
      <div class="control-group">
        <label>NLP Model Pipeline</label>
        <select id="select-method">
          <option value="sbert" selected>Stage 3: Sentence-BERT (all-MiniLM-L6-v2)</option>
          <option value="baseline">Baseline: difflib + TF-IDF</option>
        </select>
      </div>
    </div>

    <!-- Summary Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card total">
        <div class="stat-label">Total Clauses Evaluated</div>
        <div class="stat-value" id="stat-total">0</div>
      </div>
      <div class="stat-card modified">
        <div class="stat-label">Modified Clauses</div>
        <div class="stat-value" id="stat-modified">0</div>
      </div>
      <div class="stat-card added">
        <div class="stat-label">Added Clauses</div>
        <div class="stat-value" id="stat-added">0</div>
      </div>
      <div class="stat-card removed">
        <div class="stat-label">Removed Clauses</div>
        <div class="stat-value" id="stat-removed">0</div>
      </div>
      <div class="stat-card unchanged">
        <div class="stat-label">Unchanged Clauses</div>
        <div class="stat-value" id="stat-unchanged">0</div>
      </div>
    </div>

    <!-- Filter & Search Bar -->
    <div class="filter-bar">
      <div class="filter-tabs">
        <button class="tab-btn active" data-filter="all">All</button>
        <button class="tab-btn" data-filter="modified">Modified</button>
        <button class="tab-btn" data-filter="added">Added</button>
        <button class="tab-btn" data-filter="removed">Removed</button>
        <button class="tab-btn" data-filter="unchanged">Unchanged</button>
      </div>
      <input type="text" id="search-input" class="search-box" placeholder="Search clause (e.g. 11.5, 7.4)...">
    </div>

    <!-- Results List -->
    <div id="results-list" class="results-list">
      <div class="empty-state">Loading clause comparison data...</div>
    </div>

  </div>

  <script>
    let currentData = null;
    let activeFilter = 'all';

    async function init() {
      try {
        const resDocs = await fetch('/documents');
        const docs = await resDocs.json();
        const docSelect = document.getElementById('select-doc');
        docSelect.innerHTML = docs.map(d => `<option value="${d.id}">${d.title}</option>`).join('');

        if (docs.length > 0) {
          await loadVersions(docs[0].id);
        }
      } catch (err) {
        console.error("Init failed:", err);
      }
    }

    async function loadVersions(docId) {
      const resV = await fetch(`/documents/${docId}/versions`);
      const versions = await resV.json();
      const v1Select = document.getElementById('select-v1');
      const v2Select = document.getElementById('select-v2');

      v1Select.innerHTML = versions.map(v => `<option value="${v.id}">${v.label} (v${v.id})</option>`).join('');
      v2Select.innerHTML = versions.map(v => `<option value="${v.id}">${v.label} (v${v.id})</option>`).join('');

      if (versions.length >= 2) {
        v1Select.value = versions[0].id;
        v2Select.value = versions[1].id;
      }
      runComparison();
    }

    function setPreset(v1Id, v2Id) {
      document.getElementById('select-v1').value = v1Id;
      document.getElementById('select-v2').value = v2Id;
      runComparison();
    }

    async function runComparison() {
      const v1 = document.getElementById('select-v1').value;
      const v2 = document.getElementById('select-v2').value;
      const method = document.getElementById('select-method').value;

      if (!v1 || !v2) return;

      const container = document.getElementById('results-list');
      container.innerHTML = '<div class="empty-state">Executing comparison pipeline...</div>';

      try {
        const res = await fetch(`/compare/${v1}/${v2}?method=${method}`);
        currentData = await res.json();
        updateStats();
        renderResults();
      } catch (err) {
        container.innerHTML = `<div class="empty-state">Error running comparison: ${err.message}</div>`;
      }
    }

    function updateStats() {
      if (!currentData || !currentData.summary) return;
      const s = currentData.summary;
      const total = (s.unchanged || 0) + (s.modified || 0) + (s.added || 0) + (s.removed || 0);
      
      document.getElementById('stat-total').innerText = total;
      document.getElementById('stat-modified').innerText = s.modified || 0;
      document.getElementById('stat-added').innerText = s.added || 0;
      document.getElementById('stat-removed').innerText = s.removed || 0;
      document.getElementById('stat-unchanged').innerText = s.unchanged || 0;
    }

    // Token-level LCS Diff Algorithm
    function tokenize(text) {
      if (!text) return [];
      return text.match(/\\w+|[^\\w\\s]|\\s+/g) || [];
    }

    function computeLCS(oldTokens, newTokens) {
      const m = oldTokens.length;
      const n = newTokens.length;
      
      // DP Table
      const dp = Array.from({ length: m + 1 }, () => new Int32Array(n + 1));
      
      for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
          if (oldTokens[i - 1] === newTokens[j - 1]) {
            dp[i][j] = dp[i - 1][j - 1] + 1;
          } else {
            dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
          }
        }
      }

      // Backtrack
      let i = m, j = n;
      const inLcsOld = new Uint8Array(m);
      const inLcsNew = new Uint8Array(n);

      while (i > 0 && j > 0) {
        if (oldTokens[i - 1] === newTokens[j - 1]) {
          inLcsOld[i - 1] = 1;
          inLcsNew[j - 1] = 1;
          i--;
          j--;
        } else if (dp[i - 1][j] >= dp[i][j - 1]) {
          i--;
        } else {
          j--;
        }
      }

      return { inLcsOld, inLcsNew };
    }

    function highlightDiff(oldText, newText) {
      if (!oldText || !newText) return { oldHtml: oldText || '', newHtml: newText || '' };

      const oldTokens = tokenize(oldText);
      const newTokens = tokenize(newText);
      const { inLcsOld, inLcsNew } = computeLCS(oldTokens, newTokens);

      let oldHtml = '';
      let newHtml = '';

      let inDel = false;
      for (let i = 0; i < oldTokens.length; i++) {
        const token = oldTokens[i];
        const isMatch = inLcsOld[i] === 1;

        if (!isMatch) {
          if (!inDel) { oldHtml += '<mark class="del">'; inDel = true; }
          oldHtml += escapeHtml(token);
        } else {
          if (inDel) { oldHtml += '</mark>'; inDel = false; }
          oldHtml += escapeHtml(token);
        }
      }
      if (inDel) oldHtml += '</mark>';

      let inAdd = false;
      for (let j = 0; j < newTokens.length; j++) {
        const token = newTokens[j];
        const isMatch = inLcsNew[j] === 1;

        if (!isMatch) {
          if (!inAdd) { newHtml += '<mark class="add">'; inAdd = true; }
          newHtml += escapeHtml(token);
        } else {
          if (inAdd) { newHtml += '</mark>'; inAdd = false; }
          newHtml += escapeHtml(token);
        }
      }
      if (inAdd) newHtml += '</mark>';

      return { oldHtml, newHtml };
    }

    function escapeHtml(str) {
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function renderResults() {
      const container = document.getElementById('results-list');
      const searchTerm = document.getElementById('search-input').value.toLowerCase().trim();

      if (!currentData || !currentData.changes) {
        container.innerHTML = '<div class="empty-state">No comparison data available.</div>';
        return;
      }

      let warningHtml = '';
      if (currentData.warning) {
        warningHtml = `<div style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #FBBF24; padding: 12px 16px; border-radius: 10px; margin-bottom: 1rem; font-size: 0.9rem;"><strong>⚠️ System Notice:</strong> ${escapeHtml(currentData.warning)}</div>`;
      }

      let filtered = currentData.changes.filter(r => {
        if (activeFilter !== 'all' && r.change_type !== activeFilter) return false;
        if (searchTerm) {
          const clauseNum = (r.old_clause_number || r.new_clause_number || '').toLowerCase();
          const text = ((r.old_text || '') + (r.new_text || '')).toLowerCase();
          return clauseNum.includes(searchTerm) || text.includes(searchTerm);
        }
        return true;
      });

      if (filtered.length === 0) {
        container.innerHTML = warningHtml + '<div class="empty-state">No matching clauses found for current filter.</div>';
        return;
      }

      container.innerHTML = warningHtml + filtered.map(r => {
        const num = r.old_clause_number || r.new_clause_number || 'N/A';
        const simPct = (r.similarity * 100).toFixed(1) + '%';
        const { oldHtml, newHtml } = highlightDiff(r.old_text, r.new_text);

        return `
          <div class="clause-card">
            <div class="clause-header">
              <div class="clause-info">
                <div class="clause-tag">Clause ${num}</div>
                <div class="section-title">Method: <code>${r.method}</code></div>
              </div>
              <div class="badges-group">
                <div class="badge-sim">Sim: ${simPct}</div>
                <div class="badge ${r.change_type}">${r.change_type}</div>
              </div>
            </div>
            <div class="diff-grid">
              <div class="diff-pane">
                <div class="diff-pane-header">Version A (Base)</div>
                <div>${oldHtml || '<em>Clause not present in Version A</em>'}</div>
              </div>
              <div class="diff-pane">
                <div class="diff-pane-header">Version B (Comparison)</div>
                <div>${newHtml || '<em>Clause not present in Version B</em>'}</div>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Event Listeners
    document.getElementById('select-doc').addEventListener('change', e => loadVersions(e.target.value));
    document.getElementById('select-v1').addEventListener('change', runComparison);
    document.getElementById('select-v2').addEventListener('change', runComparison);
    document.getElementById('select-method').addEventListener('change', runComparison);
    document.getElementById('search-input').addEventListener('input', renderResults);

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        renderResults();
      });
    });

    init();
  </script>
</body>
</html>
"""
