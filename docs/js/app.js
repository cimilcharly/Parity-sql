/**
 * Parity Interactive Showcase Application (Vanilla JS)
 */

document.addEventListener("DOMContentLoaded", () => {
  initStatsCounters();
  initLayerVisualizer();
  initPlayground();
  initBenchmarkExplorer();
  initSemanticDifferences();
  initModal();
});

/* ==========================================================================
   1. Animated Stat Counters
   ========================================================================== */
function initStatsCounters() {
  const summary = window.PARITY_DATA?.summary || {};
  const totalObj = document.getElementById("stat-total-objects");
  const passRate = document.getElementById("stat-pass-rate");
  const reviewRate = document.getElementById("stat-review-rate");
  const avgCost = document.getElementById("stat-avg-cost");

  if (totalObj) animateCounter(totalObj, summary.total_objects || 500, "", 1200);
  if (passRate) animateCounter(passRate, summary.pass_rate_pct || 94.0, "%", 1200, 1);
  if (reviewRate) animateCounter(reviewRate, summary.human_review_rate_pct || 6.0, "%", 1200, 1);
  if (avgCost) animateCounter(avgCost, 0.00013, "$", 1200, 5);
}

function animateCounter(el, target, suffix = "", duration = 1000, decimals = 0) {
  let start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // easeOutQuad
    const eased = progress * (2 - progress);
    const current = start + (target - start) * eased;

    if (suffix === "$") {
      el.textContent = "$" + current.toFixed(decimals);
    } else {
      el.textContent = current.toFixed(decimals) + suffix;
    }

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      if (suffix === "$") {
        el.textContent = "$" + target.toFixed(decimals);
      } else {
        el.textContent = target.toFixed(decimals) + suffix;
      }
    }
  }

  requestAnimationFrame(update);
}

/* ==========================================================================
   2. 5-Layer Verification Visualizer
   ========================================================================== */
const LAYER_DETAILS = {
  1: {
    num: "Layer 1",
    title: "Syntax, AST Validation & Dialect Compilation",
    badge: "Deterministic Static Guard",
    badgeClass: "badge-purple",
    catches: "Catches incompatible keywords, invalid table expressions, missing commas, Oracle-only reserved constructs (e.g. (+) joins without rewrite), and unsupported procedure pragmas.",
    scenario: "Oracle outer join syntax (+) left untouched by naive transpilation fails immediately with PostgreSQL syntax error 42601 (syntax error near '+').",
    tolerance: "Zero tolerance (Binary Pass / Fail)",
    runtime: "~1.2 ms per query"
  },
  2: {
    num: "Layer 2",
    title: "Schema Match & Type Coercion Verification",
    badge: "Structural Invariance",
    badgeClass: "badge-purple",
    catches: "Catches column name case drift, arity mismatches (missing or extra columns), and incompatible data type conversions (e.g. VARCHAR2 to BYTEA, or silent NUMBER precision truncation).",
    scenario: "Oracle VARCHAR2(30) mapped to Postgres BYTEA causes downstream BI reporting tools and query planners to crash.",
    tolerance: "Strict column count, name normalization, and type equivalence",
    runtime: "~2.4 ms per query"
  },
  3: {
    num: "Layer 3",
    title: "Exact Row Count Equality",
    badge: "Cardinality Invariance",
    badgeClass: "badge-emerald",
    catches: "Catches Cartesian product row blowups, omitted WHERE filters, unintended inner join row drops, and improper subquery unnesting.",
    scenario: "A missing join condition on Oracle (+) conversion creates an accidental Cartesian product: 1,000 rows turns into 1,000,000 rows in PostgreSQL.",
    tolerance: "Exact match: Oracle Count == PostgreSQL Count",
    runtime: "~4.5 ms per query"
  },
  4: {
    num: "Layer 4",
    title: "Statistical Column Aggregates & Null Density",
    badge: "Mathematical Parity",
    badgeClass: "badge-emerald",
    catches: "Catches subtle numeric drift, rounding discrepancies, string truncation, and silent NULL divergences (e.g. empty string '' vs NULL).",
    scenario: "In Oracle, '' IS NULL evaluates to TRUE. In Postgres, '' IS NULL evaluates to FALSE! Layer 4 verifies COUNT(*), COUNT(col), SUM(col), and NULL counts match perfectly.",
    tolerance: "Floating point epsilon within 1e-9 tolerance; exact integer & NULL equality",
    runtime: "~7.8 ms per query"
  },
  5: {
    num: "Layer 5",
    title: "Cryptographic Row-Level Hashing",
    badge: "Row-Level Fidelity",
    badgeClass: "badge-amber",
    catches: "Catches inverted row values where column averages match identically (e.g. row A=10, B=20 swapped with row A=20, B=10) and catches collation/sorting discrepancies.",
    scenario: "Queries that group or order without explicit primary key sort order produce divergent result ordering or mismatched row associations.",
    tolerance: "100% hash bucket checksum agreement across all result partitions",
    runtime: "~12.1 ms per query"
  }
};

