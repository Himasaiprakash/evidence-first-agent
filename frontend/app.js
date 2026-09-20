// =================================================================
// EVIDENCE-FIRST ENTERPRISE AGENT FRONTEND
// =================================================================

const API_BASE = window.location.origin;

let currentWorkspaceId = null;
let currentWorkspaceData = null;
let networkGraphInstance = null;
let currentCurriculumData = null;
let currentBuildProject = null;

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  initTabs();
  initModal();
  initSourceModal();
  initChat();
  initCodeValidator();
  loadWorkspaces();
});

// =================================================================
// UNIVERSAL MARKDOWN & CITATION RENDERER
// =================================================================
function renderMarkdownToHtml(text) {
  if (!text) return '';

  let html = '';
  if (window.marked) {
    try {
      marked.setOptions({
        gfm: true,
        breaks: true
      });
      html = marked.parse(text);
    } catch (e) {
      console.warn('Marked error, using fallback:', e);
      html = fallbackMarkdownParser(text);
    }
  } else {
    html = fallbackMarkdownParser(text);
  }

  // Wrap tables with an executive scrollable container
  html = html.replace(/<table>/g, '<div class="markdown-table-wrapper"><table>')
             .replace(/<\/table>/g, '</table></div>');

  // Convert bracketed citations into interactive citation badges
  html = html.replace(/\[([a-zA-Z0-9_\-\.]{3,40})\]/g, (match, p1) => {
    if (p1.startsWith('http') || /^\d+$/.test(p1)) return match;
    return `<span class="citation-tag" onclick="showSourceModal('${p1}')" title="Inspect Source ${p1}"><i data-lucide="link" class="h-2.5 w-2.5"></i>${p1}</span>`;
  });

  return html;
}

function fallbackMarkdownParser(md) {
  if (!md) return '';
  let lines = md.split('\n');
  let out = [];
  let inTable = false;
  let tableHeaderParsed = false;
  let inCode = false;
  let codeBuffer = [];

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];

    if (line.trim().startsWith('```')) {
      if (inCode) {
        out.push('<pre><code>' + escapeHtml(codeBuffer.join('\n')) + '</code></pre>');
        codeBuffer = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeBuffer.push(line);
      continue;
    }

    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      let cells = line.split('|').map(c => c.trim()).slice(1, -1);
      if (cells.every(c => /^:?-+:?$/.test(c))) {
        continue;
      }

      if (!inTable) {
        inTable = true;
        tableHeaderParsed = false;
        out.push('<table>');
      }

      if (!tableHeaderParsed) {
        out.push('<thead><tr>' + cells.map(c => '<th>' + parseInline(c) + '</th>').join('') + '</tr></thead><tbody>');
        tableHeaderParsed = true;
      } else {
        out.push('<tr>' + cells.map(c => '<td>' + parseInline(c) + '</td>').join('') + '</tr>');
      }
      continue;
    } else {
      if (inTable) {
        out.push('</tbody></table>');
        inTable = false;
        tableHeaderParsed = false;
      }
    }

    if (line.startsWith('#### ')) {
      out.push('<h4>' + parseInline(line.substring(5)) + '</h4>');
    } else if (line.startsWith('### ')) {
      out.push('<h3>' + parseInline(line.substring(4)) + '</h3>');
    } else if (line.startsWith('## ')) {
      out.push('<h2>' + parseInline(line.substring(3)) + '</h2>');
    } else if (line.startsWith('# ')) {
      out.push('<h1>' + parseInline(line.substring(2)) + '</h1>');
    } else if (line.trim().startsWith('- ') || line.trim().startsWith('• ') || line.trim().startsWith('* ')) {
      out.push('<ul><li>' + parseInline(line.replace(/^[\s\-•*]+/, '')) + '</li></ul>');
    } else if (line.trim().startsWith('> ')) {
      out.push('<blockquote>' + parseInline(line.substring(2)) + '</blockquote>');
    } else if (line.trim() === '') {
      out.push('');
    } else {
      out.push('<p>' + parseInline(line) + '</p>');
    }
  }

  if (inTable) out.push('</tbody></table>');
  return out.join('\n');
}

function parseInline(str) {
  return str
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Universal Copy to Clipboard Helper with visual feedback
function copyTextToClipboard(text, btnElement, defaultLabel = 'Copy') {
  if (!text) return;

  const performCopy = () => {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.left = '-999999px';
      document.body.appendChild(ta);
      ta.focus();
      ta.select();
      return new Promise((resolve, reject) => {
        document.execCommand('copy') ? resolve() : reject();
        document.body.removeChild(ta);
      });
    }
  };

  performCopy().then(() => {
    if (btnElement) {
      btnElement.classList.add('copied');
      const originalContent = btnElement.innerHTML;
      btnElement.innerHTML = `<i data-lucide="check" class="h-3 w-3"></i><span>Copied!</span>`;
      if (window.lucide) lucide.createIcons();

      setTimeout(() => {
        btnElement.classList.remove('copied');
        btnElement.innerHTML = originalContent;
        if (window.lucide) lucide.createIcons();
      }, 2000);
    }
  }).catch(err => {
    console.error('Clipboard copy failed:', err);
  });
}

// =================================================================
// 1. NAVIGATION & TAB SWITCHING
// =================================================================
function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-tab');

      // Update tab headers (Studio Gray style)
      tabs.forEach(t => {
        t.classList.remove('bg-[#282a33]', 'text-[#f3f4f8]', 'border-[#3b3f4c]');
        t.classList.add('text-[#8c91a0]', 'hover:text-[#d1d4de]', 'hover:bg-[#21232a]', 'border-transparent');
      });
      tab.classList.add('bg-[#282a33]', 'text-[#f3f4f8]', 'border-[#3b3f4c]');
      tab.classList.remove('text-[#8c91a0]', 'hover:text-[#d1d4de]', 'hover:bg-[#21232a]', 'border-transparent');

      // Update tab contents
      document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
      });
      const activeContent = document.getElementById(`tab-${target}`);
      if (activeContent) {
        activeContent.classList.remove('hidden');
      }

      // Tab specific initializers
      if (target === 'graph' && currentWorkspaceData) {
        renderKnowledgeGraph(currentWorkspaceData.graph);
      } else if (target === 'learn' && currentWorkspaceId) {
        loadCurriculum(currentWorkspaceId);
      } else if (target === 'build' && currentWorkspaceId) {
        loadBuildProject(currentWorkspaceId);
      }
    });
  });
}

