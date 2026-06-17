"use strict";
// 操作トレース可視化ビューア
// - GET /trace/map      でノード/エッジ/ルート/ページ対応を取得しマップ描画
// - GET /trace/stream   (SSE) を購読し、trace_id ごとにフル経路を点灯＋粒子アニメ（失敗は赤）
// - GET /trace/rollup   で履歴集計を取得しエッジ太さ/ヒート着色
// すべてオフライン動作（外部CDNなし）。アセットは /static/trace/ 配下の絶対パス。

// ===== グローバル状態 =====
let COLS = [];                 // 列見出し
let N = {};                    // id -> {col,label,sub,detail,x,y,_rect}
let EDGES = [];                // [[u,v], ...]
let ROUTES = {};               // path -> handlerId
let PAGES = {};                // page.html -> screenId
let labelToId = {};            // テーブル名等の label -> id 逆引き

const TEAL = "#2dd4bf", ERR = "#f85149";

// レイアウト定数（モックアップ準拠）
const W = 1320, H = 720, NW = 128, NH = 36;
const colX = c => 100 + c * ((1160 - 100) / 7);
const EDGEKEY = (u, v) => u + ">" + v;

let mode = "rt";
let curWin = "10m";

// ===== SVG ヘルパ =====
const svg = document.getElementById("svg");
const NS = "http://www.w3.org/2000/svg";
function el(t, a) { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); return e; }

function layout() {
  const byCol = {};
  Object.entries(N).forEach(([id, n]) => { (byCol[n.col] = byCol[n.col] || []).push(id); });
  Object.values(byCol).forEach(ids => {
    const gap = Math.min(100, (H - 120) / Math.max(ids.length - 1, 1));
    const startY = (H - (ids.length - 1) * gap) / 2;
    ids.forEach((id, i) => { N[id].x = colX(N[id].col); N[id].y = startY + i * gap; });
  });
}

function edgePath(u, v) {
  const a = N[u], b = N[v];
  const x1 = a.x + NW / 2, y1 = a.y, x2 = b.x - NW / 2, y2 = b.y;
  const mx = (x1 + x2) / 2;
  return `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
}

let edgeEls = {};      // edgeKey -> <path>
let edgeSet = new Set(); // 有効なエッジキー集合

function drawStatic() {
  svg.innerHTML = "";
  // 列見出し＋帯
  COLS.forEach((c, i) => {
    const x = colX(i);
    svg.appendChild(el("rect", { x: x - NW / 2 - 8, y: 24, width: NW + 16, height: H - 44, rx: 10,
      fill: i % 2 ? "#11161d" : "#0f141b", opacity: .5 }));
    const t = el("text", { x: x, y: 18, "text-anchor": "middle", class: "colhead" });
    t.textContent = c; svg.appendChild(t);
  });
  // エッジ
  edgeEls = {}; edgeSet = new Set();
  EDGES.forEach(([u, v]) => {
    if (!N[u] || !N[v]) return;
    const k = EDGEKEY(u, v);
    edgeSet.add(k);
    const p = el("path", { d: edgePath(u, v), fill: "none", stroke: "#30363d", "stroke-width": 1.5,
      "stroke-linecap": "round", opacity: .55 });
    p.style.cursor = "pointer";
    p.addEventListener("click", ev => { ev.stopPropagation(); showEdge(k); });
    svg.appendChild(p); edgeEls[k] = p;
  });
  // ノード
  Object.entries(N).forEach(([id, n]) => {
    const g = el("g", { class: "node" });
    g.addEventListener("click", ev => { ev.stopPropagation(); showNode(id); });
    const r = el("rect", { x: n.x - NW / 2, y: n.y - NH / 2, width: NW, height: NH, rx: 8,
      fill: "#1c2230", stroke: "#3a4252", "stroke-width": 1.2 });
    n._rect = r;
    const t1 = el("text", { x: n.x, y: n.y - 1, "text-anchor": "middle" }); t1.textContent = n.label;
    const t2 = el("text", { x: n.x, y: n.y + 11, "text-anchor": "middle", class: "sub" }); t2.textContent = n.sub;
    g.appendChild(r); g.appendChild(t1); g.appendChild(t2); svg.appendChild(g);
  });
  if (mode === "hist") refetchHistory();
}

function resetNodes() {
  Object.values(N).forEach(n => { n._rect.setAttribute("stroke", "#3a4252"); n._rect.setAttribute("fill", "#1c2230"); });
}
function resetEdges() {
  Object.values(edgeEls).forEach(p => { p.setAttribute("stroke", "#30363d"); p.setAttribute("stroke-width", 1.5); p.setAttribute("opacity", .55); });
}

// ===== 履歴モード：ロールアップ取得 → 太さ＋ヒート =====
function heat(t) { // 0..1 -> blue->yellow->red
  const c1 = [56, 139, 255], c2 = [210, 153, 34], c3 = [248, 81, 73];
  let a, b, f;
  if (t < .5) { a = c1; b = c2; f = t / .5; } else { a = c2; b = c3; f = (t - .5) / .5; }
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * f)).join(",")})`;
}

