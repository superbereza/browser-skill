# RFC 2026-06-09: Coordinate-grid overlay for the vision layer

**Status:** Deferred — revisit after the core skill works, test in-situ.

## Question

The vision/coordinate layer lets the agent act on pixels when the accessibility tree
isn't enough — `screenshot`, `click --at x,y`, `drag x1,y1 x2,y2` — for things like
canvas widgets, map pins, sliders, and drawing surfaces. Open question: does overlaying
a **labeled coordinate grid** on the screenshot make the agent **measurably more
accurate** at naming click targets — and at what grid density?

The hypothesis: a multimodal agent estimates pixel coordinates imprecisely from a bare
screenshot; a grid (e.g. 50–100 px cells, labeled axes) gives it reference anchors and
should tighten targeting on any pixel-addressed element.

## Why deferred

- It is a **leaf** refinement of one fallback tier; the skill works without it
  (primary path is `snapshot` → `click <ref>`).
- A faithful answer needs an **A/B on real targets**, which needs the live
  `screenshot` pipeline and real pages — available only once the core skill runs.
  A synthetic mock now would be guesswork, against this project's "measure, don't
  assume" bar (cf. the snapshot three-way comparison that settled the AX decision).

## Proposed test (when we return)

1. Pick ~10 real targets across canvas controls / a slider / a map pin / a drawing surface.
2. For each: capture (a) bare screenshot, (b) same with a labeled grid overlay.
3. Have the agent name the click coordinate for the target from each variant.
4. Compare: distance from the true target center; success rate of the resulting
   `click --at`; sensitivity to grid density (none / 100 px / 50 px / adaptive).
5. Decide: ship grid by default, on-demand (`screenshot --grid`), or drop it.

## Outcome

Whatever the data says becomes an ADR (accept `screenshot --grid`, with the chosen
density) or a closed RFC (grid not worth it; bare screenshots suffice).
