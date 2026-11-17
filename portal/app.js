"use strict";
// ETRM Knowledge Agent portal: a static page (GitHub Pages) over the repo's data, plus live chat
// against the hosted API when one is configured. The client switch here is a simulated login;
// in the agent itself, isolation is enforced server-side (session tenant + Postgres RLS).

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const md = (s) => DOMPurify.sanitize(marked.parse(String(s ?? "")));
const SHARED = "consultancy";
const OUTCOME_LABEL = { answered: "answered", declined: "declined", out_of_scope: "out of scope", no_information: "doesn't know" };
const CLASS_LABEL = { public: "public", insight: "insight", inference_only: "inference-only", pii: "PII (masked)" };
const METRICS = [
  ["retrieval_hit_at_k", "Retrieval hit@6"], ["retrieval_mrr", "Retrieval MRR"], ["must_include", "Expected value present"],
  ["must_not_include", "No forbidden values"], ["outcome_correct", "Correct outcome"], ["cited_expected_doc", "Cited the right document"],
];
const GATES = [["leakage", "Cross-client leakage"], ["pii", "PII in the answer"], ["inference_only", "Internal text quoted"], ["system_prompt_or_injection", "System prompt / injection"]];

const S = { cfg: {}, clients: [], docs: [], rec: null, hist: null, client: null, token: null, history: [], apiReady: false };
const store = { get(k) { try { return localStorage.getItem(k); } catch { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } } };

async function getJSON(path) { const r = await fetch(path, { cache: "no-cache" }); if (!r.ok) throw new Error(path); return r.json(); }

async function init() {
  [S.cfg, S.clients, S.docs, S.rec, S.hist] = await Promise.all(
    ["config", "clients", "docs", "recorded-answers", "history"].map((n) => getJSON(`data/${n}.json`)));
  $("#repo-link").href = S.cfg.repo;
  const sel = $("#client");
  S.clients.filter((c) => c.id !== SHARED).forEach((c) => sel.add(new Option(c.name, c.id)));
  const saved = store.get("client");
  if (saved && S.clients.some((c) => c.id === saved)) sel.value = saved;
  sel.addEventListener("change", () => switchClient(sel.value));
  $$(".tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal" || e.target.classList.contains("close")) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); });
  $("#ask").addEventListener("submit", (e) => { e.preventDefault(); ask($("#question").value); });
  $("#question").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask($("#question").value); } });
  $("#doc-filter").addEventListener("input", renderDocList);
  ["#rec-suite", "#rec-outcome", "#rec-search"].forEach((id) => $(id).addEventListener("input", renderRecorded));
  renderReport(); renderAbout(); setupRecordedFilters();
  await switchClient(sel.value);
  const hash = location.hash.slice(1);
  if (["chat", "docs", "recorded", "report", "about"].includes(hash)) showTab(hash);
  wakeBackend();
}

function showTab(name) {
  $$(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  $$(".tab").forEach((t) => t.classList.toggle("active", t.id === `tab-${name}`));
  history.replaceState(null, "", `#${name}`);
}

const visibleDocs = () => S.docs.filter((d) => d.tenant_id === S.client || d.tenant_id === SHARED);
const clientOf = (id) => S.clients.find((c) => c.id === id);

async function switchClient(id) {
  S.client = id; S.token = null; S.history = [];
  store.set("client", id);
  $("#messages").innerHTML = "";
  $("#question").placeholder = `Ask ${clientOf(id).company}'s assistant about your trading operations…`;
  $("#doc-view").innerHTML = `<p class="muted">Pick a document. As ${esc(clientOf(id).name)} you see only your own documents plus the shared consultancy guidance.</p>`;
  renderDocList(); renderSuggestions(); renderRecorded();
  if (S.apiReady) await login();
}

/* ---------- live backend ---------- */
async function api(path, opts = {}) {
  const r = await fetch(S.cfg.apiUrl + path, { ...opts, headers: { "Content-Type": "application/json", ...(S.token ? { Authorization: `Bearer ${S.token}` } : {}), ...(opts.headers || {}) } });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) { const e = new Error(body.detail ? (typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail)) : `HTTP ${r.status}`); e.status = r.status; throw e; }
  return body;
}

function status(text, kind = "") { const el = $("#chat-status"); el.className = `status ${kind}`; el.innerHTML = text; }