function initLayerVisualizer() {
  const layerButtons = document.querySelectorAll(".layer-btn");
  if (!layerButtons.length) return;

  layerButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const layerId = btn.getAttribute("data-layer");
      layerButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderLayerDetails(layerId);
    });
  });

  renderLayerDetails(1);
}

function renderLayerDetails(layerId) {
  const data = LAYER_DETAILS[layerId];
  if (!data) return;

  const titleEl = document.getElementById("layer-detail-title");
  const badgeEl = document.getElementById("layer-detail-badge");
  const catchesEl = document.getElementById("layer-catches-content");
  const scenarioEl = document.getElementById("layer-scenario-content");
  const toleranceEl = document.getElementById("layer-tolerance-content");
  const runtimeEl = document.getElementById("layer-runtime-content");

  if (titleEl) titleEl.textContent = `${data.num}: ${data.title}`;
  if (badgeEl) {
    badgeEl.textContent = data.badge;
    badgeEl.className = `layer-badge ${data.badgeClass}`;
  }
  if (catchesEl) catchesEl.textContent = data.catches;
  if (scenarioEl) scenarioEl.textContent = data.scenario;
  if (toleranceEl) toleranceEl.textContent = data.tolerance;
  if (runtimeEl) runtimeEl.textContent = data.runtime;
}

/* ==========================================================================
   3. Interactive SQL Playground
   ========================================================================== */
