// Frontend logic for Dhaga & Co Intelligent Returns Triage Console

const API_BASE = "http://localhost:8000/api/v1";

let currentRecords = [];
let activeTab = "dashboard";

// DOM Elements
const dashboardView = document.getElementById("dashboard-view");
const intakeView = document.getElementById("intake-view");
const tabDashboard = document.getElementById("tab-dashboard");
const tabIntake = document.getElementById("tab-intake");
const apiStatusBadge = document.getElementById("api-status-badge");
const auditModal = document.getElementById("audit-modal");
const auditModalBody = document.getElementById("audit-modal-body");

// Initialize on load
document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupPresets();
  setupForm();
  checkApiHealth();
  refreshData();

  // Auto-refresh every 10 seconds
  setInterval(refreshData, 10000);
});

function setupNavigation() {
  tabDashboard.addEventListener("click", () => {
    activeTab = "dashboard";
    tabDashboard.classList.add("active");
    tabIntake.classList.remove("active");
    dashboardView.style.display = "block";
    intakeView.style.display = "none";
    refreshData();
  });

  tabIntake.addEventListener("click", () => {
    activeTab = "intake";
    tabIntake.classList.add("active");
    tabDashboard.classList.remove("active");
    dashboardView.style.display = "none";
    intakeView.style.display = "block";
  });
}

function setupPresets() {
  const container = document.getElementById("preset-container");
  if (!container || typeof SAMPLE_PRESETS === "undefined") return;

  container.innerHTML = "";
  SAMPLE_PRESETS.forEach(preset => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "preset-pill";
    btn.textContent = preset.title;
    btn.addEventListener("click", () => {
      document.getElementById("input-order-id").value = preset.order_id;
      document.getElementById("input-sku").value = preset.sku;
      document.getElementById("input-vendor-id").value = preset.vendor_id;
      document.getElementById("input-raw-text").value = preset.raw_text;
      document.getElementById("input-catalog-notes").value = preset.catalog_sizing_notes;
    });
    container.appendChild(btn);
  });
}

async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      apiStatusBadge.innerHTML = `<span class="status-dot"></span> Backend Active (${data.models.model_1})`;
      apiStatusBadge.style.color = "var(--accent-emerald)";
      apiStatusBadge.style.borderColor = "rgba(16, 185, 129, 0.3)";
    } else {
      throw new Error("API not ok");
    }
  } catch (err) {
    apiStatusBadge.innerHTML = `<span class="status-dot" style="background:var(--accent-rose)"></span> Backend Offline`;
    apiStatusBadge.style.color = "var(--accent-rose)";
    apiStatusBadge.style.borderColor = "rgba(239, 68, 68, 0.3)";
  }
}

async function refreshData() {
  await Promise.all([
    fetchAnalytics(),
    fetchRecords()
  ]);
}