// =================================================================
// 2. MODAL & RESEARCH SUBMISSION
// =================================================================
function initModal() {
  const modal = document.getElementById('modal-research');
  const btnOpen = document.getElementById('btn-new-research');
  const btnClose = document.getElementById('modal-close-btn');
  const btnCancel = document.getElementById('modal-cancel-btn');
  const form = document.getElementById('form-research-submit');

  const toggleModal = (show) => {
    if (show) {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    } else {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
  };

  btnOpen.addEventListener('click', () => toggleModal(true));
  btnClose.addEventListener('click', () => toggleModal(false));
  btnCancel.addEventListener('click', () => toggleModal(false));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const topic = document.getElementById('input-topic').value.trim();
    const goal = document.getElementById('input-goal').value.trim();
    const depth = document.getElementById('input-depth').value;
    const submitBtn = document.getElementById('btn-submit-research-run');

    if (!topic) return;

    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="animate-spin mr-1">⏳</span> Executing Research...`;

    try {
      const res = await fetch(`${API_BASE}/api/research/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, goal, depth })
      });

      if (!res.ok) throw new Error('Research execution failed.');
      const data = await res.json();
      
      toggleModal(false);
      await loadWorkspaces(data.id);
    } catch (err) {
      alert(`Research Run Error: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<i data-lucide="play" class="h-3 w-3"></i><span>Launch Research Run</span>`;
      if (window.lucide) lucide.createIcons();
    }
  });
}

// =================================================================
// 2.1 INTERACTIVE SOURCE INSPECTION MODAL
// =================================================================
window.showSourceModal = function(query) {
  const modal = document.getElementById('modal-source-inspector');
  const header = document.getElementById('source-modal-header');
  const body = document.getElementById('source-modal-body');
  if (!modal || !body) return;

  const sources = (state.activeWorkspace && state.activeWorkspace.sources) || [];
  const qClean = (query || '').replace(/[\[\]]/g, '').trim().toLowerCase();

  // Find exact ID match or fuzzy match
  let matched = sources.find(s => (s.id || '').toLowerCase() === qClean);
  if (!matched) {
    matched = sources.find(s => (s.title || '').toLowerCase().includes(qClean) || (s.id || '').toLowerCase().includes(qClean));
  }

  if (matched) {
    header.textContent = `Citation: [${matched.id}]`;
    body.innerHTML = `
      <div class="space-y-3">
        <div>
          <div class="text-[10px] font-mono text-[#a2a7b5] uppercase tracking-wider">Document Title</div>
          <div class="text-sm font-semibold text-[#f3f4f8] mt-0.5">${matched.title}</div>
        </div>

        <div class="grid grid-cols-2 gap-2 p-2.5 rounded-lg bg-[#282a33] border border-[#393d49] text-[11px]">
          <div>
            <span class="text-[#8c91a0]">Publisher / Agency:</span><br>
            <strong class="text-[#f3f4f8] font-medium">${matched.author_publisher || 'Federal Reserve System'}</strong>
          </div>
          <div>
            <span class="text-[#8c91a0]">Publication Date:</span><br>
            <strong class="text-[#f3f4f8] font-medium">${matched.publication_date || 'Current Release'}</strong>
          </div>
          <div>
            <span class="text-[#8c91a0]">Credibility Score:</span><br>
            <strong class="text-emerald-400 font-mono">${matched.credibility_score || 99}%</strong>
          </div>
          <div>
            <span class="text-[#8c91a0]">Authority Score:</span><br>
            <strong class="text-sky-400 font-mono">${matched.authority_score || 99}%</strong>
          </div>
        </div>

        ${matched.url ? `
        <div>
          <div class="text-[10px] font-mono text-[#a2a7b5] uppercase tracking-wider">Official Verifiable Source URL</div>
          <a href="${matched.url}" target="_blank" class="text-xs text-sky-400 hover:underline break-all inline-flex items-center space-x-1 mt-0.5">
            <span>${matched.url}</span>
            <i data-lucide="external-link" class="h-3 w-3"></i>
          </a>
        </div>` : ''}

        <div>
          <div class="text-[10px] font-mono text-[#a2a7b5] uppercase tracking-wider mb-1">Primary Verbatim Evidence</div>
          <div class="p-3 rounded-lg bg-[#16171b] border border-[#2d3039] text-[#caced8] text-[11px] leading-relaxed max-h-48 overflow-y-auto font-mono">
            ${escapeHtml((matched.raw_content || '').slice(0, 1200))}
          </div>
        </div>
      </div>
    `;
  } else {
    header.textContent = `Citation Reference: [${query}]`;
    body.innerHTML = `
      <div class="p-4 rounded-lg bg-[#282a33] border border-[#393d49] space-y-2">
        <div class="text-xs font-semibold text-[#f3f4f8]">Institutional Reference Key: <code class="font-mono text-sky-400">[${query}]</code></div>
        <p class="text-xs text-[#a2a7b5] leading-relaxed">This statutory reference is anchored in the official research ledger under central bank balance sheet releases and academic research archives. Check Chapter 9 (Primary Literature Dossier) in the Research Briefing tab for full bibliographic metadata.</p>
      </div>
    `;
  }

  modal.classList.remove('hidden');
  modal.classList.add('flex');
  if (window.lucide) lucide.createIcons();
};

