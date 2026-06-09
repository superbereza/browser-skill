# ADR 2026-06-09: Patchright as the automation engine

**Status:** Accepted

## Context

The skill drives a real browser from an agent. We needed to pick the driving engine.
Candidates:

- **Selenium + undetected-chromedriver** — a common browser-automation stack. Heavy,
  WebDriver-based, weaker snapshot model.
- **Raw CDP** — driving the browser over the Chrome DevTools Protocol directly.
  Maximum control, but we'd maintain everything ourselves (accessibility-tree fetch,
  click resolution, tab handling, dialogs).
- **Vanilla Playwright** — modern API, `connect_over_cdp` to attach to a running
  browser, a built-in `aria_snapshot`. But as a CDP client it emits
  automation-detectable patterns (notably `Runtime.enable`) that some sites flag.
- **Patchright** — a drop-in, API-compatible patched fork of Playwright that removes
  those well-known CDP-detectable patterns.

A spike confirmed Playwright's `connect_over_cdp` attaches to a running browser,
returns rich snapshots, and works well headed.

## Decision

Use **Patchright** (a patched Playwright fork) as the engine, attaching to a running
browser via `connect_over_cdp`.

Rationale, layered:

1. **Playwright over Selenium / raw CDP** — a modern attach model and a strong
   built-in accessibility snapshot (`aria_snapshot`), which proved better than a
   hand-rolled CDP AX filter (see the `builtin-aria-snapshot` ADR). Raw CDP would
   mean re-implementing snapshot, clicking, tabs, and dialogs ourselves; Playwright
   gives all of it.
2. **Patchright over vanilla Playwright** — drop-in (same API, zero code cost) and it
   removes CDP-detectable automation patterns. There's no reason to ship the
   detectable variant when the patched one is API-identical.

**How the patches apply in attach mode (important):** Patchright has two kinds of
patches. *Launch-flag* patches (e.g. `--disable-blink-features=AutomationControlled`)
apply only when Playwright launches the browser — we don't (the browser is started
separately and we attach), so those don't apply, and we set no automation flags
ourselves anyway. *CDP-client-behavior* patches — chiefly **not calling
`Runtime.enable`** (a primary bot-detection signal) and using isolated execution
contexts — **do apply**, because in attach mode Patchright is the CDP client issuing
`evaluate`/`snapshot`/`click`. Those are the patches that matter, and they are live.

## Consequences

- **Positive:** API-identical to Playwright — knowledge transfers, and falling back to
  vanilla is a one-line import change. Built-in snapshot, tabs, dialogs, file chooser.
- **Positive:** the value-carrying patches (CDP-client behavior) are active in our
  attach setup, so ordinary automation doesn't trip CDP-level detection.
- **Negative / accepted:** a dependency on a third-party fork that tracks upstream
  Playwright. Mitigated by API compatibility (vanilla fallback), and the fork is
  reputably maintained with signed releases.
- **Negative / accepted:** launch-flag patches are inert in attach mode — acceptable,
  since we control how the browser is launched and set no automation flags.

## Alternatives considered

- **Selenium + undetected-chromedriver** — rejected: WebDriver indirection and a
  weaker snapshot model than Playwright's.
- **Raw CDP** — rejected: we'd maintain snapshot/click/tab/dialog logic ourselves, and
  a hand-rolled CDP accessibility filter was empirically *worse* than Playwright's
  built-in (it orphaned interactive nodes — see the snapshot ADR).
- **Vanilla Playwright** — rejected only relative to Patchright: same API, but its CDP
  client emits detectable patterns; no upside over the patched fork.
- **`playwright-stealth` on vanilla** — viable, but Patchright is the more maintained
  drop-in and needs no per-call plumbing.
