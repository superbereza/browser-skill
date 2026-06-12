# ADR 2026-06-12: AI snapshot with native refs (`aria_snapshot(mode="ai")`)

**Status:** Accepted — refines [2026-06-09-builtin-aria-snapshot](2026-06-09-builtin-aria-snapshot.md)

## Context

The 2026-06-09 ADR settled the snapshot *body* on Playwright's built-in `aria_snapshot()`.
But we still hand-rolled the **ref layer** on top: parse the YAML, attach `[ref=eN]` only to
lines that are an interactive role **with a name**, and resolve a ref back to an element via
`get_by_role(role, name=name, exact=True).nth(n)`.

That ref layer had a real failure mode, hit in practice: an **icon-only / nameless button**
(a `⋮` kebab menu, a bare `✕`) has no accessible name, so the plain `aria_snapshot()` doesn't
name it and our parser skipped it — **no ref at all**. The agent then had to fall through the
targeting ladder to `eval` + manual coordinates, which is exactly where the quote/JSON-escaping
and coordinate pain showed up. Even when a nameless element *did* get a ref, resolving it by
`get_by_role(name="")` is ambiguous and `nth`-fragile.

`patchright` (1.60.1) exposes a cleaner public path: `aria_snapshot(mode="ai")` — the same
snapshot the Playwright MCP uses — which assigns a stable `[ref=eN]` to **every** addressable
element (named or not), and the built-in `aria-ref=` selector engine resolves each ref to the
**exact** element by identity. (Verified: the method/signature exist in the installed
`patchright`; `aria-ref` ships in the driver bundle. The private `_snapshot_for_ai` is *not*
exposed in Python, so we use the public `mode="ai"` instead — no version pin, no defensive
wrapping of a private API.)

## Decision

Build the snapshot with **`page.locator("html").aria_snapshot(mode="ai")`** and resolve refs
with **`page.locator(f"aria-ref={ref}")`**. Drop the hand-rolled role/name/`nth` ref map.

- `click <ref>` now works for almost everything, including nameless icon buttons — the targeting
  ladder (`--selector` → `--at` → `eval`) becomes a rare fallback, not the daily path.
- Refs resolve by node identity, not by re-finding via role+name (no wrong-match, no `nth` drift).
- Still "built-in, no custom AX filter" — fully consistent with the 2026-06-09 decision; this
  only changes which built-in variant we call and how refs resolve.

## Consequences

- `snapshot()` returns `(text, refs)` where `text` already carries `[ref=eN]` and `refs` is just
  the set of valid ids (for an "unknown ref — run `snapshot` first" guard). `locator_for` is a
  one-liner over `aria-ref=`.
- `mode="ai"` includes more structure than the old interactive-only filter, so a snapshot can be
  larger. If token size becomes an issue, `aria_snapshot(depth=…)` can bound it (deferred).
- Refs are tied to the most recent AI snapshot; our flow already re-snapshots after each action,
  so the ids the agent holds stay valid until its next action.
- `mode="ai"` also accepts `boxes=True` (geometry inline) — not enabled now; a future `--boxes`
  could surface coordinates when truly needed.