async function wakeBackend() {
  if (!S.cfg.apiUrl) {
    status(`Live chat is coming soon. Until then, browse <a href="#recorded" onclick="showTab('recorded')">242 recorded answers</a> from the real agent (same questions, refusals and leak attempts), or <a href="${esc(S.cfg.repo)}/blob/main/docs/RUN-LOCALLY.md" target="_blank" rel="noopener">run it locally</a> with one command.`, "warn");
    $("#quota").textContent = "recorded answers mode"; $("#quota").className = "pill low"; $("#send").disabled = true; return;
  }
  status("Connecting to the live agent… The free hosting sleeps when idle, so the first visit can take a minute or two.", "warn");
  const started = Date.now();
  while (Date.now() - started < 240000) {
    try {
      const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), 15000);
      const r = await fetch(S.cfg.apiUrl + "/health", { signal: ctl.signal }); clearTimeout(t);
      if (r.ok) { S.apiReady = true; status("● Live agent connected", "good"); await login(); await refreshQuota(); return; }
    } catch { /* still waking */ }
    await new Promise((res) => setTimeout(res, 8000));
  }
  status(`The live agent didn't wake up. Try again in a minute, or browse the <a href="#recorded" onclick="showTab('recorded')">recorded answers</a>.`, "bad");
}

async function login() {
  try { S.token = (await api("/login", { method: "POST", body: JSON.stringify({ client_id: S.client }) })).token; }
  catch (e) { status(`Couldn't sign in to the live agent: ${esc(e.message)}`, "bad"); }
}

async function refreshQuota() { try { setQuota(await api("/quota")); } catch { setQuota(null); } }

function setQuota(q) {
  const el = $("#quota");
  if (!q) { el.textContent = "live chat offline"; el.className = "pill out"; return; }
  const reset = new Date(q.resets_at);
  const hrs = Math.max(0, Math.ceil((reset - Date.now()) / 3600000));
  if (q.limit === 0) { el.textContent = "unlimited questions"; el.className = "pill"; return; }
  el.textContent = `${q.remaining} of ${q.limit} questions left today · resets 00:00 UTC (in ~${hrs}h)`;
  el.className = `pill ${q.remaining === 0 ? "out" : q.remaining <= q.limit * 0.2 ? "low" : ""}`;
  $("#send").disabled = q.remaining === 0;
}

function addMsg(kind, html) { const d = document.createElement("div"); d.className = `msg ${kind}`; d.innerHTML = html; $("#messages").append(d); d.scrollIntoView({ block: "end" }); return d; }

async function ask(text) {
  const q = text.trim();
  if (!q || $("#send").disabled) return;
  if (!S.apiReady || !S.token) { addMsg("err", "The live agent isn't connected yet. Wait for the green dot, or browse the recorded answers."); return; }
  $("#question").value = ""; addMsg("user", esc(q));
  const pending = addMsg("bot", '<span class="muted">Searching your documents…</span>');
  $("#send").disabled = true;
  try {
    const r = await api("/chat", { method: "POST", body: JSON.stringify({ question: q, history: S.history.slice(-6) }) });
    S.history.push({ role: "user", content: q }, { role: "assistant", content: r.answer });
    pending.innerHTML = `${md(r.answer)}<div class="meta"><span class="badge ${esc(r.outcome)}">${esc(OUTCOME_LABEL[r.outcome] || r.outcome)}</span>${r.citations.map((c) => `<button class="cite" data-doc="${esc(c.doc_id)}">📄 ${esc(c.title)} (${esc(c.doc_id)})</button>`).join("")}<span>trace ${esc(r.trace_id.slice(0, 8))}</span></div>`;
    $$(".cite", pending).forEach((b) => b.addEventListener("click", () => openDoc(b.dataset.doc, true)));
    setQuota(r.quota);
  } catch (e) {
    pending.className = "msg err";
    pending.textContent = e.status === 429 ? e.message : e.status === 401 ? "Your session expired; switching client signs you in again." : `Something went wrong: ${e.message}`;
    if (e.status === 401) await login();
    await refreshQuota();
  } finally { if ($("#quota").className.indexOf("out") < 0) $("#send").disabled = false; }
}

function renderSuggestions() {
  const mine = S.rec.answers.filter((a) => a.tenant_id === S.client && !(a.history || []).length && !a.question.includes("I have been reading"));
  const pick = (suite, pred = () => true) => mine.find((a) => a.suite === suite && pred(a));
  const qs = [
    pick("golden", (a) => a.checks.must_include && a.outcome === "answered"),
    pick("overlap"), pick("leakage"), pick("pii_inference"),
    pick("adversarial", (a) => /recipe|python/i.test(a.question)),
  ].filter(Boolean).map((a) => a.question);
  $("#suggestions").innerHTML = qs.map((q) => `<button type="button">${esc(q)}</button>`).join("");
  $$("#suggestions button").forEach((b) => b.addEventListener("click", () => { $("#question").value = b.textContent; $("#question").focus(); }));
}

