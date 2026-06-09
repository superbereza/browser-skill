# ADR — Architecture Decision Records

Immutable snapshots of **architectural choices** for `browser-skill` — what was
decided, when, and why.

Use these for irreversible-feeling decisions that shape the tool itself: the
automation engine, the process model, how we attach to the browser, how captcha
is handled, what we deliberately rejected.

**Out of scope:** process decisions (release flow, doc conventions). Those live
in `CLAUDE.md` / the skill manifest — not here. An ADR answers "how is the tool
built", not "how do we work on it".

## Naming

`YYYY-MM-DD-decision-name.md` — e.g. `2026-06-09-patched-playwright.md`.

## What an ADR contains

```markdown
# ADR YYYY-MM-DD: <Decision Name>

**Status:** Accepted | Superseded by ADR YYYY-MM-DD-other.md
**Context:** what came up, what constraints applied
**Decision:** what we chose
**Consequences:** what flows from it (positives and negatives)
**Alternatives considered:** brief notes on what we rejected and why
```

## Conventions

- One ADR = one decision. Don't bundle.
- ADRs are **immutable** once accepted. To change a decision: write a new ADR with
  `Status: Accepted`, and edit the old one to `Status: Superseded by ADR …`.
- ADRs explain *why*. The SKILL.md / manifest describes *what* and *how to use*.
- Reference ADRs from `CLAUDE.md` so a future reader finds the rationale fast.

## Index

- [Patchright as the engine](2026-06-09-patched-playwright.md)
- [Persistent daemon, not a stateless CLI](2026-06-09-daemon-not-stateless-cli.md)
- [Built-in `aria_snapshot`, no custom AX filter](2026-06-09-builtin-aria-snapshot.md)
- [Dedicated profile, not the default one](2026-06-09-dedicated-profile-not-real.md)
  — supersedes [~~the default-profile attach~~](2026-06-09-attach-real-user-profile.md)
- [Captcha handling — detect, then escalate by choice](2026-06-09-captcha-handling.md)
