// As Prescribed: the therapist's review desk. Plain JS, no build step, no third-party requests.
"use strict";

const STATE_LABEL = {
  supported: "Supported", conflict: "Conflict: therapist decides",
  proposal: "Proposal: not prescribed as stated", uncertain_translation: "Uncertain translation",
};
const KIND_LABEL = {
  wrong_dose: "Dose differs from the session", wrong_frequency: "How often differs from the session",
  wrong_side: "Side differs from the session", invented_item: "Not prescribed in the session",
  dropped_caution: "The therapist's caution is missing", not_entailed: "Not stated in the session",
  mistranslation: "Translation differs", rule_conflict: "Documented restriction",
  incomplete: "Incomplete prescription", no_catalogue_match: "Not in the exercise catalogue",
};
const SOURCE_LABEL = { checks: "deterministic check", rules: "rule engine", falsifier: "falsifier model" };
const LANG = { ar: "Arabic", uk: "Ukrainian", en: "English" };
const SPEED = Number(new URLSearchParams(location.search).get("speed")) || 15;

const $ = (s) => document.querySelector(s);
const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") n.className = v; else if (k === "text") n.textContent = v; else n.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids) if (kid !== null && kid !== undefined) n.append(kid);
  return n;
};

const state = { sessions: [], session: null, mode: "live", injection: "", es: null, result: null,
                decisions: {}, acks: {}, steps: [], loadSeq: 0 };

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

// ---------- session and transcript ----------
async function init() {
  state.sessions = await getJSON("/api/sessions");
  const demo = await getJSON("/api/demo");
  if (demo.replay && demo.recording) {
    const r = demo.recording;
    $("#replay-note").textContent = `This public demo runs no model: it replays real runs recorded on ${day(r.date)} `
      + `on AMD Radeon GPUs, ${r.generator.name} on a ${r.generator.gpu.replace(/^AMD /, "")} drafting and `
      + `${r.falsifier.name} on a ${r.falsifier.gpu.replace(/^AMD /, "")} checking.`;
    $("#replay-note").hidden = false;
  }
  const seg = $("#sessions");
  for (const s of state.sessions) {
    const b = el("button", { type: "button", "aria-pressed": "false", text: `${s.id} · ${LANG[s.language]}`,
                             title: s.demonstrates });
    b.addEventListener("click", () => selectSession(s.id));
    seg.append(b);
  }
  $("#mode-live").addEventListener("click", () => setMode("live"));
  $("#mode-rx").addEventListener("click", () => setMode("prescription"));
  $("#injection").addEventListener("change", (e) => { state.injection = e.target.value; });
  $("#run").addEventListener("click", run);
  $("#approve-supported").addEventListener("click", approveSupported);
  $("#release").addEventListener("click", release);
  await selectSession(state.sessions[0].id);
}

async function selectSession(id) {
  stopRun();
  $("#run").disabled = true;  // no run until this session's data has loaded
  const seq = ++state.loadSeq;
  const detail = await getJSON(`/api/sessions/${id}`);
  if (seq !== state.loadSeq) return;  // a later click won
  state.session = detail;
  stopRun();
  document.querySelectorAll("#sessions button").forEach((b) => b.setAttribute("aria-pressed", String(b.textContent.startsWith(id + " "))));
  const p = state.session.profile;
  $("#profile").textContent = `${p.id} · patient language ${LANG[state.session.language]}. ${p.summary}`;
  $("#conditions").replaceChildren(...p.conditions.map((c) => el("li", { text: c.en })));
  const sel = $("#injection");
  sel.replaceChildren(el("option", { value: "", text: "No error injected" }),
    ...state.session.injections.map((i) => el("option", { value: i.id, text: `${i.id} · ${i.label}: ${i.detail}` })));
  state.injection = "";
  resetResult();
  renderTranscript(state.mode === "live" ? [] : state.session.transcript);
}

function setMode(mode) {
  stopRun();
  state.mode = mode;
  $("#mode-live").setAttribute("aria-pressed", String(mode === "live"));
  $("#mode-rx").setAttribute("aria-pressed", String(mode === "prescription"));
  $("#injection").hidden = mode !== "prescription";
  $("#run").textContent = mode === "live" ? "Start the visit" : "Verify the prescription";
  resetResult();
  renderTranscript(mode === "live" ? [] : state.session.transcript);
}