async function fetchAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/triage/analytics/summary`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("stat-total").textContent = data.total_returns_processed;
    document.getElementById("stat-reduction").textContent = `${data.unclassified_other_reduction_pct}%`;
    document.getElementById("stat-auto").textContent = data.auto_triaged_count;
    document.getElementById("stat-reconciled").textContent = data.reconciled_count;
    document.getElementById("stat-flagged").textContent = data.flagged_for_review_count;
    document.getElementById("stat-vendor-defect").textContent = `${data.actionable_vendor_defect_rate}%`;

    // Render dialect badge breakdown
    const dialectContainer = document.getElementById("dialect-distribution");
    if (dialectContainer) {
      dialectContainer.innerHTML = Object.entries(data.dialect_distribution || {})
        .map(([k, v]) => `<span class="badge badge-dialect">${k}: ${v}</span>`)
        .join(" ");
    }
  } catch (e) {
    console.error("Failed to load analytics:", e);
  }
}

async function fetchRecords() {
  const categoryFilter = document.getElementById("filter-category").value;
  const statusFilter = document.getElementById("filter-status").value;

  let url = `${API_BASE}/triage?limit=100`;
  if (categoryFilter) url += `&category=${encodeURIComponent(categoryFilter)}`;
  if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;

  try {
    const res = await fetch(url);
    if (!res.ok) return;
    currentRecords = await res.json();
    renderTable(currentRecords);
  } catch (e) {
    console.error("Failed to load records:", e);
  }
}

function renderTable(records) {
  const tbody = document.getElementById("triage-tbody");
  tbody.innerHTML = "";

  if (records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-dim);">No return records found. Use the Mobile Intake Simulator or run the seed script!</td></tr>`;
    return;
  }

  records.forEach(r => {
    const tr = document.createElement("tr");

    // Status badge class
    let statusBadgeClass = "badge-auto";
    if (r.triage_status === "RECONCILED") statusBadgeClass = "badge-reconciled";
    else if (r.triage_status === "FLAGGED_FOR_MANUAL_REVIEW") statusBadgeClass = "badge-flagged";
    else if (r.triage_status === "REJECTED_SPAM") statusBadgeClass = "badge-rejected";

    // Confidence bar color
    const confPct = Math.round(r.confidence_score * 100);
    let confColor = "var(--accent-emerald)";
    if (r.confidence_score < 0.5) confColor = "var(--accent-rose)";
    else if (r.confidence_score < 0.85) confColor = "var(--accent-amber)";

    tr.innerHTML = `
      <td>
        <div style="font-weight: 700;">${r.order_id}</div>
        <div style="font-size: 0.75rem; color: var(--text-dim);">${r.sku} • ${r.vendor_id}</div>
      </td>
      <td>
        <span class="badge badge-dialect">${r.detected_dialect || 'N/A'}</span>
        ${r.is_sarcastic ? '<span class="badge" style="background:rgba(239,68,68,0.15);color:var(--accent-rose);">🎭 Sarcasm</span>' : ''}
        ${r.is_multi_issue ? '<span class="badge" style="background:rgba(139,92,246,0.15);color:var(--accent-purple);">⚡ Multi-issue</span>' : ''}
      </td>
      <td style="max-width: 320px;">
        <div style="font-size: 0.8125rem; color: var(--text-main); margin-bottom: 0.25rem;">"${escapeHtml(r.raw_text)}"</div>
        <div style="font-size: 0.75rem; color: var(--accent-gold); font-style: italic;">↳ ${escapeHtml(r.standardized_summary || '')}</div>
      </td>
      <td>
        <div style="font-weight: 600;">${r.primary_category}</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">${r.sub_category || ''}</div>
      </td>
      <td>
        <span class="badge ${statusBadgeClass}">${r.triage_status}</span>
        <div style="margin-top: 0.25rem;"><span class="badge badge-path">${r.routing_path}</span></div>
      </td>
      <td style="min-width: 120px;">
        <div class="conf-bar-wrapper">
          <span style="font-size: 0.8125rem; font-weight:700;">${r.confidence_score.toFixed(2)}</span>
          <div class="conf-bar">
            <div class="conf-fill" style="width: ${confPct}%; background: ${confColor};"></div>
          </div>
        </div>
      </td>
      <td>
        <button class="btn-secondary" style="font-size: 0.75rem; padding: 0.25rem 0.5rem;" onclick="viewAuditTrail('${r.id}')">
          Audit
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function setupForm() {
  const form = document.getElementById("intake-form");
  const resultPanel = document.getElementById("intake-result");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById("submit-btn");
    submitBtn.disabled = true;
    submitBtn.textContent = "Processing through 5-Phase Pipeline...";

    const payload = {
      order_id: document.getElementById("input-order-id").value,
      sku: document.getElementById("input-sku").value,
      vendor_id: document.getElementById("input-vendor-id").value,
      raw_text: document.getElementById("input-raw-text").value,
      catalog_sizing_notes: document.getElementById("input-catalog-notes").value
    };

    try {
      const res = await fetch(`${API_BASE}/triage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error("HTTP " + res.status);
      }

      const record = await res.json();
      resultPanel.style.display = "block";
      renderResultCard(record);
      refreshData();
    } catch (err) {
      alert("Submission error: " + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Run Intelligent Triage Pipeline";
    }
  });
}

