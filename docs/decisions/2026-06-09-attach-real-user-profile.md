# ADR 2026-06-09: Attach to the default browser profile (superseded)

**Status:** Superseded by ADR 2026-06-09-dedicated-profile-not-real.md

## Summary (kept for the trail)

An early design attached to the browser's **default profile**, restarting the browser
to expose the remote-debugging port.

Smoke-testing falsified it: **Chrome/Chromium 136+ ignores `--remote-debugging-port`
on the default profile** (a deliberate security limit). The port simply never opens
there, so attaching to the default profile is impossible.

The decision was replaced by a **dedicated, non-default profile** that the user signs
into once, launched as a separate instance — which also turned out to be simpler and
non-destructive (it never touches the user's main browser).

→ See [ADR 2026-06-09-dedicated-profile-not-real.md](2026-06-09-dedicated-profile-not-real.md).
