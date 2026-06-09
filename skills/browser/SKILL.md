---
name: browser
description: Operate a real, headed web browser — navigate, read pages as clickable accessibility snapshots, click, type, fill forms, switch tabs, upload and download files, and handle dialogs. Use for any task that needs driving a live browser end to end. A CLI over a persistent Playwright (Patchright) daemon.
---

# browser

Drive a real browser from a coding agent. The agent issues `browser …` commands; a
small auto-managed daemon holds the live browser session, so commands share state
(open tab, the last snapshot's refs) without reconnecting each time.

> **Invoking:** use `browser` if it's on PATH (after `install.sh`). If not — e.g.
> loaded as a plugin — call the bundled launcher `${CLAUDE_PLUGIN_ROOT}/bin/browser`
> (or `./bin/browser` from the repo). It bootstraps its own venv; no setup step.

## Mental model (read once)

- The **browser** is a separate process holding the dedicated profile and its tabs.
- A **daemon** attaches to it once (Patchright `connect_over_cdp`) and keeps the
  connection; each `browser` command talks to the daemon over a unix socket.
- The agent's **eyes** are `snapshot` — a compact, clickable list of the page; you
  click things by their `[ref=eN]`. This beats screenshots for precision.
- The daemon auto-starts on the first command and **auto-shuts down after 15 min
  idle** (the browser stays open). Nothing to start or stop by hand.

## First: attach

```bash
browser launch            # default browser (config)
browser launch chrome     # pick a browser: yandex | chrome | chromium | brave | edge
browser launch --list
```

`launch` starts a **separate browser instance on a dedicated profile**
(`~/.browser-skill/profiles/<browser>`) and attaches to it. It runs **alongside** the
user's normal browser and **never touches it** — no restart, nothing closed.

**Dedicated profile, not the default one:** the default profile can't be CDP-attached
(a deliberate browser-security limit), so the skill uses a dedicated one. **First run
it's signed out** — the user signs in once; sessions then persist, so it's
"them" from then on. If a task needs a login the profile doesn't have yet, tell the
user to log in once in that window.

## The loop

```bash
browser goto https://example.com    # navigate (prints a fresh snapshot)
browser snapshot                    # see the page: lines with [ref=eN]
browser click e12                   # click a ref
browser type e8 "hello world"       # type into a field (real keystrokes)
browser press Enter
```

Actions print a fresh snapshot **by default** so you see the result in one call.
Add `--no-snap` when you don't need it (saves tokens).

## Command reference

| Group | Commands |
|---|---|
| Session | `launch [name] [--port N] [--profile DIR]` · `stop` (daemon only, browser stays) · `quit` (daemon + browser) · `status` · `tabs` · `tab <idx\|url-substr>` |
| Look | `snapshot` · `text [ref]` (innerText) · `html [ref]` · `screenshot [path] [--full]` |
| Navigate | `goto <url>` · `back` · `forward` · `reload` |
| Act | `click <ref>` · `type <ref> <text…>` `[--instant]` · `press <key>` · `scroll <down\|up\|ref>` · `hover <ref>` · `select <ref> <value>` |
| Tabs / IO | `new-tab [url]` · `close-tab [idx]` · `upload <ref> <path>` · `download <ref>` |
| Misc | `wait <sec>` · `wait --for <css>` · `eval <js…>` · `dialog [--policy accept\|dismiss]` |
| Captcha | `captcha status` · `captcha solve [--method auto\|click\|api]` · `captcha ask-human [--message …]` |

### Targeting ladder (when a ref won't do)

`click` / `type` escalate: `<ref>` → `--selector <css>` → `--selector <css> --offset x,y`
→ `--at x,y` (absolute pixels). `eval "<js>"` is the universal escape hatch.

```bash
browser click e7                          # 1. by ref (preferred)
browser click --selector "#submit"        # 2. by CSS
browser click --selector ".cta" --offset 10,10   # 3. selector + pixel offset
browser click --at 640,480                # 4. absolute coordinates (canvas/captcha)
browser eval "document.querySelector('#go').click()"   # 5. JS
```

## Captcha

On a real browser at human pace, captchas are rare. When one appears, the ladder is
**your choice** — pick by what's convenient:

1. `captcha status` — detect + classify (type, sitekey).
2. **Solve it yourself** with the vision tools: `screenshot`, then `click --at x,y`.
3. **Ask the person** — `captcha ask-human` brings the window to front so they can
   solve it in the visible browser. Often the simplest: *ask first if that's
   convenient* before spending effort or credits.
4. **Solver** — `captcha solve` (needs the optional `playwright-captcha` dep, and an
   API key in config for the paid path). Off by default.

A coordinate-grid overlay to make tier-2 clicking easier is a deferred idea
(`docs/rfc/2026-06-09-coordinate-grid-overlay.md`) — not built yet.

## Recipes

**Read a page's prose:** `goto <url>` → `text` (whole page) or `text <ref>` (a part).

**Fill + submit a search:**
```bash
browser goto https://example.com
browser snapshot                     # find the input + button refs
browser type e8 "query" && browser press Enter
```

**Skip an interactive flow with a URL formula** (see per-site guides, if present):
many sites encode the whole search in the URL — `goto` straight to results instead of
clicking through; fewer steps, more robust.

## Notes

- macOS only for `launch` (uses `open` to start the browser app).
- We attach to a **dedicated-profile instance** we launch — no separate Chromium is
  downloaded, and the user's main browser is never touched. The default profile can't
  be CDP-attached (a browser-security limit), which is why the profile is dedicated and
  signed into once.
- A real, headed, logged-in profile is what makes ordinary use behave like an ordinary
  session; Patchright handles the CDP-level details. See `docs/decisions/`.
- Config: `~/.browser-skill/config.json` (default browser, port, idle minutes,
  browser registry, captcha solver key). Captcha telemetry: `~/.browser-skill/captcha.log`.