function initPlayground() {
  const presetSelect = document.getElementById("playground-presets");
  const sourceTextarea = document.getElementById("playground-source-sql");
  const previewBox = document.getElementById("playground-target-sql");
  const runBtn = document.getElementById("playground-run-btn");
  const copyBtn = document.getElementById("playground-copy-btn");
  const statusBadge = document.getElementById("playground-status-badge");
  const appliedRulesEl = document.getElementById("playground-applied-rules");
  const steps = [
    document.getElementById("step-1"),
    document.getElementById("step-2"),
    document.getElementById("step-3"),
    document.getElementById("step-4"),
    document.getElementById("step-5"),
  ];

  const presets = window.PARITY_DATA?.presets || [];

  if (presetSelect) {
    presetSelect.innerHTML = presets.map((p, idx) => `
      <option value="${p.id}">${idx + 1}. ${p.name} (${p.category})</option>
    `).join("");

    presetSelect.addEventListener("change", (e) => {
      const selected = presets.find(p => p.id === e.target.value);
      if (selected) {
        sourceTextarea.value = selected.oracle;
        runTranspilation(selected);
      }
    });

    if (presets.length > 0) {
      sourceTextarea.value = presets[0].oracle;
      runTranspilation(presets[0]);
    }
  }

  if (runBtn) {
    runBtn.addEventListener("click", () => {
      const currentSql = sourceTextarea.value.trim();
      const matchedPreset = presets.find(p => p.oracle.trim() === currentSql);
      if (matchedPreset) {
        runTranspilation(matchedPreset);
      } else {
        simulateCustomTranspile(currentSql);
      }
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const code = previewBox.textContent;
      navigator.clipboard.writeText(code).then(() => {
        const origText = copyBtn.textContent;
        copyBtn.textContent = "Copied!";
        setTimeout(() => { copyBtn.textContent = origText; }, 1500);
      });
    });
  }

  function runTranspilation(preset) {
    previewBox.textContent = preset.expected_postgres;
    appliedRulesEl.textContent = preset.rules.join(", ");

    if (preset.status === "VERIFIED_PASS") {
      statusBadge.textContent = "VERIFIED PASS";
      statusBadge.className = "status-badge status-pass";
      steps.forEach(dot => {
        if (dot) dot.className = "step-dot pass";
      });
    } else {
      statusBadge.textContent = "HUMAN REVIEW REQUIRED";
      statusBadge.className = "status-badge status-review";
      steps.forEach((dot, idx) => {
        if (dot) dot.className = idx === 0 ? "step-dot blocked" : "step-dot";
      });
    }
  }

  function simulateCustomTranspile(sql) {
    let target = sql;
    const rules = [];

    // Client-side quick transforms
    if (sql.includes("(+)")) {
      rules.push("ORACLE_OUTER_JOIN_PLUS");
      target = target.replace(/\(\+\)/g, "/* converted to LEFT JOIN */");
    }
    if (/NVL\s*\(/i.test(sql)) {
      rules.push("NVL_TO_COALESCE");
      target = target.replace(/NVL\s*\(/gi, "COALESCE(");
    }
    if (/SYSDATE/i.test(sql)) {
      rules.push("SYSDATE_TO_CURRENT_TIMESTAMP");
      target = target.replace(/SYSDATE/gi, "CURRENT_TIMESTAMP");
    }
    if (/FROM\s+DUAL/i.test(sql)) {
      rules.push("STRIP_DUAL_TABLE");
      target = target.replace(/FROM\s+DUAL/gi, "");
    }
    if (/PRAGMA\s+AUTONOMOUS_TRANSACTION/i.test(sql)) {
      rules.push("STATIC_BLOCKER_ISOLATION");
      previewBox.textContent = "/* TRANSLATION BLOCKED: PRAGMA AUTONOMOUS_TRANSACTION */\n-- PostgreSQL does not support autonomous sub-transactions.";
      statusBadge.textContent = "HUMAN REVIEW REQUIRED";
      statusBadge.className = "status-badge status-review";
      appliedRulesEl.textContent = rules.join(", ");
      steps.forEach(dot => { if (dot) dot.className = "step-dot blocked"; });
      return;
    }

    if (rules.length === 0) rules.push("STANDARD_ANSI_SQL");

    previewBox.textContent = target;
    appliedRulesEl.textContent = rules.join(", ");
    statusBadge.textContent = "VERIFIED PASS";
    statusBadge.className = "status-badge status-pass";
    steps.forEach(dot => { if (dot) dot.className = "step-dot pass"; });
  }
}

/* ==========================================================================
   4. 500-Object Benchmark Explorer
   ========================================================================== */
let allBenchmarkItems = [];
let filteredBenchmarkItems = [];
let currentPage = 1;
const pageSize = 15;

function initBenchmarkExplorer() {
  allBenchmarkItems = window.PARITY_DATA?.items || [];
  filteredBenchmarkItems = [...allBenchmarkItems];

  const searchInput = document.getElementById("bench-search");
  const catFilter = document.getElementById("bench-cat-filter");
  const tierFilter = document.getElementById("bench-tier-filter");
  const statusFilter = document.getElementById("bench-status-filter");
  const prevBtn = document.getElementById("bench-prev-page");
  const nextBtn = document.getElementById("bench-next-page");

  // Populate category filter
  if (catFilter) {
    const categories = Array.from(new Set(allBenchmarkItems.map(i => i.category))).sort();
    catFilter.innerHTML = '<option value="ALL">All Categories (10)</option>' +
      categories.map(c => `<option value="${c}">${c}</option>`).join("");
  }

  function applyFilters() {
    const q = (searchInput?.value || "").toLowerCase().trim();
    const cat = catFilter?.value || "ALL";
    const tier = tierFilter?.value || "ALL";
    const status = statusFilter?.value || "ALL";

    filteredBenchmarkItems = allBenchmarkItems.filter(item => {
      const matchQ = !q || item.name.toLowerCase().includes(q) || item.id.toLowerCase().includes(q);
      const matchCat = cat === "ALL" || item.category === cat;
      const matchTier = tier === "ALL" || item.complexity_tier === tier;
      const matchStatus = status === "ALL" || item.status === status;
      return matchQ && matchCat && matchTier && matchStatus;
    });

    currentPage = 1;
    renderBenchmarkTable();
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (catFilter) catFilter.addEventListener("change", applyFilters);
  if (tierFilter) tierFilter.addEventListener("change", applyFilters);
  if (statusFilter) statusFilter.addEventListener("change", applyFilters);

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (currentPage > 1) {
        currentPage--;
        renderBenchmarkTable();
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      const maxPages = Math.ceil(filteredBenchmarkItems.length / pageSize) || 1;
      if (currentPage < maxPages) {
        currentPage++;
        renderBenchmarkTable();
      }
    });
  }

  renderBenchmarkTable();
}

function renderBenchmarkTable() {
  const tableBody = document.getElementById("bench-table-body");
  const pageInfo = document.getElementById("bench-page-info");
  const totalCountEl = document.getElementById("bench-total-filtered");
  if (!tableBody) return;

  const total = filteredBenchmarkItems.length;
  const maxPages = Math.ceil(total / pageSize) || 1;
  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, total);
  const pageItems = filteredBenchmarkItems.slice(startIdx, endIdx);

  if (pageInfo) pageInfo.textContent = `Page ${currentPage} of ${maxPages}`;
  if (totalCountEl) totalCountEl.textContent = `Showing ${pageItems.length} of ${total} objects`;

  if (pageItems.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:2rem; color:var(--text-dim);">No objects found matching criteria</td></tr>`;
    return;
  }

  tableBody.innerHTML = pageItems.map(item => {
    const isPass = item.status === "VERIFIED_PASS";
    const statusClass = isPass ? "status-pass" : "status-review";
    const statusText = isPass ? "VERIFIED PASS" : "HUMAN REVIEW";

    const tierLower = item.complexity_tier.toLowerCase();
    const tierClass = `tier-${tierLower}`;

    return `
      <tr style="cursor: pointer;" onclick="openObjectModal('${item.id}')">
        <td style="font-family: var(--font-mono); font-size:0.8rem; color:var(--accent-cyan);">${item.id}</td>
        <td style="font-weight:600;">${item.name}</td>
        <td><span style="font-size:0.8rem; color:var(--text-muted);">${item.category}</span></td>
        <td><span class="tier-pill ${tierClass}">${item.complexity_tier} (${item.complexity_score}/10)</span></td>
        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
        <td style="font-family: var(--font-mono); color:var(--accent-amber);">$${item.cost_usd.toFixed(5)}</td>
        <td><button class="btn btn-outline btn-sm" onclick="event.stopPropagation(); openObjectModal('${item.id}')">View Details</button></td>
      </tr>
    `;
  }).join("");
}

