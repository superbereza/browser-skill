"""Captcha: deterministic detect, agent-driven solve.

Per ADR 2026-06-09-captcha: detection is bounded/deterministic; SOLVING is the
agent's job (vision tools) with optional library/API fallback. We never auto-solve.
Every detection is logged for telemetry.
"""
from __future__ import annotations

import json
import time

from . import protocol

# Bounded signatures → captcha type.
_IFRAME_SIGNS = {
    "yandex_smartcaptcha": ["smartcaptcha"],
    "recaptcha": ["recaptcha"],
    "hcaptcha": ["hcaptcha"],
    "turnstile": ["turnstile", "challenges.cloudflare.com"],
}


def detect(page) -> dict:
    """Return {present, type, sitekey}. Deterministic; logs every hit."""
    info = {"present": False, "type": None, "sitekey": None}
    url = ""
    try:
        url = page.url or ""
    except Exception:
        pass

    if "showcaptcha" in url:  # Yandex SmartCaptcha redirect
        info.update(present=True, type="yandex_smartcaptcha")

    try:
        for frame in page.frames:
            src = frame.url or ""
            for ctype, keys in _IFRAME_SIGNS.items():
                if any(k in src for k in keys):
                    info.update(present=True, type=ctype)
    except Exception:
        pass

    if info["present"] and info["sitekey"] is None:
        try:
            el = page.query_selector("[data-sitekey]")
            if el:
                info["sitekey"] = el.get_attribute("data-sitekey")
        except Exception:
            pass

    _log(info, url)
    return info


def _log(info: dict, url: str) -> None:
    if not info.get("present"):
        return
    try:
        protocol.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(protocol.TELEMETRY_FILE, "a") as f:
            f.write(json.dumps({"t": int(time.time()), "url": url, **info}) + "\n")
    except Exception:
        pass


def ask_human(page, message: str | None = None) -> dict:
    """Tier 2.5: surface the captcha to the human in their visible browser."""
    try:
        page.bring_to_front()
    except Exception:
        pass
    return {
        "waiting": True,
        "message": message or
        "Solve the captcha in the visible browser window, then tell me to continue.",
        "hint": "After the human solves it, re-run `captcha status` to confirm it cleared.",
    }


def solve(page, method: str = "auto") -> dict:
    """Tier 1.5/3: library (Cloudflare click) or API solve via playwright-captcha.

    Honest scaffold: requires the optional `playwright-captcha` dependency. Wiring
    per captcha type is added as telemetry justifies it (see the captcha ADR).
    """
    try:
        import playwright_captcha  # noqa: F401
    except Exception:
        return {"error": "playwright-captcha not installed — "
                "`pip install playwright-captcha` for Cloudflare click / 2captcha API, "
                "or use the vision tools (screenshot / click --at) or `captcha ask-human`"}
    return {"error": "library solve is scaffolded but not yet wired for this captcha type; "
            "use the vision tools or `captcha ask-human` for now"}
