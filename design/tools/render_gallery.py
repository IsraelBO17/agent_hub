#!/usr/bin/env python3
"""Build design/renders/index.html, the screen gallery, from design/renders/manifest.json.

The manifest lists every screen and board in fleet_dev.pen with its render, scope (PRODUCT_PLAN §5),
delivery status and the built screenshots (docs/screenshots/) that match it. Edit the manifest, then run:

    python3 design/tools/render_gallery.py

--shots-base sets where built screenshots are found relative to the page (default: the repo's
docs/screenshots/ seen from design/renders/). --out writes the page elsewhere, for publishing.
Needs only Python 3.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDERS = ROOT / "design" / "renders"

TEMPLATE = r"""<title>Agent Hub screens</title>
<meta name="description" content="Every screen and board in design/fleet_dev.pen, next to what is built.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: a section rail beside a grid of screen cards; a viewer overlay shows design and build side by side. */
:root {
  --bg: #FBFAF7; --surface: #FFFFFF; --sidebar: #F3F1EC; --muted: #EEEBE4; --border: #E3DFD6;
  --text: #1B1A17; --text-2: #5E5A52; --text-3: #6F6A62; --accent: #1F5C4A; --accent-soft: #E2EEE8;
  --built: #1F5C4A; --built-soft: #E2EEE8; --m2: #2F5597; --m2-soft: #E1E8F4; --m3: #6A4A94; --m3-soft: #EFE8F5;
  --m4: #8A5A12; --m4-soft: #F5ECDD; --later: #77726A; --later-soft: #ECEAE5; --scrim: #1B1A17CC; --on-scrim: #E9E6DE; --shot-bg: #EEEBE4;
  --font-ui: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #161513; --surface: #1F1E1B; --sidebar: #1B1A17; --muted: #2A2925; --border: #34322D;
  --text: #ECE9E2; --text-2: #B9B4A9; --text-3: #A8A398; --accent: #7FC2A5; --accent-soft: #1F3A30;
  --built: #7FC2A5; --built-soft: #1F3A30; --m2: #9DB8E8; --m2-soft: #232E42; --m3: #C3A8E6; --m3-soft: #322841;
  --m4: #E2B66E; --m4-soft: #3A2F1C; --later: #B9B4A9; --later-soft: #2E2C28; --scrim: #000000D9; --shot-bg: #2A2925; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #161513; --surface: #1F1E1B; --sidebar: #1B1A17; --muted: #2A2925; --border: #34322D;
  --text: #ECE9E2; --text-2: #B9B4A9; --text-3: #A8A398; --accent: #7FC2A5; --accent-soft: #1F3A30;
  --built: #7FC2A5; --built-soft: #1F3A30; --m2: #9DB8E8; --m2-soft: #232E42; --m3: #C3A8E6; --m3-soft: #322841;
  --m4: #E2B66E; --m4-soft: #3A2F1C; --later: #B9B4A9; --later-soft: #2E2C28; --scrim: #000000D9; --shot-bg: #2A2925; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--bg); color: var(--text); font: 14px/1.5 var(--font-ui); margin: 0 }
button, input { font: inherit; color: inherit }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
.wrap { display: grid; grid-template-columns: 236px minmax(0, 1fr); min-height: 100vh }
.rail { background: var(--sidebar); border-right: 1px solid var(--border); padding: 20px 14px; position: sticky; top: env(safe-area-inset-top, 0px); height: 100vh; overflow-y: auto }
.brand { display: flex; align-items: center; gap: 10px; padding: 0 6px 18px; font-weight: 600; font-size: 15px }
.mark { width: 26px; height: 26px; border-radius: 7px; background: var(--accent); color: var(--bg); display: grid; place-items: center; font-size: 13px; font-weight: 700 }
.rail h3 { font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--text-3); font-weight: 600; margin: 16px 6px 6px }
.rail a { display: flex; justify-content: space-between; gap: 8px; padding: 5px 8px; border-radius: 7px; color: var(--text-2); text-decoration: none; font-size: 13px }
.rail a:hover { background: var(--muted); color: var(--text) }
.rail a span:last-child { font-family: var(--font-mono); font-size: 12px; color: var(--text-3); font-variant-numeric: tabular-nums }
main { padding: 28px 32px 80px; min-width: 0 }
header.top { display: flex; flex-wrap: wrap; gap: 16px 32px; align-items: flex-end; justify-content: space-between; margin-bottom: 20px }
h1 { font-size: 28px; line-height: 1.2; margin: 0; letter-spacing: -.01em; text-wrap: balance }
.sub { color: var(--text-2); margin: 6px 0 0; max-width: 68ch }
.sub code, .id { font-family: var(--font-mono); font-size: 12px }
.tally { display: flex; flex-wrap: wrap; gap: 6px }
.controls { display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: center; padding: 12px 0; border-block: 1px solid var(--border); margin-bottom: 8px; position: sticky; top: env(safe-area-inset-top, 0px); background: var(--bg); z-index: 5 }
.chipset { display: flex; flex-wrap: wrap; gap: 6px; align-items: center }
.chipset > b { font-size: 12px; color: var(--text-3); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; margin-right: 2px }
.chip { border: 1px solid var(--border); background: var(--surface); border-radius: 999px; padding: 4px 11px; font-size: 13px; cursor: pointer; display: inline-flex; gap: 6px; align-items: center; min-height: 30px }
.chip[aria-pressed="false"] { opacity: .5; background: transparent }
.chip .n { font-family: var(--font-mono); font-size: 12px; color: var(--text-3); font-variant-numeric: tabular-nums }
.dot { width: 8px; height: 8px; border-radius: 50% }
.search { border: 1px solid var(--border); background: var(--surface); border-radius: 9px; padding: 6px 11px; width: 220px; max-width: 100% }
section { padding-top: 28px; scroll-margin-top: 70px }
section > h2 { font-size: 20px; margin: 0; display: flex; gap: 10px; align-items: baseline; flex-wrap: wrap }
section > h2 .count { font-size: 13px; color: var(--text-3); font-weight: 400 }
section > p { color: var(--text-2); margin: 4px 0 0; max-width: 72ch }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-top: 14px }
.grid.wide { grid-template-columns: repeat(auto-fill, minmax(min(520px, 100%), 1fr)) }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; min-width: 0 }
.thumbs { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 1px; background: var(--border); border: 0; padding: 0; cursor: zoom-in; width: 100% }
.shot { position: relative; background: var(--shot-bg); aspect-ratio: 1440 / 1024; overflow: hidden }
.shot img { width: 100%; height: 100%; object-fit: contain; object-position: top center; display: block }
.shot.tall img { object-fit: cover }
.shot .tag { position: absolute; left: 6px; top: 6px; font-size: 11px; font-weight: 600; background: var(--surface); color: var(--text-2); border-radius: 5px; padding: 1px 6px; letter-spacing: .03em; text-transform: uppercase }
.meta { padding: 11px 13px 13px; display: grid; gap: 6px }
.row1 { display: flex; gap: 8px; align-items: flex-start; justify-content: space-between }
.name { font-weight: 600; font-size: 14px; line-height: 1.35 }
.facts { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; color: var(--text-3); font-size: 12px }
.pill { font-size: 12px; font-weight: 600; border-radius: 999px; padding: 1px 8px; white-space: nowrap }
.s-built { color: var(--built); background: var(--built-soft) } .s-M2 { color: var(--m2); background: var(--m2-soft) }
.s-M3 { color: var(--m3); background: var(--m3-soft) } .s-M4 { color: var(--m4); background: var(--m4-soft) } .s-later { color: var(--later); background: var(--later-soft) }
.d-built { background: var(--built) } .d-M2 { background: var(--m2) } .d-M3 { background: var(--m3) } .d-M4 { background: var(--m4) } .d-later { background: var(--later) }
.scope { font-family: var(--font-mono); font-size: 12px; border: 1px solid var(--border); border-radius: 5px; padding: 0 5px; color: var(--text-2) }
.copy { border: 0; background: none; padding: 0; cursor: pointer; color: var(--text-3); font-family: var(--font-mono); font-size: 12px; text-decoration: underline dotted; text-underline-offset: 3px }
.trigger { font-size: 13px; color: var(--text-2) } .trigger::before { content: "→ "; color: var(--text-3) }
.note { font-size: 13px; color: var(--text-2); line-height: 1.45 }
.empty { color: var(--text-3); padding: 40px 0 }
dialog { border: 0; padding: 0; max-width: none; max-height: none; width: 100%; height: 100%; background: var(--scrim); color: var(--text) }
dialog::backdrop { background: transparent }
.vbar { display: flex; gap: 12px; align-items: center; justify-content: space-between; padding: 10px 16px; background: var(--surface); border-bottom: 1px solid var(--border); flex-wrap: wrap }
.vbar .name { font-size: 15px } .vbar .btns { display: flex; gap: 6px }
.vbtn { border: 1px solid var(--border); background: var(--surface); border-radius: 8px; padding: 5px 12px; cursor: pointer; min-height: 32px }
.vbody { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: 16px; padding: 16px; height: calc(100% - 56px); overflow: auto; align-items: start }
.vbody figure { margin: 0; min-width: 0 } .vbody figcaption { color: var(--on-scrim); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 6px; font-weight: 600 }
.vbody img { width: 100%; height: auto; display: block; border-radius: 6px; background: var(--shot-bg) }
.vbody .mobile img { max-width: 420px }
@media (max-width: 860px) {
  .wrap { grid-template-columns: 1fr } .rail { display: none }
  main { padding: 20px 16px 60px } .controls { position: static }
  .vbody { grid-auto-flow: row }
}
@media (prefers-reduced-motion: no-preference) { .card { transition: border-color .15s } .card:hover { border-color: var(--text-3) } }
</style>

