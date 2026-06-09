# browser-skill — agent guide

Operate a real browser from a coding agent — navigate, read, click, type, fill forms.
A thin `browser …` CLI over an auto-managed daemon (Patchright + `connect_over_cdp`);
pages are read as compact clickable snapshots.

The same skill is wired for several agents from one source:

- **Claude Code / Cursor / Codex** — load [`skills/browser/SKILL.md`](skills/browser/SKILL.md)
  (auto-discovered via `.claude-plugin/`, `.cursor-plugin/`, `.codex-plugin/`).
- **Gemini** — reads this file (`gemini-extension.json` → `contextFileName: AGENTS.md`).
- Full, authoritative usage: [`skills/browser/SKILL.md`](skills/browser/SKILL.md).

Requires `python3` (a venv is bootstrapped on first run) and macOS for `launch`.

## Invoking the CLI

`browser` is on PATH after `./install.sh`. Otherwise call `./bin/browser` from this
repo (or `${CLAUDE_PLUGIN_ROOT}/bin/browser` when loaded as a plugin). It
bootstraps its own venv — no build/setup step.

## Cheat sheet

```bash
browser launch [name]                # attach to the user's real browser (may restart it)
browser snapshot                     # compact clickable page view ([ref=eN])
browser goto <url> | click <ref> | type <ref> <text> | press <key>
browser tabs | tab <idx|url> | status
browser captcha status | captcha ask-human | captcha solve
browser stop                         # stop the daemon (browser stays open)
```

Architecture rationale lives in [`docs/decisions/`](docs/decisions/); open questions
in [`docs/rfc/`](docs/rfc/).

## Maintainer note

Changing the skill or CLI? For plugin consumers it propagates **only after a
release** — `scripts/bump.sh <v>` → commit → tag `vX.Y.Z` → GitHub release. A commit
on `master` alone propagates nothing (agents cache plugins by version string).
