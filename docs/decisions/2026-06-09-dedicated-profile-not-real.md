# ADR 2026-06-09: Dedicated profile, not the real default profile

**Status:** Accepted (supersedes ADR 2026-06-09-attach-real-user-profile.md)

## Context

The earlier ADR (`attach-real-user-profile`) chose to attach to the user's **real
default profile**, restarting the browser to expose the debug port. Smoke-testing on
the Mac **empirically falsified that approach**:

- **Chrome/Chromium 136+ ignores `--remote-debugging-port` on the *default*
  profile.** This is deliberate anti-cookie-theft hardening: infostealer malware was
  attaching to users' logged-in browsers via CDP to dump cookies/passwords (session
  cookies bypass 2FA). A non-default `--user-data-dir` is required, and it uses a
  *different encryption key*, so a debugged profile can't yield the real secrets.
  ([Chrome blog](https://developer.chrome.com/blog/remote-debugging-port))
- Confirmed live: temp instances launched with `--user-data-dir=/tmp/...` attached
  flawlessly; relaunching the user's real (default) Yandex with the port **never
  opened it** (Yandex is Chromium 146). There is **no override** — Google removed it;
  the only sanctioned automation paths are a non-default profile or "Chrome for
  Testing".

So attaching to the real default profile is **impossible**, not merely awkward.

## Decision

Use a **dedicated, non-default profile** at `~/.browser-skill/profiles/<browser>`.

- `launch` starts a **separate instance** of the chosen browser (`open -na` + the
  dedicated `--user-data-dir` + the debug port) that runs **alongside** the user's
  main browser. Distinct profile dirs coexist (proven). **No restart, fully
  non-destructive — the user's main browser is never touched.**
- The user **logs into their accounts once** in this profile; cookies/sessions then
  persist, so it becomes "them" for those sites. "As me" → "as me after a one-time
  login".
- `quit` closes **only our instance** (`pkill -f <profile_dir>`); `stop` leaves it
  running. Neither affects the user's main browser.
- Real-default-profile attach is documented as impossible; `--profile <dir>` lets an
  advanced user point at any non-default dir they choose.

## Consequences

- **Positive:** fully non-destructive — the user's real browser, tabs, and session
  are never disturbed (the original ADR's whole risk class is gone).
- **Positive:** reliable — the port always opens on a non-default dir; no quit /
  restore-session race.
- **Positive:** simpler launch state machine (`attached | launched`, no restart).
- **Negative / accepted:** it is **not literally the user's main profile** — a
  one-time login per browser is required, and the "looks like a long-lived real
  session" point is slightly weaker. Mitigated: a logged-in, lived-in, headed profile
  that accrues real history/cookies over time still reads as an ordinary session.
- **Negative / accepted:** a second browser instance/window runs during automation.

## Alternatives considered

- **Real default profile (the superseded ADR)** — rejected: impossible under
  Chrome/Chromium 136+ security. Empirically falsified.
- **Copy the real profile into a dedicated dir** (to inherit logins without manual
  login) — deferred as an *optional* future seed. Plausible (Chromium's cookie
  encryption key lives in the macOS Keychain per-browser/per-user, so a copy on the
  same machine can decrypt), but fragile across browser versions and racy against the
  live profile. Not in core.
- **"Chrome for Testing"** — rejected: a separate browser binary, not the user's
  actual browser; defeats the "as me" intent with no offsetting gain here.