/* ---------- documents ---------- */
function renderDocList() {
  const f = $("#doc-filter").value.toLowerCase();
  const docs = visibleDocs().filter((d) => !f || `${d.doc_id} ${d.title} ${d.doc_type} ${d.body}`.toLowerCase().includes(f));
  const group = (title, list) => list.length ? `<div class="doc-group">${esc(title)} · ${list.length}</div>` + list.map((d) => `
    <button class="doc-item" data-doc="${esc(d.doc_id)}"><b>${esc(d.title)}</b>
      <span class="row"><span>${esc(d.doc_id)}</span><span class="badge ${esc(d.data_class)}">${esc(CLASS_LABEL[d.data_class])}</span>${d.status !== "current" ? `<span class="badge superseded">${esc(d.status)}</span>` : ""}${d.contradicts ? `<span class="badge">contradicts ${esc(d.contradicts)}</span>` : ""}</span>
    </button>`).join("") : "";
  $("#doc-list").innerHTML = group(clientOf(S.client).company, docs.filter((d) => d.tenant_id === S.client)) + group("Shared consultancy guidance", docs.filter((d) => d.tenant_id === SHARED));
  $$(".doc-item").forEach((b) => b.addEventListener("click", () => openDoc(b.dataset.doc)));
}

const CLASS_NOTE = {
  public: "Quotable. The agent may cite and quote it.",
  insight: "Quotable summary. The agent may cite and paraphrase it.",
  inference_only: "Internal. The agent may use it for reasoning but must never quote or cite it; the output guard blocks verbatim overlap.",
  pii: "Contact list. It never reaches the model; names, emails and numbers are masked at ingestion (shown masked here too).",
};

function docHTML(d) {
  return `<div class="doc-head"><span class="badge ${esc(d.data_class)}">${esc(CLASS_LABEL[d.data_class])}</span>
    <span>${esc(d.doc_id)} · ${esc(d.doc_type || "")} · effective ${esc(d.effective_date)}</span>
    ${d.status !== "current" ? `<span class="badge superseded">${esc(d.status)}</span>` : ""}
    ${d.supersedes ? `<span>supersedes ${esc(d.supersedes)}</span>` : ""}${d.contradicts ? `<span>contradicts ${esc(d.contradicts)}</span>` : ""}
    <a href="${esc(d.source)}" target="_blank" rel="noopener">source ↗</a></div>
    <div class="note">${esc(CLASS_NOTE[d.data_class])}</div>${md(d.body)}`;
}

function openDoc(id, modal = false) {
  const d = visibleDocs().find((x) => x.doc_id === id);
  if (!d) { const html = `<p>Document <b>${esc(id)}</b> isn't visible to ${esc(clientOf(S.client).name)}.</p>`; return modal ? showModal(html) : ($("#doc-view").innerHTML = html); }
  if (modal) return showModal(docHTML(d));
  $("#doc-view").innerHTML = docHTML(d);
  $$(".doc-item").forEach((b) => b.classList.toggle("active", b.dataset.doc === id));
}
function showModal(html) { $("#modal-body").innerHTML = html; $("#modal").hidden = false; }
function closeModal() { $("#modal").hidden = true; }

/* ---------- recorded answers ---------- */
function setupRecordedFilters() {
  const m = S.rec.meta;
  $("#recorded-meta").innerHTML = `Real answers from the full eval run of ${esc(m.timestamp.slice(0, 10))} (model <code>${esc(m.answer_model)}</code>, prompt <code>${esc(m.prompt_version)}</code>, KB <code>${esc(m.kb_version)}</code>), filtered to the signed-in client. Every answer was checked by the four hard gates.`;
  [...new Set(S.rec.answers.map((a) => a.suite))].sort().forEach((s) => $("#rec-suite").add(new Option(s, s)));
  Object.entries(OUTCOME_LABEL).forEach(([k, v]) => $("#rec-outcome").add(new Option(v, k)));
}

