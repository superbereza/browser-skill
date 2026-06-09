# browser

An adaptation of Playwright into a small CLI for driving a real browser from a
coding agent. Same engine underneath — exposed as a handful of `browser` commands on
a persistent daemon, with opinionated defaults chosen to make agent-driven browsing
actually pleasant.

The agent sees each page as a compact snapshot of the accessibility tree, where
every interactive element carries a short ref like `[ref=e7]`; it clicks and types by
ref, with a fallback ladder down to CSS selectors, coordinates, and JS. A background
daemon keeps one connection and the page's refs in memory, so commands share state
without reconnecting — it starts on first use, stops when idle.

The browser is real and headed, on a dedicated profile you sign into once. Launch
targets macOS; commands work cross-platform once attached.

Meant for automating browser tasks you'd otherwise do by hand.

## How it works

Built on **Patchright**, a patched Playwright fork, attached to the browser over CDP.
The patches keep the agent's automation traffic from tripping the CDP-level signals
some sites use to flag automation, so ordinary use behaves like an ordinary session.
Everything else is plain Playwright underneath.

The pieces:

- **CLI + daemon** — a thin `browser …` client talks to a background daemon holding
  one Patchright/CDP connection, the current page, and the snapshot refs. State lives
  in the daemon; it auto-starts on first use and auto-stops when idle.
- **Snapshot** — Playwright's `aria_snapshot` plus `[ref=eN]` refs; click/type by
  ref, falling back to CSS selectors, pixel coordinates, and JS.
- **Profile** — a dedicated profile you sign into once; sessions persist across runs.
- **Captcha** — detected deterministically; the agent works through it with the
  vision tools or hands it to you, with an optional solver you can wire up.

## Install

```bash
./install.sh          # symlinks `browser` into ~/.local/bin and the skill
browser --help        # first run bootstraps a venv (Python >=3.10) + installs deps
browser launch        # starts a dedicated-profile browser and attaches
```

macOS for `launch`. The dedicated profile is signed out on first run — log in once
and sessions persist. Full usage: [`skills/browser/SKILL.md`](skills/browser/SKILL.md).

## Design notes

Rationale for the non-obvious calls lives in [`docs/decisions/`](docs/decisions/):

- [Patchright as the engine](docs/decisions/2026-06-09-patched-playwright.md)
- [Persistent daemon, not a stateless CLI](docs/decisions/2026-06-09-daemon-not-stateless-cli.md)
- [Built-in `aria_snapshot`, no custom AX filter](docs/decisions/2026-06-09-builtin-aria-snapshot.md)
- [Dedicated profile](docs/decisions/2026-06-09-dedicated-profile-not-real.md)
- [Captcha handling](docs/decisions/2026-06-09-captcha-handling.md)

## Status

v0.1.0. Smoke-tested on macOS: launch/attach, snapshot + refs, navigation,
click/type/press/scroll/hover/select, tabs, upload/download, dialog, eval, wait. The
optional `playwright-captcha` solver path is scaffolded, not yet wired. Per-site
navigation guides are planned next.

## License

MIT — see [LICENSE](LICENSE).