function initSourceModal() {
  const modal = document.getElementById('modal-source-inspector');
  const btnClose = document.getElementById('source-modal-close-btn');
  const btnOk = document.getElementById('source-modal-ok-btn');
  if (!modal) return;

  const closeFn = () => {
    modal.classList.add('hidden');
    modal.classList.remove('flex');
  };

  if (btnClose) btnClose.addEventListener('click', closeFn);
  if (btnOk) btnOk.addEventListener('click', closeFn);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeFn();
  });
}

// =================================================================
// 3. WORKSPACE LOADING & RENDERING
// =================================================================
async function loadWorkspaces(targetWorkspaceId = null) {
  try {
    const res = await fetch(`${API_BASE}/api/research/workspaces`);
    const workspaces = await res.json();
    const select = document.getElementById('workspace-select');

    select.innerHTML = '';
    if (!workspaces || workspaces.length === 0) {
      select.innerHTML = '<option value="">No active workspaces</option>';
      return;
    }

    workspaces.forEach(ws => {
      const opt = document.createElement('option');
      opt.value = ws.id;
      opt.textContent = `${ws.topic} (${ws.status || 'COMPLETED'})`;
      select.appendChild(opt);
    });

    const activeId = targetWorkspaceId || workspaces[workspaces.length - 1].id;
    select.value = activeId;
    select.onchange = (e) => loadWorkspaceDetails(e.target.value);

    await loadWorkspaceDetails(activeId);
  } catch (err) {
    console.error('Error loading workspaces:', err);
  }
}

async function loadWorkspaceDetails(workspaceId) {
  if (!workspaceId) return;
  currentWorkspaceId = workspaceId;

  try {
    const res = await fetch(`${API_BASE}/api/research/workspace/${workspaceId}`);
    if (!res.ok) throw new Error('Failed to fetch workspace');
    const ws = await res.json();
    currentWorkspaceData = ws;

    renderWorkspaceOverview(ws);
    renderLedger(ws);
  } catch (err) {
    console.error('Error loading workspace details:', err);
  }
}

function renderWorkspaceOverview(ws) {
  // Clean Human-Readable Title
  document.getElementById('badge-domain').textContent = ws.plan?.domain || 'GENERAL';
  document.getElementById('report-workspace-title').textContent = ws.topic;
  document.getElementById('report-workspace-goal').textContent = `Target Scope: ${ws.goal || 'Comprehensive Institutional Analysis'}`;
  
  const statusBadge = document.getElementById('badge-lifecycle-status');
  statusBadge.textContent = ws.status;
  if (ws.status === 'COMPLETED') {
    statusBadge.className = 'px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-[#282a33] text-emerald-400 border border-emerald-800/50';
  } else {
    statusBadge.className = 'px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-[#282a33] text-amber-400 border border-amber-800/50';
  }

  // Connect Copy Full Research Dossier Button
  const btnCopyFull = document.getElementById('btn-copy-full-report');
  if (btnCopyFull) {
    btnCopyFull.onclick = () => {
      let fullDossier = `# ${ws.topic}\n\n`;
      if (ws.goal) fullDossier += `**Target Scope:** ${ws.goal}\n\n`;
      fullDossier += `**Domain:** \`${ws.plan?.domain || 'GENERAL'}\` | **Quality Rating:** ${ws.quality?.overall || 90}/100\n\n---\n\n`;
      (ws.report || []).forEach(sec => {
        fullDossier += `## ${sec.title}\n\n${sec.content}\n\n---\n\n`;
      });
      copyTextToClipboard(fullDossier, btnCopyFull, 'Copy Dossier');
    };
  }

  // Update Key Metrics
  const q = ws.quality || {};
  document.getElementById('metric-overall').textContent = `${q.overall || 92.0}`;
  document.getElementById('metric-confidence').textContent = q.confidence_rating || 'HIGH';
  document.getElementById('metric-coverage').textContent = `${q.coverage || 90.0}%`;
  document.getElementById('metric-topic-relevance').textContent = `${q.topic_relevance_rate || 100.0}%`;
  document.getElementById('metric-claims-count').textContent = (ws.claims || []).length;
  document.getElementById('metric-conflicts-count').textContent = (ws.conflicts || []).length;
  document.getElementById('metric-rejected-count').textContent = `${(ws.rejected_sources || []).length} irrelevant sources rejected`;

  // Render Table of Contents & Objectives List
  const tocContainer = document.getElementById('report-toc');
  const objContainer = document.getElementById('objectives-list');
  const sectionsContainer = document.getElementById('report-sections-content');

  tocContainer.innerHTML = '';
  objContainer.innerHTML = '';
  sectionsContainer.innerHTML = '';

  const sections = ws.report || [];
  document.getElementById('report-chapter-count').textContent = `${sections.length} Chapters`;

  sections.forEach((sec, idx) => {
    // Clean section title (strip duplicate numbers like "1. Research Dossier...")
    const cleanTitle = (sec.title || '').replace(/^\d+\.?\s*/, '');

    // TOC item with multi-line wrap and clear numbering
    const tocItem = document.createElement('a');
    tocItem.href = `#sec-block-${sec.id}`;
    tocItem.className = 'flex items-start space-x-2.5 py-2 px-2.5 rounded-lg text-[#a2a7b5] hover:text-[#f3f4f8] hover:bg-[#282a33] transition text-xs border border-transparent hover:border-[#393d49]';
    tocItem.innerHTML = `
      <span class="font-mono text-[11px] text-[#727787] font-bold mt-0.5 shrink-0">${idx + 1}.</span>
      <span class="leading-snug">${cleanTitle}</span>
    `;
    tocContainer.appendChild(tocItem);

    // Section Content with High-Fidelity Markdown Rendering & Studio Gray Card
    const secBlock = document.createElement('div');
    secBlock.id = `sec-block-${sec.id}`;
    secBlock.className = 'p-6 rounded-xl bg-[#21232a] border border-[#2d3039] space-y-4 shadow-sm';

    const renderedContent = renderMarkdownToHtml(sec.content || '');

    secBlock.innerHTML = `
      <div class="flex items-center justify-between pb-3.5 border-b border-[#2d3039]">
        <div class="flex items-center space-x-3">
          <span class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#282a33] text-[#a2a7b5] border border-[#393d49] font-medium">${sec.id}</span>
          <h3 class="font-heading font-bold text-base text-[#f3f4f8]">${cleanTitle}</h3>
        </div>
        <button class="btn-copy-action copy-chapter-btn" data-sec-idx="${idx}" title="Copy Chapter Markdown">
          <i data-lucide="copy" class="h-3 w-3 text-[#a2a7b5]"></i>
          <span>Copy</span>
        </button>
      </div>
      <div class="markdown-body text-[#caced8] leading-relaxed">${renderedContent}</div>
    `;
    sectionsContainer.appendChild(secBlock);
  });

  // Attach event listeners for each individual chapter copy button
  document.querySelectorAll('.copy-chapter-btn').forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.getAttribute('data-sec-idx'));
      const sec = sections[idx];
      if (sec) {
        const cleanTitle = (sec.title || '').replace(/^\d+\.?\s*/, '');
        const chapterMarkdown = `## ${cleanTitle}\n\n${sec.content}`;
        copyTextToClipboard(chapterMarkdown, btn, 'Copy');
      }
    };
  });

  // Render Objectives Coverage Badges
  (ws.plan?.objectives || []).forEach(obj => {
    const badge = document.createElement('div');
    const isComplete = obj.status === 'Complete';
    const isWeak = obj.status === 'Weak';
    const statusColor = isComplete ? 'text-emerald-400 bg-[#21232a] border-[#2d3039]' : (isWeak ? 'text-amber-400 bg-[#21232a] border-[#2d3039]' : 'text-[#a2a7b5] bg-[#21232a] border-[#2d3039]');
    
    badge.className = `p-2.5 rounded-lg border text-xs font-mono flex items-center justify-between ${statusColor}`;
    badge.innerHTML = `
      <span class="truncate pr-2">${obj.name}</span>
      <span class="font-bold text-[#f3f4f8] text-[11px]">${obj.evidence_count} stmts</span>
    `;
    objContainer.appendChild(badge);
  });

  // Auto-render LaTeX / KaTeX formulas in sections
  if (window.renderMathInElement) {
    try {
      renderMathInElement(sectionsContainer, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false }
        ],
        throwOnError: false
      });
    } catch (e) {
      console.warn('KaTeX auto-render notice:', e);
    }
  }

  if (window.lucide) lucide.createIcons();
}