<div class="wrap">
  <nav class="rail" aria-label="Sections">
    <div class="brand"><span class="mark" aria-hidden="true">A</span>Agent Hub screens</div>
    <div id="nav"></div>
  </nav>
  <main>
    <header class="top">
      <div>
        <h1>Every screen, designed and built</h1>
        <p class="sub" id="sub"></p>
      </div>
      <div class="tally" id="tally" aria-label="Screens by status"></div>
    </header>
    <div class="controls">
      <div class="chipset" id="f-status"><b>Status</b></div>
      <div class="chipset" id="f-scope"><b>Scope</b></div>
      <div class="chipset"><button class="chip" id="f-built" aria-pressed="false">Has a build screenshot</button></div>
      <input class="search" id="q" type="search" placeholder="Search name or node ID" aria-label="Search screens">
    </div>
    <div id="out"></div>
  </main>
</div>
<dialog id="viewer" aria-label="Screen viewer">
  <div class="vbar"><div><div class="name" id="v-name"></div><div class="facts" id="v-facts"></div></div>
    <div class="btns"><button class="vbtn" id="v-prev" aria-label="Previous screen">←</button><button class="vbtn" id="v-next" aria-label="Next screen">→</button><button class="vbtn" id="v-close">Close</button></div></div>
  <div class="vbody" id="v-body"></div>
