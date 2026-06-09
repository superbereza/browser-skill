# ADR 2026-06-09: Persistent daemon, not a stateless CLI

**Status:** Accepted

## Context

The skill is driven by an agent issuing one command at a time (`browser snapshot`,
`browser click e7`, …). Each command needs the live browser **page**, the **CDP
connection**, and the **ref-map** (the `e7 → element` mapping produced by the last
snapshot). Two process models were on the table:

- **Stateless CLI** — every command is a fresh process that re-attaches via
  `connect_over_cdp`, does one action, exits. State that must survive between
  commands (the ref-map) is persisted to a file in `/tmp`; because refs from one
  process don't survive into the next, a **version/stale-guard** is needed so a
  `click` against a stale ref fails loudly instead of clicking the wrong thing.
- **Persistent daemon** — a background process holds the connection, the page, and
  the ref-map in memory. A thin CLI client forwards each command over a unix socket.

The stateless model has two recurring costs the user pushed back on directly:
re-connecting on **every** command (~150 ms each), and the hand-rolled
**stale-guard** that exists only because in-memory refs don't survive a process.

## Decision

Use a **persistent, auto-managed daemon** with a thin CLI client over a unix
socket. The daemon holds: one long-lived `connect_over_cdp` connection, the current
page/tab, and the ref-map as **live Playwright locators in memory**.

Lifecycle is invisible to the caller:

- **Auto-spawn:** the first `browser` command finds no socket → spawns the daemon
  detached → connects. Subsequent commands reuse it.
- **Auto-respawn:** a dead socket (crash, browser closed) → client respawns.
- **`browser stop`** kills only the daemon; the browser and its tabs stay alive.
  **`browser quit`** kills the daemon *and* closes the browser.
- **Idle auto-shutdown:** a watchdog ends the daemon after N minutes (default 15)
  with no command. Each command resets the timer; respawn is cheap.

## Consequences

- **Positive — the stale-guard disappears.** Refs are stored as lazy Playwright
  locators (`page.get_by_role(role, name=…)`), not strings in a file. A locator
  re-resolves on the live page at click time: page re-rendered but the element is
  still there → it just works; element truly gone → Playwright raises a *truthful*
  "resolved to 0 elements" error. We don't add a guard — Playwright tells the truth.
- **Positive — no per-command reconnect.** One connection, held open.
- **Positive — enables capabilities statelessness can't:** JS dialog handling needs
  a `page.on("dialog")` handler registered *before* the dialog fires; downloads and
  long waits likewise need a living page. Only a persistent process can do these.
- **Negative / accepted — a lifecycle exists.** Neutralized by auto-spawn /
  auto-respawn (never started by hand) and idle-shutdown (never lingers).
- **Negative / accepted — soft state loss on idle.** After idle-shutdown the
  in-memory ref-map is gone, so a `click e7` 20 minutes later fails with
  "ref expired, run snapshot". Acceptable: this is a long-pause event, not
  per-command, and re-snapshotting after a pause is natural anyway.
- This is a persistent-server model, modernized: a unix socket instead of an HTTP
  port, and auto-managed instead of manually started.

## Alternatives considered

- **Stateless CLI + `/tmp` ref-file + version stale-guard** — rejected: pays the
  reconnect cost on every call and forces a hand-rolled stale-guard that exists
  purely to compensate for not having a process. Both are pure overhead the daemon
  removes. (Note: the file-based ref-map was validated in a spike and *works* — it
  was rejected on ergonomics, not feasibility.)
- **In-process library (no CLI, agent writes Python inline)** — rejected: repeated
  attach boilerplate per snippet and shell-quoting pain for `type` with arbitrary
  text; a thin CLI over a daemon is the better driving surface for an agent.
- **HTTP server on a TCP port** — rejected in favor of a unix socket: no port
  allocation, no "is the port taken", local-only by construction.
