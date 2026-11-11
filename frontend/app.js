// Otto Frontend Controller

let activeTab = "quarantine";

async function fetchJson(url, options = {}) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API Request Failed");
    }
    return await res.json();
  } catch (error) {
    console.error("API error:", error);
    throw error;
  }
}

// Format Unix timestamp to localized time
function formatTimestamp(ts) {
  if (!ts) return "-";
  const date = new Date(ts * 1000);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// Update Top Metrics Strip
async function refreshMetrics() {
  try {
    const metrics = await fetchJson("/api/metrics");
    document.getElementById("metric-volume").textContent = `$${metrics.total_settled_volume.toFixed(2)}`;
    document.getElementById("metric-approved").textContent = metrics.approved_count;
    document.getElementById("metric-quarantine").textContent = metrics.quarantine_pending;
    document.getElementById("quarantine-count").textContent = metrics.quarantine_pending;
    document.getElementById("metric-blocked").textContent = metrics.adversarial_blocks;
  } catch (e) {
    // Keep quiet on connection retry
  }
}

// Load Benchmark Scenarios
async function loadScenarios() {
  try {
    const scenarios = await fetchJson("/api/scenarios");
    const container = document.getElementById("scenarios-container");
    container.innerHTML = "";

    scenarios.forEach((item) => {
      const div = document.createElement("div");
      div.className = "scenario-item";
      div.innerHTML = `
        <div class="scenario-item-title">${escapeHtml(item.label)}</div>
        <div class="scenario-item-desc">${escapeHtml(item.description)}</div>
      `;
      div.onclick = () => populateAndExecuteScenario(item);
      container.appendChild(div);
    });
  } catch (e) {
    console.error("Failed to load scenarios:", e);
  }
}

function populateAndExecuteScenario(item) {
  const req = item.request;
  document.getElementById("agent-role").value = req.agent.role;
  document.getElementById("agent-id").value = req.agent.agent_id;
  document.getElementById("vendor-name").value = req.vendor_name;
  document.getElementById("vendor-domain").value = req.vendor_domain;
  document.getElementById("category").value = req.category;
  document.getElementById("amount").value = req.amount.toFixed(2);
  document.getElementById("justification").value = req.justification;
  document.getElementById("raw-prompt").value = req.raw_prompt_context || "";

  // Auto trigger submission
  submitSpendIntent();
}

// Submit Spend Request to Backend
async function submitSpendIntent(e) {
  if (e) e.preventDefault();

  const submitBtn = document.getElementById("btn-submit-intent");
  submitBtn.disabled = true;
  submitBtn.textContent = "Processing Firewall & Policy Checks...";

  const payload = {
    agent: {
      agent_id: document.getElementById("agent-id").value.trim(),
      role: document.getElementById("agent-role").value,
      environment: "production",
    },
    vendor_name: document.getElementById("vendor-name").value.trim(),
    vendor_domain: document.getElementById("vendor-domain").value.trim(),
    category: document.getElementById("category").value.trim(),
    amount: parseFloat(document.getElementById("amount").value) || 0,
    currency: "USD",
    justification: document.getElementById("justification").value.trim(),
    raw_prompt_context: document.getElementById("raw-prompt").value.trim(),
    line_items: [
      {
        item_name: "Automated Resource Allocation",
        quantity: 1,
        unit_price: parseFloat(document.getElementById("amount").value) || 0,
      },
    ],
  };

  try {
    const res = await fetchJson("/api/spend-request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    renderTelemetry(res);
    await refreshAll();
  } catch (err) {
    alert(`Submission error: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Evaluate & Dispatch to PayPal Sandbox";
  }
}

function renderTelemetry(res) {
  const box = document.getElementById("telemetry-box");
  const pill = document.getElementById("telemetry-pill");
  const risk = document.getElementById("telemetry-risk");
  const reasoning = document.getElementById("telemetry-reasoning");
  const violationsRow = document.getElementById("telemetry-violations-row");
  const violationsText = document.getElementById("telemetry-violations");
  const paypalRow = document.getElementById("telemetry-paypal-row");
  const orderIdText = document.getElementById("telemetry-order-id");
  const approvalWrap = document.getElementById("telemetry-approval-link-wrap");
  const approvalLink = document.getElementById("telemetry-approval-link");

  box.style.display = "block";
  pill.textContent = res.decision;
  pill.className = `pill-decision ${res.decision.toLowerCase()}`;
  risk.textContent = res.evaluation.risk_score.toFixed(2);
  reasoning.textContent = res.evaluation.reasoning;

  if (res.evaluation.violations && res.evaluation.violations.length > 0) {
    violationsRow.style.display = "block";
    violationsText.textContent = res.evaluation.violations.join(" | ");
  } else {
    violationsRow.style.display = "none";
  }

  if (res.paypal_order && res.paypal_order.order_id) {
    paypalRow.style.display = "block";
    orderIdText.textContent = res.paypal_order.order_id;

    if (res.paypal_order.approval_url) {
      approvalWrap.style.display = "block";
      approvalLink.href = res.paypal_order.approval_url;
    } else {
      approvalWrap.style.display = "none";
    }
  } else {
    paypalRow.style.display = "none";
    approvalWrap.style.display = "none";
  }
}

// Load Quarantine Queue
async function loadQuarantine() {
  const container = document.getElementById("quarantine-container");
  try {
    const list = await fetchJson("/api/quarantine");
    if (!list || list.length === 0) {
      container.innerHTML = `<div class="empty-state">No transactions currently in quarantine hold.</div>`;
      return;
    }

    container.innerHTML = "";
    list.forEach((item) => {
      const card = document.createElement("div");
      card.className = "quarantine-card";
      card.innerHTML = `
        <div class="quarantine-header">
          <strong>${escapeHtml(item.request.vendor_name)} ($${item.request.amount.toFixed(2)})</strong>
          <span class="pill-decision quarantined">HOLD: DUAL-CONTROL</span>
        </div>
        <div class="telemetry-row">
          <strong>Agent:</strong> ${escapeHtml(item.request.agent.agent_id)} (${escapeHtml(item.request.agent.role)})
        </div>
        <div class="telemetry-row">
          <strong>Reason:</strong> ${escapeHtml(item.evaluation.reasoning)}
        </div>
        <div class="telemetry-row">
          <strong>PayPal Order ID:</strong> <span class="cell-mono">${escapeHtml(item.paypal_order ? item.paypal_order.order_id : "-")}</span>
        </div>
        <div class="quarantine-actions">
          <button class="btn btn-success" onclick="resolveQuarantine('${item.transaction_id}', 'APPROVE')">
            Approve & Capture PayPal Order
          </button>
          <button class="btn btn-danger" onclick="resolveQuarantine('${item.transaction_id}', 'REJECT')">
            Reject & Void
          </button>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    console.error("Failed to load quarantine:", e);
  }
}

async function resolveQuarantine(txId, action) {
  try {
    await fetchJson(`/api/quarantine/${txId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: action, reviewer_note: `Manual resolution by compliance officer (${action})` }),
    });
    await refreshAll();
  } catch (err) {
    alert(`Failed to resolve transaction: ${err.message}`);
  }
}

// Load Audited Transaction Ledger
async function loadLedger() {
  const tbody = document.getElementById("ledger-tbody");
  try {
    const transactions = await fetchJson("/api/ledger");
    if (!transactions || transactions.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="empty-state">No transactions recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    transactions.forEach((tx) => {
      const tr = document.createElement("tr");
      const decisionClass = tx.evaluation.status.toLowerCase();
      tr.innerHTML = `
        <td class="cell-mono">${formatTimestamp(tx.created_at)}</td>
        <td class="cell-mono">${escapeHtml(tx.transaction_id)}</td>
        <td>${escapeHtml(tx.request.agent.role)}</td>
        <td>${escapeHtml(tx.request.vendor_name)}</td>
        <td class="cell-mono"><strong>$${tx.request.amount.toFixed(2)}</strong></td>
        <td><span class="pill-decision ${decisionClass}">${escapeHtml(tx.evaluation.status)}</span></td>
        <td><span class="status-badge">${escapeHtml(tx.settlement_status)}</span></td>
        <td class="cell-mono">${escapeHtml(tx.paypal_order ? tx.paypal_order.order_id : "-")}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("Failed to load ledger:", e);
  }
}

// Load Policies Table
async function loadPolicies() {
  const tbody = document.getElementById("policies-tbody");
  try {
    const rules = await fetchJson("/api/rules");
    tbody.innerHTML = "";
    Object.values(rules).forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${escapeHtml(r.agent_role)}</strong></td>
        <td class="cell-mono">$${r.max_single_spend.toFixed(2)}</td>
        <td class="cell-mono">$${r.hourly_velocity_limit.toFixed(2)}/hr</td>
        <td class="cell-mono">$${r.require_dual_control_above.toFixed(2)}</td>
        <td><span style="font-size: 11px;">${r.allowed_categories.join(", ")}</span></td>
        <td><span style="font-size: 11px; color: var(--status-danger-text);">${r.prohibited_categories.join(", ")}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    console.error("Failed to load policies:", e);
  }
}

// Tab Switching
function switchTab(tabName) {
  activeTab = tabName;
  document.getElementById("tab-btn-quarantine").classList.toggle("active", tabName === "quarantine");
  document.getElementById("tab-btn-ledger").classList.toggle("active", tabName === "ledger");
  document.getElementById("tab-btn-policies").classList.toggle("active", tabName === "policies");

  document.getElementById("tab-content-quarantine").style.display = tabName === "quarantine" ? "block" : "none";
  document.getElementById("tab-content-ledger").style.display = tabName === "ledger" ? "block" : "none";
  document.getElementById("tab-content-policies").style.display = tabName === "policies" ? "block" : "none";
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function refreshAll() {
  await Promise.all([
    refreshMetrics(),
    loadQuarantine(),
    loadLedger(),
  ]);
}

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("spend-form").addEventListener("submit", submitSpendIntent);
  loadScenarios();
  loadPolicies();
  refreshAll();

  // Periodic metrics refresh every 10 seconds
  setInterval(refreshAll, 10000);
});