</dialog>

<script>
const DATA = __DATA__;
const SHOTS = __SHOTS__;
const STATUSES = ["built", "M2", "M3", "M4", "later"];
const LABEL = { built: "Built", M2: "M2", M3: "M3", M4: "M4", later: "Later" };
const state = { status: new Set(STATUSES), scope: new Set(["P0", "P1", "P2"]), builtOnly: false, q: "" };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const isMobile = s => s.size.startsWith("390");
const isTall = s => { const [w, h] = s.size.split("×").map(Number); return !h || h / w > 1.6 };
const sections = [
  ...DATA.groups.map(g => ({ key: g.key, title: g.title, kind: "surface", items: DATA.screens.filter(s => s.group === g.key) })),
  ...DATA.flows.map(f => ({ key: "f" + f.n, title: `Flow ${f.n} · ${f.title}`, kind: "flow", desc: f.description, items: DATA.screens.filter(s => s.flow === f.n) })),
];
const count = (arr, k) => arr.reduce((m, s) => (m[s[k]] = (m[s[k]] || 0) + 1, m), {});

document.getElementById("sub").innerHTML = `${DATA.screens.length} screens and boards from <code>${esc(DATA.source)}</code>, rendered ${esc(DATA.generated)}. Status is the milestone that builds each one; build screenshots come from <code>docs/screenshots/</code>. Click a screen to see it full size.`;
const st = count(DATA.screens, "status");
document.getElementById("tally").innerHTML = STATUSES.map(s => `<span class="pill s-${s}">${LABEL[s]} ${st[s] || 0}</span>`).join("");
const sc = count(DATA.screens, "scope");
for (const s of STATUSES) document.getElementById("f-status").insertAdjacentHTML("beforeend", `<button class="chip" data-status="${s}" aria-pressed="true"><span class="dot d-${s}"></span>${LABEL[s]}<span class="n">${st[s] || 0}</span></button>`);
for (const s of ["P0", "P1", "P2"]) document.getElementById("f-scope").insertAdjacentHTML("beforeend", `<button class="chip" data-scope="${s}" aria-pressed="true">${s}<span class="n">${sc[s] || 0}</span></button>`);

const visible = s => state.status.has(s.status) && state.scope.has(s.scope) && (!state.builtOnly || s.built.length) &&
  (!state.q || (s.name + " " + s.id).toLowerCase().includes(state.q));
let order = [];