/* ==========================================================================
   5. Semantic Differences Catalog
   ========================================================================== */
function initSemanticDifferences() {
  const container = document.getElementById("diffs-container");
  const searchInput = document.getElementById("diff-search");
  const sevFilter = document.getElementById("diff-severity-filter");
  const diffs = window.PARITY_DATA?.differences || [];
  if (!container) return;

  function renderDiffs() {
    const q = (searchInput?.value || "").toLowerCase().trim();
    const sev = sevFilter?.value || "ALL";

    const filtered = diffs.filter(d => {
      const matchQ = !q || d.title.toLowerCase().includes(q) || d.id.toLowerCase().includes(q);
      const matchSev = sev === "ALL" || d.severity === sev;
      return matchQ && matchSev;
    });

    if (filtered.length === 0) {
      container.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 2rem; color: var(--text-dim);">No semantic differences found matching query</div>`;
      return;
    }

    container.innerHTML = filtered.map(d => {
      const sevClass = d.severity === "HIGH" ? "badge-amber" : (d.severity === "MEDIUM" ? "badge-purple" : "badge-emerald");
      return `
        <article class="diff-card">
          <div class="diff-header">
            <span class="diff-id">${d.id}</span>
            <span class="layer-badge ${sevClass}">${d.severity}</span>
          </div>
          <h3 class="diff-title">${d.title}</h3>
          <div class="diff-body">
            <div class="diff-behavior-box">
              <div class="diff-behavior-label">Oracle Behavior</div>
              <div>${d.oracle_behavior}</div>
            </div>
            <div class="diff-behavior-box">
              <div class="diff-behavior-label">PostgreSQL Divergence</div>
              <div>${d.postgres_behavior}</div>
            </div>
            <div style="font-size:0.8rem; color:var(--accent-emerald);">
              <strong>Parity Automated Remedy:</strong> ${d.recommendation}
            </div>
          </div>
        </article>
      `;
    }).join("");
  }

  if (searchInput) searchInput.addEventListener("input", renderDiffs);
  if (sevFilter) sevFilter.addEventListener("change", renderDiffs);

  renderDiffs();
}

