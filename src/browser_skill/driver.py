"""Browser launch / attach (macOS).

We launch a SEPARATE browser instance on a **dedicated profile** (a non-default
`--user-data-dir`) and attach to it via CDP. This is forced by Chrome/Chromium 136+
security: `--remote-debugging-port` is ignored on the *default* profile (anti
cookie-theft hardening). A dedicated profile is non-default, so the port works — and
we never touch the user's main browser. See ADR 2026-06-09-dedicated-profile-not-real.

The user logs into their accounts once in this profile; sessions then persist, so it
becomes "them" for those sites.
"""
from __future__ import annotations

import subprocess
import time
import urllib.request


def _http_ok(port: int) -> bool:
    """True if a debuggable browser is listening on the CDP port."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def launch_instance(app: str, port: int, profile_dir: str, restore: bool = False) -> None:
    """Launch a separate instance of `app` on its own profile dir + debug port.

    `open -na` forces a new instance; the distinct `--user-data-dir` keeps it apart
    from the user's running browser (proven to coexist).
    """
    args = ["open", "-na", app, "--args",
            f"--remote-debugging-port={port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={profile_dir}",
            "--no-first-run", "--no-default-browser-check"]
    if restore:
        args.append("--restore-last-session")
    args.append("about:blank")
    subprocess.run(args, capture_output=True, text=True, timeout=20)


def ensure_browser(app: str, port: int, profile_dir: str) -> tuple[str, str]:
    """Make `app` attachable on `port` with the dedicated profile. Returns (action, note).

    action ∈ {"attached", "launched"}. Never restarts the user's main browser.
    """
    if _http_ok(port):
        return "attached", f"already debuggable on :{port}"
    launch_instance(app, port, profile_dir)
    for _ in range(60):  # up to 30s
        if _http_ok(port):
            return "launched", f"{app} on :{port} (profile {profile_dir})"
        time.sleep(0.5)
    raise RuntimeError(f"{app} did not expose debug port :{port} within 30s")


def kill_instance(profile_dir: str) -> None:
    """Close only *our* dedicated instance (matched by its profile dir). Precise —
    leaves the user's main browser untouched."""
    subprocess.run(["pkill", "-f", profile_dir], capture_output=True, text=True, timeout=10)