function renderResultCard(record) {
  const container = document.getElementById("result-card-body");
  let statusBadgeClass = "badge-auto";
  if (record.triage_status === "RECONCILED") statusBadgeClass = "badge-reconciled";
  else if (record.triage_status === "FLAGGED_FOR_MANUAL_REVIEW") statusBadgeClass = "badge-flagged";
  else if (record.triage_status === "REJECTED_SPAM") statusBadgeClass = "badge-rejected";

  container.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
      <span class="badge ${statusBadgeClass}" style="font-size: 0.875rem;">Status: ${record.triage_status}</span>
      <span class="badge badge-path" style="font-size: 0.8125rem;">Route: ${record.routing_path}</span>
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
      <div>
        <div style="font-size:0.75rem; color:var(--text-muted);">EXTRACTED CATEGORY</div>
        <div style="font-size:1.1rem; font-weight:700; color:var(--accent-gold);">${record.primary_category}</div>
        <div style="font-size:0.85rem; color:var(--text-muted);">${record.sub_category || 'N/A'}</div>
      </div>
      <div>
        <div style="font-size:0.75rem; color:var(--text-muted);">CONFIDENCE & SPEED</div>
        <div style="font-size:1.1rem; font-weight:700;">${record.confidence_score.toFixed(2)} (${record.execution_time_ms} ms)</div>
        <div style="font-size:0.85rem; color:var(--text-muted);">Dialect: ${record.detected_dialect || 'N/A'}</div>
      </div>
    </div>
    <div style="background:var(--bg-secondary); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle); margin-bottom: 1rem;">
      <div style="font-size:0.75rem; color:var(--accent-gold); font-weight:600; margin-bottom:0.25rem;">STANDARDIZED SUMMARY</div>
      <div style="font-size:0.875rem;">${escapeHtml(record.standardized_summary || '')}</div>
    </div>
    ${record.reconciliation_notes ? `
    <div style="background:rgba(139,92,246,0.1); padding:0.75rem; border-radius:var(--radius-sm); border:1px solid rgba(139,92,246,0.3);">
      <div style="font-size:0.75rem; color:var(--accent-purple); font-weight:600; margin-bottom:0.25rem;">MODEL 2 RECONCILIATION NOTES</div>
      <div style="font-size:0.875rem;">${escapeHtml(record.reconciliation_notes)}</div>
    </div>
    ` : ''}
  `;
}

function viewAuditTrail(recordId) {
  const record = currentRecords.find(r => r.id === recordId);
  if (!record) return;

  auditModalBody.innerHTML = `
    <div style="margin-bottom:1.5rem;">
      <div style="font-size:0.8125rem; color:var(--text-muted);">Order Reference</div>
      <div style="font-size:1.25rem; font-weight:700;">${record.order_id} <span style="font-size:0.875rem; font-weight:400; color:var(--text-dim);">(${record.sku})</span></div>
    </div>

    <div class="pipeline-step">
      <div class="step-title">Phase 0: Deterministic Ingestion & Sanitation</div>
      <div class="step-content">
        <div><strong>Raw Customer Text:</strong> "${escapeHtml(record.raw_text)}"</div>
        <div><strong>Sanitized Text:</strong> "${escapeHtml(record.sanitized_text)}"</div>
      </div>
    </div>

    <div class="pipeline-step">
      <div class="step-title">Phase 1: Native Linguistic Extraction & Standardization (Model 1)</div>
      <div class="step-content">
        <div><strong>Standardized Summary:</strong> ${escapeHtml(record.standardized_summary || 'N/A')}</div>
        <div><strong>Detected Dialect:</strong> ${record.detected_dialect || 'N/A'}</div>
        <div><strong>Primary Category:</strong> ${record.primary_category} (${record.sub_category || ''})</div>
        <div><strong>Sarcasm Detected:</strong> ${record.is_sarcastic ? 'Yes 🎭' : 'No'} | <strong>Multi-issue:</strong> ${record.is_multi_issue ? 'Yes ⚡' : 'No'}</div>
      </div>
    </div>

    <div class="pipeline-step">
      <div class="step-title">Phase 2: Programmatic Confidence Routing Gate</div>
      <div class="step-content">
        <div><strong>Assigned Routing Path:</strong> <span class="badge badge-path">${record.routing_path}</span></div>
        <div><strong>Confidence Score:</strong> ${record.confidence_score.toFixed(2)}</div>
      </div>
    </div>

    ${record.model_2_model_name ? `
    <div class="pipeline-step" style="border-left-color: var(--accent-purple);">
      <div class="step-title" style="color: var(--accent-purple);">Phase 3: Dispute Reconciliation & Evaluation (Model 2: ${record.model_2_model_name})</div>
      <div class="step-content">
        <div><strong>Reconciliation Notes:</strong> ${escapeHtml(record.reconciliation_notes || 'N/A')}</div>
        <div><strong>Actionable for Vendor:</strong> ${record.is_actionable_for_vendor ? 'Yes' : 'No'}</div>
      </div>
    </div>
    ` : ''}

    <div class="pipeline-step" style="border-left-color: var(--accent-emerald);">
      <div class="step-title" style="color: var(--accent-emerald);">Phase 4: Persistence & Final State</div>
      <div class="step-content">
        <div><strong>Final Triage Status:</strong> <strong>${record.triage_status}</strong></div>
        <div><strong>Execution Latency:</strong> ${record.execution_time_ms} ms</div>
      </div>
    </div>
  `;

  auditModal.style.display = "flex";
}

function closeAuditModal() {
  auditModal.style.display = "none";
}

function escapeHtml(text) {
  if (!text) return "";
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.toString().replace(/[&<>"']/g, m => map[m]);
}
