# browser-skill — agent guide

Operate a real browser from a coding agent. A thin `browser …` CLI over an
auto-managed daemon (Patchright + `connect_over_cdp`).

## Documentation

- **[`docs/decisions/`](docs/decisions/)** — immutable ADRs: *why* the tool is built
  this way. Read these before changing architecture.

## Architecture decisions (index)

- Engine: **Patchright** (patched Playwright), attach via `connect_over_cdp`.
  [ADR](docs/decisions/2026-06-09-patched-playwright.md)
- Process model: **persistent auto-managed daemon** + thin CLI; no stateless
  reconnect, no stale-guard. [ADR](docs/decisions/2026-06-09-daemon-not-stateless-cli.md)
- Snapshot: **built-in `aria_snapshot`** + our refs; no custom AX filter (the old
  one was empirically worse). [ADR](docs/decisions/2026-06-09-builtin-aria-snapshot.md)
- Profile: a **dedicated non-default profile** (`~/.browser-skill/profiles/<browser>`),
  launched as a separate instance — the real default profile can't be CDP-attached
  (Chrome 136+ security). [ADR](docs/decisions/2026-06-09-dedicated-profile-not-real.md)
- Captcha handling: **deterministic detect → escalate by choice** (optional library →
  agent vision → ask the person → optional service); the agent picks. No bespoke handler.
  [ADR](docs/decisions/2026-06-09-captcha-handling.md)

## Command surface (planned)

`launch <name>` · `stop` · `quit` · `status` · `tabs` · `tab <sel>` ·
`snapshot` · `text [ref]` · `html [ref]` · `screenshot [path]` ·
`goto <url>` · `back` · `forward` · `reload` ·
`click <ref>` · `type <ref> <text>` · `press <key>` · `scroll <dir|ref>` ·
`hover <ref>` · `select <ref> <value>` ·
`new-tab [url]` · `close-tab [idx]` · `upload <ref> <path>` · `download <ref>` ·
`dialog accept|dismiss [text]` · `wait <sec>|--for <x>` · `eval <js>` ·
`captcha status` · `captcha solve [--method auto|click|api]` · `captcha ask-human [--message]`

Targeting ladder on `click`/`type`: `<ref>` → `--selector` → `--offset` → `--at x,y`,
then `eval` as the escape hatch. Actions print a fresh snapshot by default
(`--no-snap` to suppress).

## Status

Design locked (see ADRs). Next: scaffold the daemon, CLI client, and `SKILL.md`.