let histData = {}; // edgeKey -> {count, avg_ms}

function paintHistory() {
  resetEdges();
  const keys = Object.keys(histData);
  if (!keys.length) {
    // 空（集計未実装/データ無し）→ 全エッジを細く中立色のまま。グレースフルに処理。
    return;
  }
  let mx = 1, mn = 1e9;
  keys.forEach(k => { mx = Math.max(mx, histData[k].count); mn = Math.min(mn, histData[k].count); });
  Object.entries(edgeEls).forEach(([k, p]) => {
    const d = histData[k];
    if (!d) return; // データの無いエッジは細いまま
    const c = d.count;
    const t = (Math.log(c + 1) - Math.log(mn + 1)) / (Math.log(mx + 1) - Math.log(mn + 1) || 1);
    p.setAttribute("stroke", heat(t));
    p.setAttribute("stroke-width", 1.5 + t * 11);
    p.setAttribute("opacity", .85);
  });
}

async function refetchHistory() {
  histData = {};
  try {
    const res = await fetch(`/trace/rollup?window=${encodeURIComponent(curWin)}`);
    const arr = await res.json();
    (arr || []).forEach(row => {
      // row.edge は "fromId>toId"
      histData[row.edge] = { count: row.count, avg_ms: row.avg_ms };
    });
  } catch (e) {
    histData = {}; // 取得失敗もグレースフルに（空扱い）
  }
  if (mode === "hist") {
    paintHistory();
    const n = Object.keys(histData).length;
    if (!n) {
      document.getElementById("detail").innerHTML =
        `この時間窓（<b>${curWin}</b>）の集計データはまだありません。<br>` +
        `<span class="hint">集計が貯まると各経路が太さ・色（ヒート）で表示されます。アプリを操作してから再度お試しください。</span>`;
    }
  }
}

// ===== リアルタイム：粒子アニメ =====
const fx = document.getElementById("fx");
const ctx = fx.getContext("2d");
let particles = [], raf = null;

function resizeFx() {
  const r = svg.getBoundingClientRect();
  fx.width = r.width; fx.height = r.height;
  fx.style.width = r.width + "px"; fx.style.height = r.height + "px";
  fx._sx = r.width / W; fx._sy = r.height / H;
}
window.addEventListener("resize", resizeFx);

function nodePt(id, side) { const n = N[id]; return { x: n.x + (side || 0) * NW / 2, y: n.y }; }
function bez(p0, p1, p2, p3, t) {
  const u = 1 - t;
  return {
    x: u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
    y: u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y
  };
}
function loop() {
  const now = performance.now();
  ctx.clearRect(0, 0, fx.width, fx.height);
  const sx = fx._sx, sy = fx._sy;
  particles = particles.filter(p => now < p.start + p.dur);
  particles.forEach(p => {
    if (now < p.start) return;
    const t = (now - p.start) / p.dur;
    const pt = bez(p.a0, p.a1, p.a2, p.a3, t);
    const x = pt.x * sx, y = pt.y * sy;
    ctx.beginPath(); ctx.arc(x, y, 4.2, 0, 7); ctx.fillStyle = p.color;
    ctx.shadowColor = p.color; ctx.shadowBlur = 12; ctx.fill(); ctx.shadowBlur = 0;
  });
  if (particles.length || mode === "rt") raf = requestAnimationFrame(loop);
  else { raf = null; ctx.clearRect(0, 0, fx.width, fx.height); }
}

