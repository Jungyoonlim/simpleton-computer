const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

let sessionId = null;

// ── API helpers ───────────────────────────────────────────────────
async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

// ── File loading ──────────────────────────────────────────────────
const dropZone = $("#drop-zone");
const fileInput = $("#file-input");

document.addEventListener("dragover", (e) => e.preventDefault());
document.addEventListener("drop", (e) => e.preventDefault());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("over"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("over");
  const files = e.dataTransfer.files;
  if (files && files.length) uploadFile(files[0]);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  const form = new FormData();
  form.append("file", file);
  dropZone.classList.add("loading");
  try {
    const data = await api("/api/load", { method: "POST", body: form });
    sessionId = data.session_id;
    render(data);
    $("#load-section").classList.add("hidden");
    $("#workspace").classList.remove("hidden");
  } catch (e) {
    alert("Load failed: " + e.message);
  } finally {
    dropZone.classList.remove("loading");
  }
}

// ── Rendering ─────────────────────────────────────────────────────
function typeHead(typeStr) {
  const m = typeStr.match(/^(\w+)/);
  return m ? m[1] : typeStr;
}

function render(data) {
  renderHandle(data.type, data.value);
  renderActions(data.actions);
  renderHistory(data.history || []);
  loadGoalTypes();
}

function renderHandle(typeStr, value) {
  const badge = $("#handle-type");
  badge.textContent = typeStr;
  badge.dataset.typeHead = typeHead(typeStr);

  const pre = $("#handle-value");
  if (value === null || value === undefined) {
    pre.textContent = "(empty)";
  } else if (value.items) {
    pre.textContent = value.items.join("\n");
    if (value.total > value.items.length) {
      pre.textContent += `\n… and ${value.total - value.items.length} more`;
    }
  } else if (value.text !== undefined) {
    let display = value.text;
    if (value.length > 500) display += `\n\n[${value.length} chars total]`;
    pre.textContent = display;
  } else {
    pre.textContent = String(value);
  }
}

function renderActions(actions) {
  const grid = $("#actions-grid");
  const count = $("#action-count");
  grid.innerHTML = "";
  count.textContent = `${actions.length} available`;

  for (const act of actions) {
    const card = document.createElement("div");
    card.className = "action-card";
    card.innerHTML = `
      <div class="action-name">
        ${act.name}
        ${act.pure
          ? '<span class="pure-tag">pure</span>'
          : '<span class="effect-tag">effectful</span>'}
      </div>
      <div class="action-sig">
        <span>${act.input_type}</span>
        <span class="arrow">→</span>
        <span>${act.output_type}</span>
      </div>
    `;
    card.addEventListener("click", () => executeAction(act.name, card));
    grid.appendChild(card);
  }
}

function renderHistory(history) {
  const trail = $("#history-trail");
  trail.innerHTML = "";
  for (let i = 0; i < history.length; i++) {
    const h = history[i];
    if (i > 0) {
      const arrow = document.createElement("span");
      arrow.className = "history-arrow";
      arrow.textContent = "→";
      trail.appendChild(arrow);
    }
    const node = document.createElement("span");
    node.className = "history-node";
    node.textContent = i === 0 ? h.type : `${h.action} → ${h.type}`;
    trail.appendChild(node);
  }
}

// ── Execute action ────────────────────────────────────────────────
async function executeAction(name, card) {
  card.classList.add("running");
  try {
    const data = await api("/api/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, action: name }),
    });
    render(data);
  } catch (e) {
    alert("Action failed: " + e.message);
  } finally {
    card.classList.remove("running");
  }
}

// ── Plan ──────────────────────────────────────────────────────────
async function loadGoalTypes() {
  try {
    const types = await api("/api/types");
    const select = $("#goal-select");
    select.innerHTML = "";
    for (const t of types) {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      select.appendChild(opt);
    }
  } catch (_) { /* ignore */ }
}

$("#plan-btn").addEventListener("click", async () => {
  const goal = $("#goal-select").value;
  if (!goal || !sessionId) return;

  const result = $("#plan-result");
  result.classList.remove("hidden");
  result.innerHTML = "searching…";

  try {
    const data = await api("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, goal_type: goal }),
    });

    result.innerHTML = "";
    if (data.steps.length === 0) {
      result.textContent = "Already at goal type.";
      return;
    }
    for (let i = 0; i < data.steps.length; i++) {
      if (i > 0) {
        const arrow = document.createElement("span");
        arrow.className = "plan-arrow";
        arrow.textContent = " → ";
        result.appendChild(arrow);
      }
      const step = document.createElement("span");
      step.className = "plan-step";
      step.textContent = data.steps[i].action;
      result.appendChild(step);
    }
  } catch (e) {
    result.textContent = e.message;
  }
});

// ── Reset ─────────────────────────────────────────────────────────
$("#reset-btn").addEventListener("click", () => {
  sessionId = null;
  $("#workspace").classList.add("hidden");
  $("#load-section").classList.remove("hidden");
  $("#plan-result").classList.add("hidden");
  fileInput.value = "";
});