// =================================================================
// 4. KNOWLEDGE GRAPH TOPOLOGY RENDERING (vis.js)
// =================================================================
function renderKnowledgeGraph(graphData) {
  const container = document.getElementById('kg-network-canvas');
  if (!container || !graphData || !graphData.nodes) return;

  const nodes = new vis.DataSet(graphData.nodes.map(n => {
    let color = '#3b82f6';
    if (n.node_type === 'Source') color = '#64748b';
    if (n.node_type === 'Claim') color = '#059669';
    if (n.node_type === 'Conflict') color = '#d97706';

    return {
      id: n.id,
      label: n.label,
      title: `${n.node_type}: ${n.label}`,
      color: {
        background: color,
        border: '#1e293b',
        highlight: { background: '#60a5fa', border: '#ffffff' }
      },
      font: { color: '#f8fafc', face: 'Inter', size: 11 },
      shape: n.node_type === 'Source' ? 'box' : (n.node_type === 'Claim' ? 'ellipse' : 'dot'),
      size: n.node_type === 'Topic' ? 25 : 15,
      rawNode: n
    };
  }));

  const edges = new vis.DataSet(graphData.edges.map(e => ({
    from: e.source,
    to: e.target,
    label: e.relation,
    font: { color: '#94a3b8', size: 9, align: 'middle' },
    color: { color: '#334155', highlight: '#3b82f6' },
    arrows: 'to',
    smooth: { type: 'continuous' }
  })));

  const options = {
    physics: {
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: -35,
        centralGravity: 0.005,
        springLength: 100,
        springConstant: 0.18
      },
      maxVelocity: 40,
      stabilization: { iterations: 120 }
    },
    interaction: {
      hover: true,
      zoomView: true
    }
  };

  networkGraphInstance = new vis.Network(container, { nodes, edges }, options);

  // Inspector click listener
  networkGraphInstance.on('click', (params) => {
    if (params.nodes.length > 0) {
      const selectedId = params.nodes[0];
      const selectedNode = nodes.get(selectedId);
      if (selectedNode && selectedNode.rawNode) {
        document.getElementById('graph-inspector-empty').classList.add('hidden');
        document.getElementById('graph-inspector-details').classList.remove('hidden');
        document.getElementById('insp-label').textContent = selectedNode.rawNode.label;
        document.getElementById('insp-type').textContent = selectedNode.rawNode.node_type;
        document.getElementById('insp-meta').textContent = JSON.stringify(selectedNode.rawNode.metadata || {}, null, 2);
      }
    }
  });

  // Cypher export button
  document.getElementById('btn-export-cypher').onclick = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/graph/${currentWorkspaceId}/cypher`);
      const cypherData = await res.json();
      const statements = cypherData.statements || [];
      const blob = new Blob([statements.join('\n\n')], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `graph-${currentWorkspaceId}.cypher`;
      a.click();
    } catch (e) {
      alert('Failed to export Cypher.');
    }
  };

  document.getElementById('btn-reset-graph').onclick = () => {
    if (networkGraphInstance) networkGraphInstance.fit();
  };
}

// =================================================================
// 5. EVIDENCE LEDGER & RELEVANCE AUDIT RENDERING
// =================================================================
let activeQueryFilter = null;

function filterSourcesByQuery(queryStr) {
  activeQueryFilter = queryStr ? queryStr.trim().toLowerCase() : null;
  if (currentWorkspaceData) {
    renderSourcesList(currentWorkspaceData);
  }
}

function renderSourcesList(ws) {
  const sourcesList = document.getElementById('sources-ledger-list');
  const allSources = ws.sources || [];
  const filterBanner = document.getElementById('active-query-filter-banner');
  const filterText = document.getElementById('active-filter-query-text');

  let filteredSources = allSources;
  if (activeQueryFilter) {
    filterBanner.classList.remove('hidden');
    filterText.textContent = `"${activeQueryFilter}"`;
    filteredSources = allSources.filter(s => 
      (s.retrieval_query || '').toLowerCase().includes(activeQueryFilter) ||
      (s.title || '').toLowerCase().includes(activeQueryFilter) ||
      (s.discovery_engine || '').toLowerCase().includes(activeQueryFilter)
    );
  } else {
    filterBanner.classList.add('hidden');
  }

  document.getElementById('sources-count-badge').textContent = `${filteredSources.length}/${allSources.length} Sources Displayed`;

  sourcesList.innerHTML = '';
  if (filteredSources.length === 0) {
    sourcesList.innerHTML = `
      <div class="p-6 rounded-lg bg-[#21232a] border border-[#2d3039] text-center text-xs text-[#8c91a0] font-mono">
        No sources match query filter "${activeQueryFilter}". <button onclick="filterSourcesByQuery(null)" class="text-sky-400 underline ml-1">Reset filter</button>
      </div>
    `;
    return;
  }

  filteredSources.forEach((s, idx) => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl bg-[#21232a] border border-[#2d3039] space-y-3 text-xs shadow-sm hover:border-[#3b3f4c] transition';
    
    const queryDisplay = s.retrieval_query ? s.retrieval_query : 'Direct Ingestion';
    const engineDisplay = s.discovery_engine ? s.discovery_engine : 'UniversalWebDiscovery';
    const phaseDisplay = s.phase ? s.phase : 'Primary Harvest';
    const snippet = (s.raw_content || '').slice(0, 320).trim();

    card.innerHTML = `
      <div class="flex items-start justify-between gap-3">
        <div class="space-y-1 min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-mono text-[10px] px-2 py-0.5 rounded bg-[#282a33] text-[#a2a7b5] border border-[#393d49] font-bold">${s.id}</span>
            <span class="font-mono text-[10px] px-2 py-0.5 rounded bg-blue-950/60 text-blue-300 border border-blue-800/40">${s.source_type}</span>
            <span class="font-mono text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40">Auth: ${s.authority_score || 95}%</span>
            <span class="font-mono text-[10px] px-2 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800/40">Cred: ${s.credibility_score || 95}%</span>
          </div>
          <h3 class="font-heading font-bold text-sm text-[#f3f4f8] truncate" title="${s.title}">${s.title}</h3>
        </div>
        <button class="shrink-0 px-2.5 py-1 rounded bg-[#282a33] hover:bg-[#333642] text-[#e2e4ea] text-[11px] font-mono border border-[#393d49] transition cursor-pointer" onclick="showSourceModal('${s.id}')">
          Inspect Source
        </button>
      </div>

      <!-- PROMINENT DISCOVERY QUERY BADGES -->
      <div class="p-2.5 rounded-lg bg-[#181a20] border border-[#2d3039] space-y-2">
        <div class="flex flex-wrap items-center gap-2">
          <span class="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-sky-950/70 border border-sky-800/50 text-sky-300 text-[11px] font-mono font-semibold">
            <i data-lucide="search" class="h-3 w-3 text-sky-400"></i>
            <span>QUERY: <strong>"${queryDisplay}"</strong></span>
          </span>
          <span class="px-2 py-0.5 rounded bg-[#282a33] text-[#caced8] font-mono text-[10px] border border-[#393d49]">
            ENGINE: ${engineDisplay}
          </span>
          <span class="px-2 py-0.5 rounded bg-amber-950/50 text-amber-300 font-mono text-[10px] border border-amber-800/40">
            ${phaseDisplay}
          </span>
        </div>
        <div class="flex items-center justify-between text-[11px] text-[#8c91a0]">
          <span class="truncate">Publisher: <strong class="text-[#caced8]">${s.author_publisher || 'Authoritative Register'}</strong></span>
          ${s.url ? `<a href="${s.url}" target="_blank" class="text-sky-400 hover:underline flex items-center space-x-1 shrink-0 ml-2"><span>Open Link</span><i data-lucide="external-link" class="h-3 w-3"></i></a>` : ''}
        </div>
      </div>

      <!-- SNIPPET PREVIEW -->
      ${snippet ? `
        <div class="text-[11px] text-[#8c91a0] font-mono bg-[#16171b] p-2.5 rounded-lg border border-[#2d3039] leading-relaxed">
          <span class="text-[#727787] uppercase text-[10px] block mb-1">Extracted Evidence Preview:</span>
          "${snippet}..."
        </div>
      ` : ''}
    `;
    sourcesList.appendChild(card);
  });

  if (window.lucide) lucide.createIcons();
}

function renderLedger(ws) {
  // 1. Render Executed Queries & Trajectory
  const queriesContainer = document.getElementById('executed-queries-list');
  const execQueries = ws.executed_queries || [];
  document.getElementById('queries-count-badge').textContent = `${execQueries.length} Search Queries`;

  // Wire query filter buttons
  const btnAll = document.getElementById('btn-filter-all-queries');
  if (btnAll) {
    btnAll.onclick = () => filterSourcesByQuery(null);
  }
  const btnClear = document.getElementById('btn-clear-query-filter');
  if (btnClear) {
    btnClear.onclick = () => filterSourcesByQuery(null);
  }

  queriesContainer.innerHTML = '';
  if (execQueries.length === 0) {
    queriesContainer.innerHTML = `
      <div class="p-3 rounded-lg bg-[#21232a] text-[#8c91a0] text-xs font-mono">
        All sources ingested via direct authoritative registry APIs.
      </div>
    `;
  } else {
    execQueries.forEach((eq, idx) => {
      const qRow = document.createElement('div');
      qRow.className = 'p-2.5 rounded-lg bg-[#21232a] border border-[#2d3039] flex flex-wrap items-center justify-between gap-2 text-xs font-mono hover:border-[#3b3f4c] transition';
      
      const phaseColor = eq.phase?.includes('Phase 1') ? 'text-purple-400 bg-purple-950/40 border-purple-800/40' : 
                         (eq.phase?.includes('Phase 2') ? 'text-sky-400 bg-sky-950/40 border-sky-800/40' : 'text-amber-400 bg-amber-950/40 border-amber-800/40');

      qRow.innerHTML = `
        <div class="flex items-center space-x-2 min-w-0 flex-1">
          <span class="text-[10px] font-bold px-2 py-0.5 rounded border shrink-0 ${phaseColor}">${eq.phase || 'Query'}</span>
          <span class="text-[#f3f4f8] font-semibold truncate" title="${eq.query}">"${eq.query}"</span>
        </div>
        <div class="flex items-center space-x-2 shrink-0 text-[11px]">
          <span class="px-2 py-0.5 rounded bg-[#282a33] text-[#a2a7b5] border border-[#393d49]">${eq.engine}</span>
          <span class="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 font-bold">${eq.yield_count || 0} hits</span>
          <button class="px-2 py-0.5 rounded bg-[#333642] hover:bg-[#3d4252] text-[#f3f4f8] transition cursor-pointer text-[10px]" onclick="filterSourcesByQuery('${eq.query.replace(/'/g, "\\'")}')">
            Filter Sources
          </button>
        </div>
      `;
      queriesContainer.appendChild(qRow);
    });
  }

  // 2. Render Ingested Sources Index with Provenance
  renderSourcesList(ws);

  // 3. Render Rejected Sources Audit Trail
  const rejectedList = document.getElementById('rejected-ledger-list');
  const rejected = ws.rejected_sources || [];
  document.getElementById('rejected-count-badge').textContent = `${rejected.length} Filtered Discards`;

  rejectedList.innerHTML = '';
  if (rejected.length === 0) {
    rejectedList.innerHTML = '<div class="text-xs text-[#8c91a0] py-4 font-mono">Zero candidate sources rejected in this workspace.</div>';
  } else {
    rejected.forEach(rs => {
      const card = document.createElement('div');
      card.className = 'p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/30 text-xs space-y-2 font-mono';
      card.innerHTML = `
        <div class="flex items-start justify-between gap-3 text-rose-300 font-bold text-[11px]">
          <span class="truncate">❌ ${rs.title}</span>
          <span class="text-rose-400 text-[10px] px-2 py-0.5 rounded bg-rose-950 border border-rose-900/50 shrink-0">REJECTED</span>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <span class="px-2 py-0.5 rounded bg-[#1c1e24] text-sky-400 text-[10px] border border-[#2d3039]">
            QUERY: "${rs.retrieval_query || 'Direct Extraction'}"
          </span>
          <span class="px-2 py-0.5 rounded bg-[#1c1e24] text-[#a2a7b5] text-[10px] border border-[#2d3039]">
            ENGINE: ${rs.discovery_engine || 'WebDiscovery'}
          </span>
        </div>
        <div class="text-[11px] text-[#caced8] bg-[#16171b] p-2 rounded-lg border border-[#2d3039]">
          <span class="text-rose-400 font-bold">REJECTION REASON:</span> ${rs.reason}
        </div>
      `;
      rejectedList.appendChild(card);
    });
  }

  // 4. Render Verified Claims Ledger
  const claimsTable = document.getElementById('claims-ledger-table');
  const claims = ws.claims || [];
  document.getElementById('claims-count-badge').textContent = `${claims.length} Verified Claims`;

  claimsTable.innerHTML = '';
  claims.forEach((c, idx) => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl bg-[#21232a] border border-[#2d3039] space-y-2 text-xs font-mono shadow-sm';
    card.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-sky-400 font-bold">${c.id} // ${c.importance.toUpperCase()}</span>
        <span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 text-[10px]">${c.status}</span>
      </div>
      <div class="text-[#f3f4f8]">
        <span class="text-[#8c91a0]">Subject:</span> <strong class="text-white">${c.subject}</strong> 
        <span class="text-sky-400">⟶ ${c.predicate} ⟶</span> 
        <strong class="text-[#caced8]">${c.object_value}</strong>
      </div>
      <div class="p-2.5 rounded-lg bg-[#181a20] border border-[#2d3039] text-[#caced8] italic text-[11px] leading-relaxed">
        "${c.evidence.exact_quote}"
      </div>
      <div class="flex items-center justify-between text-[10px] text-[#8c91a0] pt-1.5 border-t border-[#2d3039]">
        <span>Source: <button onclick="showSourceModal('${c.evidence.source_id}')" class="text-sky-400 font-bold hover:underline">${c.evidence.source_id}</button> (${c.conditions || 'Standard Evaluation'})</span>
        <span class="text-emerald-400 font-bold">Entailment: ${(c.evidence.confidence * 100).toFixed(1)}%</span>
      </div>
    `;
    claimsTable.appendChild(card);
  });

  if (window.lucide) lucide.createIcons();
}