function spanNode(s, fresh) {
  return el("div", { class: `span ${s.speaker}${fresh ? " new" : ""}`, id: `span-${s.span_id}` },
    el("span", { class: "sid", text: s.span_id }), el("span", { class: "who", text: s.speaker === "therapist" ? "T" : "P" }),
    el("span", { text: s.text }));
}

function renderTranscript(spans) {
  const t = $("#transcript");
  t.replaceChildren(...spans.map((s) => spanNode(s, false)));
  if (!spans.length) t.append(el("p", { class: "muted small", id: "t-empty",
    text: state.mode === "live" ? "The session appears here as it happens." : "" }));
}

function highlight(ids, on) {
  for (const id of ids) document.getElementById(`span-${id}`)?.classList.toggle("hl", on);
}

// ---------- running ----------
function stopRun() {
  if (state.es) { state.es.close(); state.es = null; }
  $("#run").disabled = false;
}

function resetResult() {
  state.result = null; state.decisions = {}; state.acks = {}; state.steps = [];
  $("#lines").replaceChildren(el("p", { class: "muted small",
    text: state.mode === "live" ? "Start the visit to see the program build as the session goes."
                                : "Verify the approved prescription, or inject an error first and see whether it is caught." }));
  $("#banner").replaceChildren(); $("#facts").replaceChildren(); $("#progress").replaceChildren();
  $("#heard-panel").hidden = true;
  updateRelease();
}

function step(name, status = "now") {
  for (const s of state.steps) if (s.status === "now") s.status = "done";
  const existing = state.steps.find((s) => s.name === name);
  if (existing) existing.status = status; else state.steps.push({ name, status });
  $("#progress").replaceChildren(...state.steps.map((s) => el("span", { class: `step ${s.status}`, text: s.name })));
}

function run() {
  stopRun(); resetResult();
  if (state.mode === "live") renderTranscript([]);
  const q = new URLSearchParams({ mode: state.mode, speed: String(SPEED) });
  if (state.mode === "prescription" && state.injection) q.set("injection", state.injection);
  const es = new EventSource(`/api/sessions/${state.session.id}/run?${q}`);
  state.es = es;
  $("#run").disabled = true;
  step(state.mode === "live" ? "Visit in progress" : "Approved prescription loaded");
  const on = (kind, fn) => es.addEventListener(kind, (e) => fn(JSON.parse(e.data)));
  on("span", (s) => {
    $("#t-empty")?.remove();
    const node = spanNode(s, true);
    $("#transcript").append(node);
    node.scrollIntoView({ block: "nearest" });
  });
  on("items", (d) => renderDraft(d.items, d.upto));
  on("queued", (d) => banner("info", d.message));
  on("stage", (d) => stage(d));
  on("result", (d) => { state.result = d; step("Ready for approval", "done"); renderResult(); });
  on("failure", (d) => { banner("warn", d.message); step("Stopped", "done"); });
  on("end", () => stopRun());
  es.onerror = () => { if (state.es) { banner("warn", "The connection to the server was lost."); stopRun(); } };
}

function stage(d) {
  const r = d.round !== undefined ? `Round ${d.round}: ` : "";
  const name = {
    visit_ended: "Visit ended", extracted: "Program extracted", round: `Round ${d.round}`,
    checked: `${r}fidelity checked`, translated: `${r}translated`, back_checked: `${r}back-translated`,
    round_done: `${r}${d.correctable} objection(s) to correct`, corrected: `${r}generator corrected`,
  }[d.stage];
  if (name) step(name);
}

function renderDraft(items, upto) {
  step("Drafting during the visit");
  const shown = items.filter((i) => i.status === "prescribed");
  $("#lines").replaceChildren(el("p", { class: "small muted", text: `Draft after ${upto}: ${shown.length} item(s). Verification starts when the visit ends.` }),
    ...shown.map((i) => el("div", { class: "draft", text:
      `${i.exercise}${i.side ? ` (${i.side})` : ""}: ${i.dose || "dose not stated"}, ${i.frequency || "how often not stated"}` })));
}