function shot(src, tag, s) {
  return `<div class="shot${isTall(s) ? " tall" : ""}"><img loading="lazy" decoding="async" src="${esc(src)}" alt="${esc(tag + ": " + s.name)}"><span class="tag">${tag}</span></div>`;
}
function card(s) {
  const imgs = [shot(s.render, "Design", s), ...s.built.map(b => shot(SHOTS + b, "Built", s))].join("");
  return `<article class="card">
    <button class="thumbs" data-open="${s.id}" aria-label="Open ${esc(s.name)} full size">${imgs}</button>
    <div class="meta">
      <div class="row1"><div class="name">${esc(s.name)}</div><span class="pill s-${s.status}">${LABEL[s.status]}</span></div>
      <div class="facts"><button class="copy" data-copy="${s.id}" title="Copy node ID">${s.id}</button><span>${esc(s.size)}</span><span class="scope">${s.scope}</span></div>
      ${s.trigger ? `<div class="trigger">${esc(s.trigger)}</div>` : ""}
      ${s.note ? `<div class="note">${esc(s.note)}</div>` : ""}
    </div></article>`;
}
function render() {
  order = [];
  let html = "", nav = "", lastKind = "";
  for (const sec of sections) {
    const items = sec.items.filter(visible);
    if (sec.kind !== lastKind) { nav += `<h3>${sec.kind === "surface" ? "By surface" : "By flow"}</h3>`; lastKind = sec.kind }
    nav += `<a href="#${sec.key}"><span>${esc(sec.title)}</span><span>${items.length}</span></a>`;
    if (!items.length) continue;
    order.push(...items);
    const wide = items.some(s => s.built.length) && !items.every(isMobile);
    html += `<section id="${sec.key}"><h2>${esc(sec.title)} <span class="count">${items.length} of ${sec.items.length}</span></h2>
      ${sec.desc ? `<p>${esc(sec.desc)}</p>` : ""}<div class="grid${wide ? " wide" : ""}">${items.map(card).join("")}</div></section>`;
  }
  document.getElementById("nav").innerHTML = nav;
  document.getElementById("out").innerHTML = html || `<p class="empty">No screens match these filters.</p>`;
}
document.addEventListener("click", e => {
  const c = e.target.closest("[data-status],[data-scope],#f-built,[data-copy],[data-open]");
  if (!c) return;
  if (c.dataset.copy) {
    const t = c.dataset.copy;
    navigator.clipboard?.writeText(t).then(() => { c.textContent = "copied"; setTimeout(() => c.textContent = t, 900) }).catch(() => getSelection().selectAllChildren(c));
    return;
  }
  if (c.dataset.open) return openViewer(c.dataset.open);
  if (c.id === "f-built") { state.builtOnly = !state.builtOnly; c.setAttribute("aria-pressed", state.builtOnly) }
  else { const set = c.dataset.status ? state.status : state.scope, v = c.dataset.status || c.dataset.scope; set.has(v) ? set.delete(v) : set.add(v); c.setAttribute("aria-pressed", set.has(v)) }
  render();
});
document.getElementById("q").addEventListener("input", e => { state.q = e.target.value.trim().toLowerCase(); render() });

const viewer = document.getElementById("viewer");
let current = -1;
function openViewer(id) {
  current = order.findIndex(s => s.id === id);
  const s = order[current]; if (!s) return;
  document.getElementById("v-name").textContent = s.name;
  document.getElementById("v-facts").innerHTML = `<span class="id">${s.id}</span><span>${esc(s.size)}</span><span class="scope">${s.scope}</span><span class="pill s-${s.status}">${LABEL[s.status]}</span>${s.trigger ? `<span class="trigger">${esc(s.trigger)}</span>` : ""}`;
  const fig = (src, cap) => `<figure class="${isMobile(s) ? "mobile" : ""}"><figcaption>${cap}</figcaption><img src="${esc(src)}" alt="${esc(cap + ": " + s.name)}"></figure>`;
  document.getElementById("v-body").innerHTML = [fig(s.render, "Design"), ...s.built.map(b => fig(SHOTS + b, "Built · " + b))].join("");
  document.getElementById("v-body").scrollTop = 0;
  if (!viewer.open) viewer.showModal();
}
const step = d => { if (order.length) openViewer(order[(current + d + order.length) % order.length].id) };
document.getElementById("v-prev").onclick = () => step(-1);
document.getElementById("v-next").onclick = () => step(1);
document.getElementById("v-close").onclick = () => viewer.close();
viewer.addEventListener("keydown", e => { if (e.key === "ArrowLeft") step(-1); if (e.key === "ArrowRight") step(1) });
viewer.addEventListener("click", e => { if (e.target === viewer) viewer.close() });
render();
</script>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--shots-base", default="../../docs/screenshots/")
    ap.add_argument("--out", default=str(RENDERS / "index.html"))
    args = ap.parse_args()
    data = json.loads((RENDERS / "manifest.json").read_text())
    page = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__SHOTS__", json.dumps(args.shots_base))
    # A local file needs its own document skeleton; the published artifact adds one itself.
    if args.out.endswith("index.html") and Path(args.out).parent == RENDERS:
        page = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n' + page.replace("</style>", "</style>\n</head>\n<body>", 1) + "\n</body>\n</html>\n"
    Path(args.out).write_text(page)
    print(f"wrote {args.out} ({len(data['screens'])} screens)")


if __name__ == "__main__":
    main()