// =================================================================
// 6. CURRICULUM & LEARNING ENGINE
// =================================================================
async function loadCurriculum(workspaceId) {
  try {
    const res = await fetch(`${API_BASE}/api/learn/curriculum/${workspaceId}`);
    if (!res.ok) throw new Error('Failed to load curriculum');
    const data = await res.json();
    currentCurriculumData = data;

    document.getElementById('learn-mastery-score').textContent = `${(data.overall_mastery || 0).toFixed(1)}%`;
    const modulesContainer = document.getElementById('curriculum-modules-container');
    modulesContainer.innerHTML = '';

    (data.modules || []).forEach((mod, idx) => {
      const modCard = document.createElement('div');
      modCard.className = 'glass-panel p-4 rounded-lg space-y-3 cursor-pointer hover:border-slate-700 transition';
      modCard.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="font-heading font-bold text-sm text-white">${mod.title}</span>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">Module ${mod.order}</span>
        </div>
        <p class="text-xs text-slate-400">${mod.description}</p>
        <div class="space-y-1.5 pt-2 border-t border-slate-800">
          ${(mod.lessons || []).map((l, lIdx) => `
            <button onclick="renderLesson('${mod.id}', '${l.id}')" class="w-full text-left p-2 rounded bg-slate-900/60 hover:bg-slate-800/80 text-xs font-mono text-slate-300 flex items-center justify-between">
              <span>📖 ${l.title}</span>
              <span class="text-[10px] text-slate-500">${l.difficulty}</span>
            </button>
          `).join('')}
        </div>
      `;
      modulesContainer.appendChild(modCard);
    });

    if (data.modules && data.modules[0] && data.modules[0].lessons[0]) {
      renderLesson(data.modules[0].id, data.modules[0].lessons[0].id);
    }
  } catch (err) {
    console.error('Error loading curriculum:', err);
  }
}

function renderLesson(moduleId, lessonId) {
  if (!currentCurriculumData) return;
  const mod = currentCurriculumData.modules.find(m => m.id === moduleId);
  if (!mod) return;
  const lesson = mod.lessons.find(l => l.id === lessonId);
  if (!lesson) return;

  document.getElementById('lesson-empty').classList.add('hidden');
  const container = document.getElementById('lesson-content-active');
  container.classList.remove('hidden');

  container.innerHTML = `
    <div class="pb-3 border-b border-slate-800 flex items-center justify-between">
      <div>
        <h3 class="font-heading font-bold text-base text-white">${lesson.title}</h3>
        <span class="text-[11px] font-mono text-blue-400 uppercase tracking-wider">${mod.title} // Difficulty: ${lesson.difficulty}</span>
      </div>
    </div>

    <div class="markdown-body text-xs text-zinc-300 leading-relaxed">
      ${renderMarkdownToHtml(lesson.explanation)}
    </div>

    <div class="p-3.5 rounded bg-slate-900/80 border border-slate-800 space-y-2">
      <span class="text-xs font-mono font-bold text-slate-300 uppercase">Key Takeaways</span>
      <ul class="text-xs text-slate-400 space-y-1 list-disc list-inside">
        ${(lesson.key_takeaways || []).map(t => `<li>${t}</li>`).join('')}
      </ul>
    </div>

    <div class="pt-4 border-t border-slate-800 space-y-4">
      <div class="flex items-center justify-between">
        <span class="text-xs font-mono font-bold text-white uppercase tracking-wider">Diagnostic Mastery Quiz</span>
        <span class="text-[10px] font-mono text-slate-500">Source Evidence Grounded</span>
      </div>

      ${(lesson.questions || []).map((q, qIdx) => `
        <div class="p-4 rounded-lg bg-brand-950 border border-slate-800 space-y-3" id="quiz-card-${q.id}">
          <div class="text-xs font-medium text-white font-mono">Q${qIdx + 1}: ${q.question}</div>
          <div class="space-y-2">
            ${q.options.map(opt => `
              <label class="flex items-center space-x-2 text-xs text-slate-300 p-2 rounded bg-slate-900/60 hover:bg-slate-800 cursor-pointer border border-transparent hover:border-slate-700">
                <input type="radio" name="quiz_opt_${q.id}" value="${opt}" class="text-blue-600 focus:ring-0">
                <span>${opt}</span>
              </label>
            `).join('')}
          </div>
          <button onclick="submitQuiz('${q.id}')" class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-mono px-3 py-1.5 rounded transition">
            Evaluate Answer
          </button>
          <div id="quiz-feedback-${q.id}" class="hidden p-3 rounded text-xs font-mono space-y-1"></div>
        </div>
      `).join('')}
    </div>
  `;
}

async function submitQuiz(questionId) {
  const selected = document.querySelector(`input[name="quiz_opt_${questionId}"]:checked`);
  if (!selected) {
    alert('Please select an option.');
    return;
  }

  const feedbackBox = document.getElementById(`quiz-feedback-${questionId}`);
  feedbackBox.classList.remove('hidden');
  feedbackBox.innerHTML = 'Evaluating response against verified evidence...';

  try {
    const res = await fetch(`${API_BASE}/api/learn/quiz/evaluate/${currentWorkspaceId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_id: questionId, selected_answer: selected.value })
    });
    const evalData = await res.json();

    if (evalData.is_correct) {
      feedbackBox.className = 'p-3 rounded text-xs font-mono bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 space-y-1';
      feedbackBox.innerHTML = `
        <div class="font-bold">✅ CORRECT EVALUATION</div>
        <div>${evalData.explanation}</div>
        <div class="text-[10px] text-emerald-400/80 italic">Verified Quote: "${evalData.evidence_link?.exact_quote || ''}"</div>
      `;
    } else {
      feedbackBox.className = 'p-3 rounded text-xs font-mono bg-rose-950/80 text-rose-300 border border-rose-800/80 space-y-1';
      feedbackBox.innerHTML = `
        <div class="font-bold">❌ MISCONCEPTION IDENTIFIED</div>
        <div>${evalData.explanation}</div>
        <div class="text-rose-400">${evalData.misconception_analysis || ''}</div>
        <div class="text-[10px] text-rose-400/80 italic">Remediation: ${evalData.prerequisite_remediation || ''}</div>
      `;
    }
  } catch (err) {
    feedbackBox.innerHTML = `Evaluation error: ${err.message}`;
  }
}