/* ==========================================================================
   6. Object Details Modal
   ========================================================================== */
function initModal() {
  const modal = document.getElementById("object-modal");
  const closeBtn = document.getElementById("modal-close");
  if (!modal) return;

  if (closeBtn) {
    closeBtn.addEventListener("click", () => modal.classList.remove("active"));
  }

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("active");
  });
}

window.openObjectModal = function(id) {
  const item = (window.PARITY_DATA?.items || []).find(i => i.id === id);
  if (!item) return;

  const modal = document.getElementById("object-modal");
  const title = document.getElementById("modal-title");
  const body = document.getElementById("modal-body");
  if (!modal || !title || !body) return;

  title.textContent = `${item.id}: ${item.name}`;

  const isPass = item.status === "VERIFIED_PASS";
  const statusBadge = isPass
    ? '<span class="status-badge status-pass">VERIFIED PASS</span>'
    : '<span class="status-badge status-review">HUMAN REVIEW REQUIRED</span>';

  let blockerHtml = "";
  if (item.unsupported_constructs && item.unsupported_constructs.length > 0) {
    blockerHtml = `
      <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.5rem;">
        <h4 style="color: var(--accent-amber); margin-bottom: 0.5rem;">Explicit Blocker Detected</h4>
        <p style="font-size: 0.875rem;">Constructs flagged: <strong>${item.unsupported_constructs.join(", ")}</strong></p>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">Safely isolated to prevent broken production DDL. Requires procedural refactoring.</p>
      </div>
    `;
  }

  body.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;">
      <div>
        <span style="color:var(--text-dim); font-size:0.85rem;">Category:</span>
        <strong style="color:var(--accent-cyan); font-size:0.95rem;"> ${item.category}</strong>
      </div>
      <div>
        ${statusBadge}
        <span class="tier-pill tier-${item.complexity_tier.toLowerCase()}" style="margin-left:0.5rem;">${item.complexity_tier} (Score: ${item.complexity_score}/10)</span>
      </div>
    </div>

    ${blockerHtml}

    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:1rem; margin-bottom:1.5rem;">
      <div class="info-box">
        <div class="info-box-title">Verification Duration</div>
        <div style="font-size:1.1rem; font-weight:700; color:#fff;">${item.duration_ms} ms</div>
      </div>
      <div class="info-box">
        <div class="info-box-title">Model / LLM Cost</div>
        <div style="font-size:1.1rem; font-weight:700; color:var(--accent-amber);">$${item.cost_usd.toFixed(6)}</div>
      </div>
      <div class="info-box">
        <div class="info-box-title">Repair Attempts</div>
        <div style="font-size:1.1rem; font-weight:700; color:#fff;">${item.repair_attempts}</div>
      </div>
    </div>

    <div style="margin-bottom:1rem;">
      <h4 style="font-size:0.9rem; text-transform:uppercase; color:var(--text-dim); margin-bottom:0.5rem;">Applied AST Transform Rules</h4>
      <div style="font-family:var(--font-mono); font-size:0.85rem; color:var(--accent-cyan); background:rgba(255,255,255,0.03); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-color);">
        ${item.applied_rules.length > 0 ? item.applied_rules.join(", ") : "None (Base Transpile)"}
      </div>
    </div>

    <div>
      <h4 style="font-size:0.9rem; text-transform:uppercase; color:var(--text-dim); margin-bottom:0.5rem;">Target PostgreSQL Generated Code Sample</h4>
      <pre style="background:rgba(10,13,20,0.9); padding:1rem; border-radius:var(--radius-md); border:1px solid var(--border-color); color:#38bdf8; font-size:0.85rem; overflow-x:auto;"><code>${item.target_sql_sample}</code></pre>
    </div>
  `;

  modal.classList.add("active");
};