// 1トレース分の点灯（フル経路）＋粒子を放つ
function lightTrace(nodeIds, color) {
  // ノード点灯
  nodeIds.forEach(id => {
    const n = N[id]; if (!n) return;
    n._rect.setAttribute("stroke", color);
    n._rect.setAttribute("fill", color === ERR ? "#3a1f24" : "#243044");
  });
  // 両端が点灯集合にあるエッジを点灯＋粒子
  const litSet = new Set(nodeIds);
  const litEdges = [];
  edgeSet.forEach(k => {
    const i = k.indexOf(">");
    const u = k.slice(0, i), v = k.slice(i + 1);
    if (litSet.has(u) && litSet.has(v)) litEdges.push([u, v, k]);
  });
  const now = performance.now();
  litEdges.forEach(([u, v, k]) => {
    const p = edgeEls[k];
    if (p) { p.setAttribute("stroke", color); p.setAttribute("stroke-width", 3); p.setAttribute("opacity", 1); }
    const startCol = N[u].col;
    const a0 = nodePt(u, 1), a3 = nodePt(v, -1);
    const mx = (a0.x + a3.x) / 2;
    const a1 = { x: mx, y: a0.y }, a2 = { x: mx, y: a3.y };
    for (let s = 0; s < 3; s++) {
      particles.push({ a0, a1, a2, a3, color, start: now + startCol * 260 + s * 90, dur: 520 });
    }
  });
  if (!raf) loop();
  // 一定時間後にこのトレースの点灯を解除（履歴モードでなければ）
  clearTimeout(lightTrace._t);
  lightTrace._t = setTimeout(() => {
    if (mode === "rt") { resetNodes(); resetEdges(); }
  }, 3000);
}

// ===== SSE: trace_id ごとに span を集約しフル経路を計算 =====
const TTL = 3000;
const traces = new Map(); // trace_id -> { nodes:Set, error:bool, steps:[], t:timestamp }

function routeHandler(path) {
  if (ROUTES[path]) return ROUTES[path];                  // 完全一致
  let best = null, bestLen = -1;                           // 最長プレフィックス一致
  for (const key in ROUTES) {
    if (path.indexOf(key) === 0 && key.length > bestLen) { best = ROUTES[key]; bestLen = key.length; }
  }
  return best;
}

function tableNodeId(name) {
  if (labelToId[name]) return labelToId[name];   // label 一致
  if (N["t_" + name]) return "t_" + name;        // フォールバック id
  return null;
}

function nodesForSpan(span) {
  const ids = [];
  if (span.kind === "http") {
    if (span.page && PAGES[span.page]) ids.push(PAGES[span.page]);
    if (N["fetch"]) ids.push("fetch");
    if (N["cors"]) ids.push("cors");
    const h = routeHandler(span.node);
    if (h && N[h]) ids.push(h);
  } else if (span.kind === "auth") {
    if (N["auth"]) ids.push("auth");
  } else if (span.kind === "sql") {
    if (N["db"]) ids.push("db");
    if (N["pg"]) ids.push("pg");
    (span.tables || []).forEach(name => { const tid = tableNodeId(name); if (tid) ids.push(tid); });
  }
  return ids;
}

function stepLabel(span) {
  if (span.kind === "http") return `HTTP ${span.node}` + (span.page ? ` (${span.page})` : "");
  if (span.kind === "auth") return `認証 ${span.node}`;
  if (span.kind === "sql") return `SQL ${(span.tables || []).join(", ") || span.node}`;
  return span.kind + " " + (span.node || "");
}