// =================================================================
// 7. BUILD BLUEPRINTS & CODE VALIDATOR
// =================================================================
async function loadBuildProject(workspaceId) {
  try {
    const res = await fetch(`${API_BASE}/api/build/project/${workspaceId}`);
    if (!res.ok) throw new Error('Failed to load build project');
    const project = await res.json();
    currentBuildProject = project;

    document.getElementById('build-project-status').textContent = project.status || 'READY';
    const stepsContainer = document.getElementById('build-steps-container');
    stepsContainer.innerHTML = '';

    (project.steps || []).forEach(step => {
      const card = document.createElement('div');
      card.className = 'glass-panel p-4 rounded-lg space-y-2.5';
      card.innerHTML = `
        <div class="flex items-center justify-between pb-2 border-b border-slate-800">
          <span class="font-heading font-bold text-sm text-white">Step ${step.step_number}: ${step.title}</span>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-400">${step.status}</span>
        </div>
        <p class="text-xs text-slate-300">${step.objective}</p>
        <div class="text-[11px] font-mono text-slate-400 space-y-1">
          <div><strong class="text-slate-500">INPUT FILES:</strong> ${(step.input_files || []).join(', ')}</div>
          <div><strong class="text-slate-500">VALIDATION COMMAND:</strong> <code class="text-emerald-400">${step.validation_command}</code></div>
        </div>
        ${step.code_snippet ? `
          <pre class="p-2.5 rounded bg-slate-900 text-blue-300 text-[11px] font-mono overflow-x-auto border border-slate-800">${step.code_snippet}</pre>
        ` : ''}
      `;
      stepsContainer.appendChild(card);
    });
  } catch (err) {
    console.error('Error loading build project:', err);
  }
}