function renderRecorded() {
  const suite = $("#rec-suite").value, outcome = $("#rec-outcome").value, q = $("#rec-search").value.toLowerCase();
  const list = S.rec.answers.filter((a) => a.tenant_id === S.client && (!suite || a.suite === suite) && (!outcome || a.outcome === outcome)
    && (!q || `${a.question} ${a.answer}`.toLowerCase().includes(q)));
  $("#recorded").innerHTML = `<p class="muted">${list.length} answers</p>` + list.slice(0, 200).map((a) => {
    const gates = Object.keys(a.gate_failures || {});
    const ok = Object.values(a.checks || {}).every(Boolean);
    const hist = (a.history || []).map((t) => `${t.role === "user" ? "Q" : "A"}: ${esc(t.content)}`).join("<br>");
    return `<div class="rec">${hist ? `<div class="hist">${hist}</div>` : ""}<div class="q">${esc(a.question.length > 400 ? "…" + a.question.slice(-200) : a.question)}</div>
      <div class="a">${esc(a.answer)}</div>
      <div class="meta"><span class="badge">${esc(a.suite)}</span><span class="badge ${esc(a.outcome)}">${esc(OUTCOME_LABEL[a.outcome] || a.outcome)}</span>
      <span class="badge ${ok ? "pass" : "fail"}">${ok ? "checks passed" : "check missed"}</span>
      <span class="badge ${gates.length ? "fail" : "pass"}">${gates.length ? "gate failed: " + esc(gates.join(", ")) : "gates: 0 failures"}</span>
      ${(a.cited || []).map((c) => `<button class="cite" data-doc="${esc(c)}">📄 ${esc(c)}</button>`).join("")}</div></div>`;
  }).join("");
  $$("#recorded .cite").forEach((b) => b.addEventListener("click", () => openDoc(b.dataset.doc, true)));
}

/* ---------- report ---------- */
const f3 = (v) => (v === null || v === undefined ? "n/a" : Number(v).toFixed(3));

function renderReport() {
  const [full, regBase, latest] = S.hist.runs;
  const gates = latest.summary.hard_gate_failures || {};
  const floors = (S.hist.floors && S.hist.floors.regression) || {};
  const delta = (k) => { const a = regBase.summary.overall[k], b = latest.summary.overall[k]; if (a == null || b == null) return ""; const d = b - a; return d === 0 ? '<span class="delta">±0</span>' : `<span class="delta ${d > 0 ? "up" : "down"}">${d > 0 ? "+" : ""}${d.toFixed(3)}</span>`; };
  $("#report").innerHTML = `
    <h2>Hard gates on the latest run</h2>
    <p class="muted">Checked deterministically on every answer, whatever the suite. Any failure blocks a merge. ${esc(latest.label)}, ${esc(latest.timestamp.slice(0, 10))}, ${latest.summary.overall.n} items.</p>
    <div class="cards">${GATES.map(([k, l]) => `<div class="card"><div class="big ${gates[k] ? "" : "zero"}">${gates[k] ?? 0}</div><div class="lbl">${esc(l)}</div></div>`).join("")}</div>
    <h2>Quality: is it improving?</h2>
    <p class="muted">The regression subset is frozen, so these numbers are comparable run to run. Floors only ever go up.</p>
    <div class="cards">${METRICS.slice(2).map(([k, l]) => `<div class="card"><div class="big">${f3(latest.summary.overall[k])}</div><div class="lbl">${esc(l)}</div>${delta(k)} <span class="lbl">vs baseline ${f3(regBase.summary.overall[k])}</span></div>`).join("")}</div>
    <table class="grid"><tr><th>Metric</th><th>Full baseline (${full.summary.overall.n})</th><th>Regression baseline (${regBase.summary.overall.n})</th><th>Latest run (${latest.summary.overall.n})</th><th>Change</th><th>Floor</th></tr>
      ${METRICS.map(([k, l]) => `<tr><td>${esc(l)}</td><td>${f3(full.summary.overall[k])}</td><td>${f3(regBase.summary.overall[k])}</td><td><b>${f3(latest.summary.overall[k])}</b></td><td>${delta(k)}</td><td>${floors[k] != null ? f3(floors[k]) : "n/a"}</td></tr>`).join("")}</table>
    <h2>By suite (latest run)</h2>
    <table class="grid"><tr><th>Suite</th><th>n</th><th>hit@6</th><th>MRR</th><th>Expected value</th><th>Outcome</th><th>Cited</th></tr>
      ${Object.entries(latest.summary.by_suite).map(([s, m]) => `<tr><td>${esc(s)}</td><td>${m.n}</td><td>${f3(m.retrieval_hit_at_k)}</td><td>${f3(m.retrieval_mrr)}</td><td>${f3(m.must_include)}</td><td>${f3(m.outcome_correct)}</td><td>${f3(m.cited_expected_doc)}</td></tr>`).join("")}</table>
    <h2>What changed, and why</h2>
    <div class="timeline">${S.hist.timeline.map((t) => `<div><b>${esc(t.date)} · ${esc(t.what)}</b><span class="muted">${esc(t.detail)}</span></div>`).join("")}</div>
    <h2>Full eval report</h2>
    <details class="md"><summary>Iteration 1 report: methodology, misses and what to try next</summary><div id="report-md" class="doc-view" style="border:0;padding:8px 0">Loading…</div></details>`;
  fetch("data/report.md").then((r) => r.text()).then((t) => { $("#report-md").innerHTML = md(t); }).catch(() => {});
}

