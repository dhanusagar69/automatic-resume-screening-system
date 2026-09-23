const state = { payload: null, selected: 0 };
const API_BASE = window.__API_BASE_URL__ || "";
document.querySelector("#download-button").href = `${API_BASE}/api/results/download`;

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[char]));
const scoreMax = { ai_project_depth: 40, python_backend: 30, cloud_fullstack: 15, github: 10, engineering_depth: 5 };

function render(payload) {
  state.payload = payload;
  const summary = payload.summary || {};
  document.querySelector("#summary").innerHTML = [
    ["Resumes screened", summary.total_resumes, "batch"],
    ["Eligible", summary.eligible, summary.total_resumes ? `${Math.round(summary.eligible / summary.total_resumes * 100)}% pass` : ""],
    ["Rejected", summary.rejected, "hard filter"],
    ["Unreadable", summary.failed_unreadable, summary.failed_unreadable ? "needs review" : "all parsed"]
  ].map(([label, value, note]) => `<div class="metric"><div class="metric-label">${label}</div><div class="metric-value">${value}<small>${note}</small></div></div>`).join("");

  const eligible = (payload.results || []).filter((candidate) => candidate.eligible);
  document.querySelector("#candidate-list").innerHTML = eligible.map((candidate, index) => `<article class="candidate-card ${index === state.selected ? "active" : ""}" data-index="${index}">
    <div class="rank">#${candidate.rank ?? index + 1}</div><div><div class="candidate-name">${escapeHtml(candidate.candidate_name)}</div><div class="candidate-sub">${(candidate.matched_skills || []).slice(0, 5).map((skill) => `<span class="tag">${escapeHtml(skill)}</span>`).join("")}</div></div><div class="score"><div class="score-number">${candidate.total_score}</div><div class="score-label">/ 100</div></div>
  </article>`).join("");
  document.querySelector("#empty-state").hidden = eligible.length !== 0;
  document.querySelectorAll(".candidate-card").forEach((card) => card.addEventListener("click", () => { state.selected = Number(card.dataset.index); renderDetail(eligible[state.selected]); document.querySelectorAll(".candidate-card").forEach((item) => item.classList.remove("active")); card.classList.add("active"); }));
  renderDetail(eligible[state.selected] || eligible[0]);

  const rejected = (payload.results || []).filter((candidate) => !candidate.eligible);
  document.querySelector("#rejected-count").textContent = rejected.length;
  document.querySelector("#rejected-list").innerHTML = rejected.map((candidate) => `<article class="rejected-card"><div class="rejected-name">${escapeHtml(candidate.candidate_name)}</div><div class="rejected-reason">${(candidate.rejection_reasons || []).map(escapeHtml).join(" · ")}</div></article>`).join("") || `<div class="empty-state">No rejected profiles in this batch.</div>`;
  document.querySelector("#last-run").textContent = `Updated ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

function renderDetail(candidate) {
  const panel = document.querySelector("#detail-panel");
  if (!candidate) { panel.innerHTML = `<p class="eyebrow">CANDIDATE DETAIL</p><h2 class="detail-title">Nothing to review yet.</h2><p class="detail-summary">Add resumes to the folder and run screening to see evidence here.</p>`; return; }
  const rows = Object.entries(candidate.score_breakdown || {}).map(([key, value]) => `<div class="breakdown-row"><div>${key.replaceAll("_", " ")}<div class="bar"><i style="width:${Math.min(100, value / scoreMax[key] * 100)}%"></i></div></div><b>${value}</b></div>`).join("");
  panel.innerHTML = `<p class="eyebrow">CANDIDATE #${candidate.rank}</p><h2 class="detail-title">${escapeHtml(candidate.candidate_name)}</h2><div class="detail-file">${escapeHtml(candidate.source_file)}</div><p class="detail-summary">${escapeHtml(candidate.project_summary)}</p><div class="breakdown">${rows}</div><div class="evidence"><div class="evidence-title">Resume evidence</div>${(candidate.evidence || []).slice(0, 2).map((line) => `<p>${escapeHtml(line)}</p>`).join("")}</div>`;
}

async function loadResults() { const response = await fetch(`${API_BASE}/api/results`, { cache: "no-store" }); render(await response.json()); }
async function runScreening() { const button = document.querySelector("#run-button"); const archive = document.querySelector("#archive-input").files[0]; const body = archive ? (() => { const form = new FormData(); form.append("archive", archive); return form; })() : undefined; button.disabled = true; button.innerHTML = "Screening..."; try { render(await (await fetch(`${API_BASE}/api/screen`, { method: "POST", body })).json()); } finally { button.disabled = false; button.innerHTML = '<span class="play-icon">▶</span> Run screening'; } }
function updateFileStatus() { const input = document.querySelector("#archive-input"); const status = document.querySelector("#file-status"); const clear = document.querySelector("#clear-file"); const file = input.files[0]; status.textContent = file ? file.name : "No file selected"; status.classList.toggle("has-file", Boolean(file)); clear.hidden = !file; }
document.querySelector("#run-button").addEventListener("click", runScreening);
document.querySelector("#archive-input").addEventListener("change", updateFileStatus);
document.querySelector("#clear-file").addEventListener("click", () => { document.querySelector("#archive-input").value = ""; updateFileStatus(); });
loadResults().catch(() => { document.querySelector("#detail-panel").innerHTML = `<p class="eyebrow">SERVER OFFLINE</p><h2 class="detail-title">Start the dashboard server.</h2><p class="detail-summary">Run <strong>py web_server.py</strong> from the project folder, then refresh this page.</p>`; });