function onSpan(span) {
  const tid = span.trace_id || "_";
  let tr = traces.get(tid);
  if (!tr) { tr = { nodes: new Set(), error: false, steps: [], t: Date.now() }; traces.set(tid, tr); }
  tr.t = Date.now();
  if (span.status === "error") tr.error = true;
  nodesForSpan(span).forEach(id => tr.nodes.add(id));
  tr.steps.push({ label: stepLabel(span), status: span.status, dur: span.dur_ms });

  const color = tr.error ? ERR : TEAL;
  if (mode === "rt") lightTrace([...tr.nodes], color);
  renderTraceLog(tid, tr);
  pruneTraces();
}

function pruneTraces() {
  const now = Date.now();
  for (const [k, v] of traces) if (now - v.t > TTL) traces.delete(k);
}

function renderTraceLog(tid, tr) {
  const color = tr.error ? ERR : TEAL;
  const steps = tr.steps.map((s, i) =>
    `<div class="trace-step ${s.status === "error" ? "err" : ""}"><b>${String(i + 1).padStart(2, "0")}</b> ${s.label}` +
    (s.dur ? ` <span class="hint">${s.dur}ms</span>` : "") +
    (s.status === "error" ? " <span style='color:var(--err)'>✗ 失敗</span>" : "") + `</div>`
  ).join("");
  document.getElementById("tracelog").innerHTML =
    `<h2>トレース連鎖（最新）</h2>` +
    `<div class="trace-step"><span class="tid">trace_id = ${tid}</span> ` +
    `<span style="color:${color}">${tr.error ? "● 失敗を含む" : "● 正常"}</span></div>` +
    steps;
}

let es = null;
function connectSSE() {
  try {
    es = new EventSource("/trace/stream");
    es.onopen = () => setConn(true);
    es.onerror = () => setConn(false); // EventSource は自動再接続する
    es.onmessage = (ev) => {
      if (!ev.data) return;
      let span;
      try { span = JSON.parse(ev.data); } catch (_) { return; }
      onSpan(span);
    };
  } catch (e) { setConn(false); }
}
function setConn(ok) {
  const c = document.getElementById("conn");
  c.classList.toggle("off", !ok);
  c.textContent = ok ? "● 接続中（リアルタイム）" : "● 未接続";
}

// ===== 詳細パネル（FR-U7） =====
function showNode(id) {
  const n = N[id]; if (!n) return;
  const d = n.detail || {};
  let html = `<div class="k">${d.k || ""}</div><div class="title">${n.label}</div>`;
  if (d.one) html += `<div class="onebox">💡 ${d.one}</div>`;
  if (d.easy) html += `<div class="easy">${d.easy}</div>`; // HTML（<span class=term>）をそのまま描画
  if (d.f) html += `<div><span class="k">対応する実体：</span><code>${d.f}</code></div>`;
  if (d.sql) html += `<div style="margin-top:8px"><span class="k">実際に流れるSQL：</span><div class="sql">${escapeHtml(d.sql)}</div></div>`;
  if (d.terms && d.terms.length) {
    html += `<div class="glossary"><div class="gh">📖 用語メモ（注釈）</div><dl>`;
    d.terms.forEach(([t, r, m]) => {
      html += `<dt>${t}${r && r !== "―" ? `<span class="read">${r}</span>` : ""}</dt><dd>${m}</dd>`;
    });
    html += `</dl></div>`;
  }
  document.getElementById("detail").innerHTML = html;
}