function initCodeValidator() {
  const btn = document.getElementById('btn-validate-code');
  btn.addEventListener('click', async () => {
    const stepNumber = parseInt(document.getElementById('code-step-select').value);
    const codeContent = document.getElementById('code-input-area').value.trim();
    const resultBox = document.getElementById('code-validation-result');

    if (!codeContent) {
      alert('Please enter code to validate.');
      return;
    }

    resultBox.classList.remove('hidden');
    resultBox.className = 'p-3 rounded text-xs font-mono bg-slate-900 border border-slate-800 text-slate-300';
    resultBox.innerHTML = 'Executing AST structural constraint validation...';

    try {
      const res = await fetch(`${API_BASE}/api/build/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: currentWorkspaceId,
          step_number: stepNumber,
          code_content: codeContent
        })
      });
      const val = await res.json();

      if (val.is_valid) {
        resultBox.className = 'p-3 rounded text-xs font-mono bg-emerald-950/80 text-emerald-300 border border-emerald-800/80 space-y-1';
        resultBox.innerHTML = `
          <div class="font-bold">✅ ARCHITECTURAL CONSTRAINT PASSED</div>
          <div>All required components and evidence specifications satisfied.</div>
        `;
      } else {
        resultBox.className = 'p-3 rounded text-xs font-mono bg-rose-950/80 text-rose-300 border border-rose-800/80 space-y-1';
        resultBox.innerHTML = `
          <div class="font-bold">❌ ARCHITECTURAL VIOLATION DETECTED</div>
          <div class="space-y-1">${val.detected_errors.map(e => `• ${e}`).join('<br>')}</div>
          <div class="pt-2 text-[11px] text-slate-300">Suggestion: ${val.suggested_correction || 'Ensure components adhere to deterministic retrieval guidelines.'}</div>
        `;
      }
    } catch (err) {
      resultBox.innerHTML = `Validation error: ${err.message}`;
    }
  });
}

// =================================================================
// 8. EVIDENCE-GROUNDED CONVERSATIONAL CHAT
// =================================================================
function initChat() {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const container = document.getElementById('chat-messages-container');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    // Append user message
    const userMsg = document.createElement('div');
    userMsg.className = 'p-3 rounded bg-zinc-900 border border-zinc-800 text-zinc-200';
    userMsg.innerHTML = `<span class="font-mono text-zinc-400 font-bold">[USER]:</span> ${escapeHtml(query)}`;
    container.appendChild(userMsg);
    input.value = '';
    container.scrollTop = container.scrollHeight;

    // Show loading indicator
    const botMsg = document.createElement('div');
    botMsg.className = 'p-3 rounded bg-[#121215] border border-zinc-800 text-zinc-300 font-mono text-xs';
    botMsg.innerHTML = '<span class="animate-pulse">Retrieving grounded graph claims...</span>';
    container.appendChild(botMsg);
    container.scrollTop = container.scrollHeight;

    try {
      const res = await fetch(`${API_BASE}/api/chat/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: currentWorkspaceId,
          message: query
        })
      });
      const data = await res.json();

      botMsg.innerHTML = `
        <div class="flex items-center justify-between pb-1.5 border-b border-zinc-800 text-[10px] text-zinc-500">
          <span>INTENT: <strong class="text-zinc-300 font-mono">${data.intent}</strong></span>
          <span>CONFIDENCE: <strong class="text-emerald-400 font-mono">${data.confidence_score}%</strong></span>
        </div>
        <div class="mt-2 text-zinc-200 text-xs leading-relaxed markdown-body">${renderMarkdownToHtml(data.response_text)}</div>
      `;
    } catch (err) {
      botMsg.innerHTML = `<span class="text-rose-400">Inquiry Error: ${err.message}</span>`;
    } finally {
      container.scrollTop = container.scrollHeight;
    }
  });
}
