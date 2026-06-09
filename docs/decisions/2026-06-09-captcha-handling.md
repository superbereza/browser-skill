# ADR 2026-06-09: Captcha handling — detect, then escalate by choice

**Status:** Accepted

## Context

When the agent (a stand-in for the person at the keyboard) runs into a captcha during
ordinary operation, it needs a way through.

The obvious naive approach is a **bespoke deterministic per-captcha handler**: detect a
known captcha by signature (a URL marker or an iframe), then act on it with hardcoded
steps — e.g. clicking a checkbox at fixed coordinates, with a selector fallback — then
hand off to a human or give up. It works for one captcha type but is brittle (hardcoded
offsets break on any layout change), narrow (one provider, checkbox-only), and really
only fits unattended high-volume runs.

The initial proposal mirrored that: daemon detects → daemon acts deterministically → if
unknown, hand to the agent → optional external service. Challenged through two lenses:

- **Musk's algorithm.** *Question the requirement:* determinism mainly pays off for
  unattended, high-volume runs; here it's an agent in the loop at low volume, so
  captchas are infrequent. *Delete:* a hand-rolled deterministic handler is brittle,
  narrow, and redundant with the agent that can already see and click. *Automate
  (last):* a paid service is the final, optional step.
- **Huang's first principles.** The most *general* path is the multimodal agent that
  sees and acts — route there, not to narrow code. And the coordinate tools are a
  general **vision/interaction layer** (canvas, maps, sliders, drag-drop), not a
  captcha-specific thing — a platform investment. Captcha is adversarial and never
  "done" → graceful degradation + **instrument every encounter**.

## Research (2026-06-09): existing libraries

The "is a deterministic path just one dependency?" question was searched:

- **`playwright-captcha`** (PyPI, MIT, v0.1.5) — supports Patchright. A free
  **click-based** path for **Cloudflare Turnstile + Interstitial**, plus an **API**
  path (2Captcha / TenCaptcha) for Cloudflare + reCAPTCHA v2/v3 that handles
  sitekey→token→inject. → chosen as the one optional library dependency.
- **`playwright-recaptcha`** — free reCAPTCHA via an audio challenge, needs `ffmpeg`.
  Optional extra, deferred.
- **`hcaptcha-challenger`** (GPL-3.0, local ONNX models) — copyleft, heavy, and
  overlaps the multimodal agent. Not in core.

So a clean one-dependency path exists for Cloudflare/Turnstile, partly elsewhere, and
not for every provider.

## Decision

A layered ladder. **Detection is deterministic; what happens next escalates from
cheap+narrow to general. The agent chooses the path** (and may ask the person which is
convenient). No hand-rolled per-captcha handler in v1; the spicier paths are opt-in.

| Tier | What | Cost |
|------|------|------|
| **0 — Avoidance** | a real, headed browser at human pace. Most captchas never appear. | architecture |
| **1 — Detect & classify** | daemon flags a captcha on each snapshot/navigation via **bounded signatures** (URL markers; iframe `smartcaptcha`/`recaptcha`/`hcaptcha`/`turnstile`; "I'm not a robot"). Emits `{present, type, sitekey?}`. **Never acts on its own.** | deterministic |
| **1.5 — Library** | optional `playwright-captcha` click path for **Cloudflare/Turnstile**. Invoked by the agent via `captcha solve`, not automatically. | free, local |
| **2 — Agent (vision)** | agent uses `screenshot`, `click --at x,y`, `drag x1,y1 x2,y2` — the same way a person would point and click. | agent round-trip |
| **2.5 — Ask the human** | `captcha ask-human` brings the window to front; the person handles it in the visible browser. | human |
| **3 — External service** | `captcha solve --method api` via `playwright-captcha`'s 2Captcha path. Requires a configured key. **Off by default.** | paid |

**The path is the agent's decision, not a fixed cascade.** Detection only flags; the
agent picks among the tools, and is expected to **ask the person when they're in the
loop**, e.g. *"a captcha came up — want to handle it in the window, or should I try?"*
— then call the matching tool.

### Captcha tool surface (agent-invokable)

- `browser captcha status` — detect + classify (type, where, sitekey).
- `browser captcha solve [--method auto|click|api]` — library (tier 1.5) or service
  (tier 3) via `playwright-captcha`; `auto` = click if a free path exists, else fail
  with a hint to escalate.
- `browser captcha ask-human [--message "..."]` — tier 2.5: surface it, bring the
  window to front, wait.
- Tier 2 uses the **general** `screenshot` / `click --at` / `drag` tools, not
  captcha-specific ones.

**Telemetry:** every encounter is logged (type, url, tier that resolved it, outcome).
That data — not a guess — decides whether a specific library or shortcut is worth
adding later (closing Musk's "add back 10%" loop).

## Consequences

- **Positive:** minimal core — deterministic detect, then the agent's general ability;
  no brittle hardcoded-offset handler to rot. The spicier library/service paths are
  opt-in.
- **Positive:** the agent works *with* the person by choice, not via a blocking
  prompt — it can weigh "convenient for you?" against effort and pick.
- **Positive:** the vision/coordinate layer pays off well beyond captcha.
- **Negative / accepted:** reCAPTCHA/hCaptcha have no free *library* path in core v1 —
  they go to the agent (tier 2) or service (tier 3); telemetry will say if a library is
  worth adding.
- **Negative / accepted:** an interactive captcha the agent handles costs a round-trip,
  not microseconds — fine at this skill's volume.
- **Negative / accepted:** image/slider challenges are probabilistic — no guarantee;
  fall through to 2.5/3.

## Alternatives considered

- **A bespoke deterministic per-captcha handler** — rejected: brittle hardcoded
  offsets, single-provider, redundant with the agent. A candidate to add back *only*
  if telemetry justifies it.
- **`hcaptcha-challenger`** — rejected for core: GPL-3.0 (copyleft, awkward to
  redistribute), heavy ONNX models, overlaps the multimodal agent.
- **Hand-rolling the API token relay** — rejected: `playwright-captcha` already does
  sitekey extraction + token injection.
- **Leading with the external service** or a **blocking human handoff** — rejected as
  the primary path: the service is "automate last" and paid; the human path survives as
  an *agent-invoked* tool (tier 2.5), not a blocking gate.