function showEdge(k) {
  const i = k.indexOf(">");
  const u = k.slice(0, i), v = k.slice(i + 1);
  let html = `<div class="k">経路（エッジ）</div>` +
    `<div style="font-size:14px;margin:6px 0"><b>${N[u] ? N[u].label : u}</b> → <b>${N[v] ? N[v].label : v}</b></div>`;
  if (mode === "hist") {
    const d = histData[k];
    if (d) html += `<div style="margin-top:6px">この時間窓の通過 <b>${d.count}</b> 回` +
      (d.avg_ms != null ? `<br>平均所要 <b>${Number(d.avg_ms).toFixed(1)}</b> ms` : "") + `</div>`;
    else html += `<div class="hint" style="margin-top:6px">この時間窓の集計データはまだありません。</div>`;
  } else {
    html += `<div class="hint" style="margin-top:6px">通過量は「履歴（集計）」モードで確認できます。</div>`;
  }
  document.getElementById("detail").innerHTML = html;
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ===== モード/時間窓 UI =====
function setMode(m) {
  mode = m;
  document.getElementById("m-rt").classList.toggle("on", m === "rt");
  document.getElementById("m-hist").classList.toggle("on", m === "hist");
  document.getElementById("rt-tools").style.display = m === "rt" ? "flex" : "none";
  document.getElementById("hist-tools").style.display = m === "hist" ? "flex" : "none";
  renderLegend();
  if (m === "hist") {
    if (raf) { cancelAnimationFrame(raf); raf = null; }
    ctx.clearRect(0, 0, fx.width, fx.height);
    resetNodes();
    document.getElementById("tracelog").innerHTML = "";
    document.getElementById("detail").innerHTML =
      "時間窓を切り替えると、各経路の <b>通過量</b> が線の太さ・色（ヒート）で変わります。線をクリックで回数表示。";
    refetchHistory();
  } else {
    resetEdges(); resetNodes(); resizeFx(); loop();
    document.getElementById("detail").innerHTML =
      "アプリを操作すると、その1クリックが起こす経路が点灯し <b>粒子</b> が流れます。失敗は赤で表示されます。";
  }
}

const WINDOWS = [["10分", "10m"], ["1時間", "1h"], ["1日", "1d"], ["1週", "1w"], ["1月", "1m"], ["1年", "1y"]];
function setWindow(w, i) {
  curWin = w;
  document.querySelectorAll("#window-btns button").forEach((b, j) => b.classList.toggle("on", j === i));
  refetchHistory();
}

function renderLegend() {
  const lg = document.getElementById("legend");
  if (mode === "rt") {
    lg.innerHTML = `<div style="margin-bottom:4px;color:#e6edf3">凡例（リアルタイム）</div>` +
      `<div class="row"><span class="swatch" style="background:${TEAL}"></span>正常な経路</div>` +
      `<div class="row"><span class="swatch" style="background:${ERR}"></span>失敗（エラー）を含む経路</div>` +
      `<div class="row hint">粒子＝1トレースの流れ</div>`;
  } else {
    lg.innerHTML = `<div style="margin-bottom:4px;color:#e6edf3">凡例（通過量ヒート）</div>
      <div class="row"><span class="swatch" style="background:${heat(0)}"></span>少ない</div>
      <div class="row"><span class="swatch" style="background:${heat(.5)}"></span>中</div>
      <div class="row"><span class="swatch" style="background:${heat(1)}"></span>多い</div>
      <div class="row hint">線の太さ＝通過回数</div>`;
  }
}

// ===== 初期化 =====
async function init() {
  let map;
  try {
    const res = await fetch("/trace/map");
    map = await res.json();
  } catch (e) {
    document.getElementById("detail").innerHTML = "マップの取得に失敗しました（/trace/map）。サーバーが起動しているか確認してください。";
    return;
  }
  COLS = map.columns || [];
  N = map.nodes || {};
  EDGES = map.edges || [];
  ROUTES = map.routes || {};
  PAGES = map.pages || {};
  labelToId = {};
  Object.entries(N).forEach(([id, n]) => { if (n.label) labelToId[n.label] = id; });

  layout();
  drawStatic();
  svg.addEventListener("click", () => {}); // 背景クリック

  // 時間窓ボタン
  const wb = document.getElementById("window-btns");
  WINDOWS.forEach(([lbl, w], i) => {
    const b = document.createElement("button");
    b.textContent = lbl;
    if (w === curWin) b.classList.add("on");
    b.onclick = () => setWindow(w, i);
    wb.appendChild(b);
  });

  resizeFx();
  renderLegend();
  document.getElementById("detail").innerHTML =
    "アプリを操作すると、その1クリックが起こす経路が点灯し <b>粒子</b> が流れます。失敗は赤で表示されます。";
  loop();
  connectSSE();
}

window.addEventListener("load", init);
setTimeout(resizeFx, 300);
