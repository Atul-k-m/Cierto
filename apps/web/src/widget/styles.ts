// Widget styles. Every colour, radius and face comes from the host's tokens (--w-*);
// the widget has no identity of its own. Status is always carried by words, never colour alone.
export const styles = /* css */ `
:host { display: block; font-family: var(--w-font-body); color: var(--w-color-ink); -webkit-font-smoothing: antialiased; }
:host([hidden]) { display: none; }
* { box-sizing: border-box; }
p { margin: 0; }
ul { margin: 0; padding: 0; list-style: none; }
::selection { background: color-mix(in srgb, var(--w-color-action) 22%, transparent); }

.w { display: grid; gap: 10px; font-variant-numeric: tabular-nums; }
.headline { font-weight: 700; letter-spacing: -0.01em; text-wrap: balance; }
.detail { color: var(--w-color-muted); line-height: 1.45; }
.question { font-weight: 700; letter-spacing: -0.01em; }

.badge { display: inline-flex; align-items: center; gap: 6px; width: fit-content; padding: 3px 10px 3px 8px;
  border-radius: 999px; font-size: 12px; font-weight: 600; line-height: 18px; }
.badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.badge.calm { background: var(--w-color-surface-2); color: var(--w-color-muted); }
.badge.check { background: var(--w-color-check-soft); color: var(--w-color-check); }
.badge.alert { background: var(--w-color-alert-soft); color: var(--w-color-alert); }
.badge.ok { background: var(--w-color-ok-soft); color: var(--w-color-ok); }

.facts { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 13px; }
.facts li { display: inline-flex; align-items: center; gap: 6px; color: var(--w-color-ink); }
.facts svg { flex: none; }
.facts .absent svg, .facts .unknown svg { color: var(--w-color-muted); }
.facts .present svg { color: var(--w-color-ok); }
.facts .warn { color: var(--w-color-check); font-weight: 600; }

.clock { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--w-color-muted); }
.clock.urgent { color: var(--w-color-check); font-weight: 600; }
.holder { font-size: 13px; color: var(--w-color-muted); }
.was { display: flex; flex-wrap: wrap; gap: 4px 10px; font-size: 13px; color: var(--w-color-muted); }
.was s { text-decoration-thickness: 1px; text-decoration-color: currentColor; }
.ref { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 12px;
  border-radius: 10px; background: var(--w-color-surface-2); font-size: 13px; }
.ref code { font-family: inherit; font-weight: 600; letter-spacing: 0.02em; }

.actions { display: flex; flex-wrap: wrap; gap: 8px; }
button { font: inherit; cursor: pointer; }
.btn { min-height: 44px; padding: 0 18px; border-radius: var(--w-radius-control); font-size: 14px; font-weight: 600;
  border: 1px solid transparent; transition: background-color .2s cubic-bezier(.16,1,.3,1), border-color .2s cubic-bezier(.16,1,.3,1); }
.btn.primary { background: var(--w-color-action); color: var(--w-color-action-ink); }
.btn.primary:hover { background: var(--w-color-action-strong); }
.btn.secondary { background: var(--w-color-surface); color: var(--w-color-ink); border-color: var(--w-color-line); }
.btn.secondary:hover { border-color: var(--w-color-muted); }
.btn[disabled] { opacity: .55; cursor: progress; }
.link { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0; border: 0; background: none;
  color: var(--w-color-action-strong); font-size: 14px; font-weight: 600; text-underline-offset: 3px; }
.link:hover { text-decoration: underline; }
:focus-visible { outline: 2px solid var(--w-color-focus); outline-offset: 2px; border-radius: 6px; }

/* orders-row: lives inside the host's order card */
.row .top { display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
.row .headline { font-size: 15px; line-height: 1.3; }
.row .detail { font-size: 13px; }
.row .actions .btn { min-height: 44px; padding: 0 16px; font-size: 13px; }

/* tracking-card: one card in the host's stack */
.card { padding: 16px; border-radius: var(--w-radius-surface); background: var(--w-color-surface); border: 1px solid var(--w-color-line);
  box-shadow: 0 1px 2px color-mix(in srgb, var(--w-color-ink) 5%, transparent), 0 6px 16px -8px color-mix(in srgb, var(--w-color-ink) 16%, transparent); gap: 12px; }
.card .headline { font-size: 17px; line-height: 1.3; }
.card .detail { font-size: 14px; }
.card .question { font-size: 16px; margin-top: 2px; }
.card .actions .btn { flex: 1 1 0; }

/* after-delivered: the main content of the host's post-delivery screen */
.screen { gap: 16px; }
.screen .headline { font-size: 22px; line-height: 1.25; }
.screen .detail { font-size: 15px; }
.screen .proof { display: grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); gap: 8px; }
.screen .proof li { display: grid; justify-items: center; gap: 6px; padding: 12px 6px; border-radius: 12px;
  background: var(--w-color-surface-2); font-size: 12px; text-align: center; line-height: 1.3; }
.screen .proof .absent svg, .screen .proof .unknown svg { color: var(--w-color-muted); }
.screen .proof .present svg { color: var(--w-color-ok); }
.screen .proof .warn { color: var(--w-color-check); font-weight: 600; }
.screen .ask { display: grid; gap: 12px; padding: 18px 16px; border-radius: var(--w-radius-surface); background: var(--w-color-surface);
  border: 1px solid var(--w-color-line); }
.screen .question { font-size: 20px; }
.screen .actions { display: grid; gap: 10px; }
.screen .actions .btn { min-height: 52px; font-size: 16px; }

/* resolution: what Cierto is doing about it */
.res { display: grid; gap: 10px; padding: 14px; border-radius: var(--w-radius-surface); background: var(--w-color-surface-2); }
.res-msg { line-height: 1.5; font-size: 14px; }
.remedy { display: grid; gap: 2px; padding: 10px 12px; border-radius: 10px; background: var(--w-color-surface);
  border-left: 3px solid var(--w-color-line); }
.remedy.ok { border-left-color: var(--w-color-ok); }
.remedy.check { border-left-color: var(--w-color-check); }
.remedy-title { font-weight: 700; font-size: 14px; letter-spacing: -0.01em; }
.remedy-detail { font-size: 13px; color: var(--w-color-muted); }
.case { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--w-color-muted); }
.case svg { flex: none; }
.steps summary { cursor: pointer; font-size: 13px; font-weight: 600; color: var(--w-color-action-strong); min-height: 32px;
  display: flex; align-items: center; list-style: none; }
.steps summary::-webkit-details-marker { display: none; }
.steps summary::after { content: "+"; margin-left: 6px; font-weight: 700; }
.steps[open] summary::after { content: "−"; }
.steps ol { margin: 6px 0 0; padding: 0; list-style: none; display: grid; gap: 8px; }
.steps li { display: grid; grid-template-columns: auto 1fr; gap: 2px 10px; font-size: 13px; line-height: 1.4; }
.steps .who { font-weight: 600; }
.steps time { grid-column: 1 / -1; font-size: 12px; color: var(--w-color-muted); }
.row .res { padding: 12px; }
.screen .res-msg { font-size: 15px; }

@keyframes settle { from { transform: translateY(6px); } to { transform: none; } }
.changed .headline, .changed .question, .changed .res { animation: settle .5s cubic-bezier(.16,1,.3,1); }
@media (prefers-reduced-motion: reduce) { .changed .headline, .changed .question, .changed .res { animation: none; } .btn { transition: none; } }
`