/* ---------- about ---------- */
function renderAbout() {
  const R = S.cfg.repo, G = `${R}/blob/main/docs/governance`;
  const link = (href, title, text) => `<a class="card" href="${esc(href)}" target="_blank" rel="noopener"><b>${esc(title)} ↗</b><div class="lbl">${esc(text)}</div></a>`;
  $("#about").innerHTML = `
    <h2>What this is</h2>
    <p>One RAG assistant serving three fictional ETRM clients (a gas and power utility, a refined-products trader and an agri trader) plus a shared consultancy knowledge base. Their topics overlap on purpose, with different facts, to tempt the agent into blending clients' answers. It doesn't, and every change is scored before it ships.</p>
    <ul>
      <li><b>Isolation in the data layer:</b> the tenant comes from the session only; SQL filter plus Postgres FORCE row-level security.</li>
      <li><b>Data classes:</b> public, insight, inference-only (reason but never quote) and PII (never sent to the model).</li>
      <li><b>Cite or abstain:</b> answers cite sources; weak retrieval means "I don't know" without calling the model.</li>
      <li><b>Evaluated:</b> 242 frozen cases, 4 zero-tolerance hard gates, floors that only go up.</li>
      <li><b>Traced:</b> Langfuse traces with client, chunks and scores, versions, tokens and cost; PII masked.</li>
    </ul>
    <h2>Code and documents</h2>
    <div class="links">
      ${link(R, "Agent repository", "Source, tests, CI, evals and the governance pack")}
      ${link(`${R}/blob/main/docs/RUN-LOCALLY.md`, "Run it locally", "Git + Docker Desktop + an Anthropic key, one command")}
      ${link("https://github.com/ICSmartBanana/agent-standards", "Standards pack", "Principles, review gates, playbooks, Claude Code skills")}
      ${link("https://github.com/ICSmartBanana/agent-project-template", "Project template", "Start the next agent with all of this wired in")}
      ${link(`${R}/blob/main/docs/evals/iteration-1-report.md`, "Eval report", "Iteration 1 baseline, misses and next steps")}
      ${link(`${R}/blob/main/docs/decisions/0001-stack.md`, "ADR 0001", "Stack, isolation design and budget")}
      ${link(`${G}/use-case-classification.md`, "EU AI Act classification", "Limited risk, Art. 50 disclosure")}
      ${link(`${G}/risk-register.md`, "Risk register", "Each risk with an owner, a mitigation and live tests")}
      ${link(`${G}/model-card.md`, "Model card", "Purpose, limits, evaluation, change history")}
      ${link(`${G}/data-source-register.md`, "Data-source register", "Knowledge bases, data classes, deliberate messiness")}
      ${link(`${G}/human-oversight.md`, "Human oversight", "Who checks what, and when")}
      ${link(`${G}/incident-process.md`, "Incident process", "Report, contain, notify, review")}
      ${link(`${G}/regulatory-register.md`, "Regulatory register", "EU, US states, UK, Australia, India")}
      ${link(`${R}/actions`, "CI runs", "Quality, security, governance and eval gates")}
    </div>
    <h2>About this hosted demo</h2>
    <p class="muted">The page is static (GitHub Pages). Live chat calls a small hosted backend that runs the same agent and database. The Anthropic key stays on the server. The backend accepts browser calls only from this site, rate-limits each visitor, and shares a daily question allowance across everyone, shown at the top and reset at 00:00 UTC. Off-topic questions are answered with "I don't know" without calling the model. The client switch is a simulated login, as in the POC.</p>`;
}

init().catch((e) => { document.body.insertAdjacentHTML("afterbegin", `<p style="padding:20px;color:#b91c1c">Failed to load the portal data: ${esc(e.message)}</p>`); });
