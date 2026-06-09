# ADR 2026-06-09: Built-in `aria_snapshot`, no custom AX filter

**Status:** Accepted

## Context

The agent's "eyes" are a compact, clickable representation of the page. An earlier
hand-rolled approach built this directly over CDP: fetch the raw accessibility tree
(`Accessibility.getFullAXTree`), drop `ignored` / `none` / `generic` / `InlineTextBox`
nodes, then assign versioned UIDs and render an indented tree. The natural assumption
was to **port** that "interesting-nodes" filter as our snapshot edge.

A live three-way comparison was run on a real page (a synthetic flight-search form,
98 raw AX nodes) with Playwright:

- **Raw** `getFullAXTree` — 98 nodes, unusable noise.
- **`page.aria_snapshot()`** (Playwright built-in) — 30 lines, correctly nested,
  interactive elements kept with their values, noise dropped.
- **The hand-rolled filter** — 55 lines, but **structurally broken**: the form's text
  inputs were **orphaned out of the form** to the root,
  and date-picker internals (`spinbutton`, `StaticText`, `ListMarker`) leaked in.

Root cause of the breakage: when you drop a `generic` wrapper but rebuild the tree
from `parentId/childIds`, any child of a dropped node loses its parent
(`parentId not in lookup`) and floats up as a fake root. Playwright's snapshot
re-parents orphans to the surviving ancestor correctly; our naive filter did not.

## Decision

**Do not write our own AX filter.** Base the snapshot on Playwright's built-in
`page.aria_snapshot()`. Add only the thin layer it lacks:

1. **Clickable refs** — `aria_snapshot()` YAML carries no refs, so we attach our own
   `[ref=eN]` per interactive line and map `eN → get_by_role(role, name)`.
2. **Ref-map in daemon memory** — held as live locators (see the daemon ADR), not a
   custom versioning scheme.

The compaction, nesting, noise-dropping, and orphan re-parenting — the actual hard
parts — are delegated to Playwright, which does them measurably better than the
ported code.

## Consequences

- **Positive:** correct structure (interactive elements stay in context), less
  noise, far less code to own. Empirically validated, not assumed.
- **Positive:** tracks Playwright improvements for free.
- **Negative / accepted:** we depend on Playwright's snapshot format and its
  evolution. Acceptable — it is the maintained, better-engineered path, and the
  ref layer we add is small and under our control.
- The versioned-UID + stale-guard ideas from the hand-rolled approach are **dropped**,
  not ported — the daemon's in-memory live locators replace them.

## Alternatives considered

- **Port the hand-rolled CDP filter** — rejected: empirically worse (orphans
  interactive elements, leaks noise) and more code to maintain.
- **Playwright's internal `_snapshot_for_ai()`** (the `[ref=eN]` format used under
  the MCP server) — not exposed in the public sync API; reproduced cheaply by
  attaching our own refs over `aria_snapshot()`, which was validated to resolve and
  click correctly via `get_by_role`.