function banner(kind, text) {
  $("#banner").replaceChildren(el("div", { class: `banner ${kind}`, role: "status", text }));
}

function day(iso) {
  return new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

// A recorded run always says so, and names the models and GPUs it was recorded on.
function recordedText(d) {
  const r = d.recording;
  const origin = r ? ` Recorded on ${day(r.date)}: ${r.generator.name} on an ${r.generator.gpu} drafted, `
    + `${r.falsifier.name} on an ${r.falsifier.gpu} checked (${r.runtime}).` : "";
  return (d.replay ? "A recorded run, replayed: no model runs on this public demo."
    : "The model endpoint did not answer: this is a recorded run, shown as recorded.") + origin;
}

// The model name, with the GPU when this is a recorded run made on that model.
function modelFact(d, role) {
  const name = d.models[role] || "-";
  const r = d.recording && d.recording[role];
  return d.recorded && r && r.model === name ? `${name} · ${r.gpu}` : name;
}

// ---------- the result ----------
function renderResult() {
  const d = state.result;
  const facts = [];
  if (d.latency_after_last_chunk_s !== undefined) facts.push(["Ready after the visit", `${d.latency_after_last_chunk_s} s`]);
  if (d.seconds !== undefined) facts.push(["Verification", `${d.seconds} s`]);
  facts.push(["Rounds", String(d.summary.rounds)]);
  for (const [role, tps] of Object.entries(d.tokens_per_s || {})) facts.push([`${role} tok/s`, String(tps)]);
  facts.push(["Generator", modelFact(d, "generator")], ["Falsifier", modelFact(d, "falsifier")]);
  const bars = el("span", { class: "bars", title: "Objections to correct, per round" },
    ...d.summary.objections_per_round.map((n) => { const b = el("span"); b.style.height = `${Math.max(2, n * 5)}px`; return b; }));
  $("#facts").replaceChildren(...facts.map(([k, v]) => el("span", {}, `${k} `, el("b", { text: v }))),
    el("span", {}, "Objections per round ", bars, ` ${d.summary.objections_per_round.join(" → ")}`));
  if (d.recorded) banner(d.replay ? "info" : "warn", recordedText(d));
  else if (d.cached_at) banner("info", `Served from a run at ${new Date(d.cached_at * 1000).toLocaleTimeString()} (identical case).`);
  if (d.injection) renderInjection(d.injection);
  renderLines();
  const heard = d.heard_not_prescribed || [];
  $("#heard-panel").hidden = !heard.length;
  $("#heard").replaceChildren(...heard.map((i) => el("li", { text: `${i.exercise} (${i.status}) · ${i.source_span_ids.join(", ")}` })));
}

function renderInjection(inj) {
  const o = inj.observation;
  if (!o.injected) { banner("warn", `${inj.label}: the mutation found nothing to change in this translation, so it was not injected.`); return; }
  const by = [o.by_falsifier && "the falsifier model", o.by_checks && "a deterministic check or rule"].filter(Boolean).join(" and ");
  const text = o.detected
    ? `Injected: ${inj.label} (${inj.detail}). Caught before any correction by ${by}. Final state: ${o.final_state}.`
    : `Injected: ${inj.label} (${inj.detail}). Not caught before correction. Final state: ${o.final_state}. A miss is shown as it is.`;
  $("#banner").append(el("div", { class: `banner ${o.detected ? "caught" : "missed"}`, role: "status", text }));
}

function renderLines() {
  const lines = state.result.lines;
  $("#lines").replaceChildren(...lines.map(lineNode));
  updateRelease();
}

function lineNode(line) {
  const name = (line.source_en.split(". ")[0] || line.item_id).replace(/\.$/, "");
  const decision = state.decisions[line.item_id];
  const card = el("article", { class: `line s-${line.state}${decision === "remove" ? " removed" : ""}` });
  card.append(el("div", { class: "head" }, el("span", { class: `chip ${line.state}`, text: STATE_LABEL[line.state] }),
    el("span", { class: "name", text: name })));
  const marker = el("div", { class: `marker${line.span_ids.length ? "" : " none"}` });
  if (line.span_ids.length) {
    marker.append("Prescribed by therapist:");
    for (const id of line.span_ids) {
      const b = el("button", { type: "button", text: id, title: "Show in the transcript" });
      b.addEventListener("mouseenter", () => highlight([id], true));
      b.addEventListener("mouseleave", () => highlight([id], false));
      b.addEventListener("click", () => document.getElementById(`span-${id}`)?.scrollIntoView({ block: "center" }));
      marker.append(b);
    }
  } else marker.append("No transcript span: not prescribed by the therapist");
  card.append(marker);
  card.addEventListener("mouseenter", () => highlight(line.span_ids, true));
  card.addEventListener("mouseleave", () => highlight(line.span_ids, false));
  card.append(el("p", { class: "en", text: line.source_en }));
  card.append(el("p", { class: "pl", lang: line.language, dir: line.language === "ar" ? "rtl" : "ltr", text: line.text || "(no translation)" }));
  if (line.back_translation) card.append(el("p", { class: "back", text: `Back-translated by the falsifier: ${line.back_translation}` }));
  const objs = line.objections.filter((o) => o.blocking || o.kind === "no_catalogue_match");
  if (objs.length) card.append(el("ul", { class: "objs" }, ...objs.map((o) =>
    el("li", {}, el("span", { class: "src", text: SOURCE_LABEL[o.source] || o.source }),
      el("span", {}, el("b", { text: `${KIND_LABEL[o.kind] || o.kind}. ` }), o.detail)))));
  card.append(decisionNode(line));
  return card;
}

function decisionNode(line) {
  const d = state.decisions[line.item_id];
  const wrap = el("div", { class: "decide" });
  const needsAck = line.state === "conflict";
  const approve = el("button", { type: "button", class: "approve", "aria-pressed": String(d === "approve"),
    text: needsAck ? "Keep this line (my decision)" : "Approve" });
  const remove = el("button", { type: "button", class: "remove", "aria-pressed": String(d === "remove"), text: "Remove" });
  approve.disabled = needsAck && !state.acks[line.item_id];
  approve.addEventListener("click", () => { state.decisions[line.item_id] = d === "approve" ? undefined : "approve"; renderLines(); });
  remove.addEventListener("click", () => { state.decisions[line.item_id] = d === "remove" ? undefined : "remove"; renderLines(); });
  if (needsAck) {
    const box = el("input", { type: "checkbox", id: `ack-${line.item_id}`, checked: !!state.acks[line.item_id] });
    box.addEventListener("change", () => { state.acks[line.item_id] = box.checked; if (!box.checked && d === "approve") delete state.decisions[line.item_id]; renderLines(); });
    wrap.append(el("label", { for: `ack-${line.item_id}` }, box, "I have read the documented restriction"));
  }
  wrap.append(approve, remove);
  return wrap;
}

function approveSupported() {
  for (const l of state.result?.lines || []) if (l.state === "supported" && !state.decisions[l.item_id]) state.decisions[l.item_id] = "approve";
  renderLines();
}

function updateRelease() {
  const lines = state.result?.lines || [];
  const open = lines.filter((l) => !state.decisions[l.item_id]).length;
  const approved = lines.filter((l) => state.decisions[l.item_id] === "approve").length;
  $("#approve-supported").disabled = !lines.some((l) => l.state === "supported" && !state.decisions[l.item_id]);
  $("#release").disabled = !lines.length || open > 0 || approved === 0;
  $("#release-note").textContent = !lines.length ? "Nothing reaches the patient until every line is approved or removed."
    : open ? `${open} line(s) still need your decision.` : `${approved} line(s) approved for the patient.`;
}

function release() {
  const d = state.result;
  const program = {
    session: state.session.id, language: state.session.language, date: new Date().toISOString().slice(0, 10),
    lines: d.lines.filter((l) => state.decisions[l.item_id] === "approve").map((l) => ({ text: l.text, en: l.source_en })),
  };
  const bytes = new TextEncoder().encode(JSON.stringify(program));
  let bin = ""; for (const b of bytes) bin += String.fromCharCode(b);
  const hash = btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  window.open(`/patient#${hash}`, "_blank", "noopener");
}

init().catch((e) => banner("warn", `Could not load the sessions: ${e.message}`));
