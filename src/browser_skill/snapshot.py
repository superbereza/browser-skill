"""Compact, clickable page snapshot.

Uses Playwright's built-in **AI snapshot** — ``aria_snapshot(mode="ai")`` — which tags
every addressable element with a stable ``[ref=eN]``, *including icon-only / nameless*
buttons (a ``⋮`` kebab, a bare ``✕``) that a plain ``aria_snapshot`` can't name. Each ref
resolves back to the **exact** element by identity via the built-in ``aria-ref=`` selector
engine — no ``get_by_role`` name-guessing, no ``nth`` drift.

Supersedes the hand-rolled ref map (which only named interactive roles, so nameless
elements never got a ref). See ADR 2026-06-12-ai-ref-snapshot.
"""
from __future__ import annotations

import re

_REF = re.compile(r"\[ref=([^\]\s]+)\]")


def snapshot(page) -> tuple[str, set]:
    """Return ``(text, refs)``. ``text`` already carries ``[ref=eN]`` markers (assigned by
    Playwright's AI snapshot); ``refs`` is the set of valid ref ids for that snapshot."""
    text = page.locator("html").aria_snapshot(mode="ai")
    return text, set(_REF.findall(text))


def locator_for(page, refs, ref: str):
    """Resolve a ref to a live locator via the built-in ``aria-ref=`` engine.

    The ref must come from the most recent snapshot (Playwright ties ``aria-ref`` ids to it).
    """
    if not refs or ref not in refs:
        raise ValueError(f"unknown ref '{ref}' — run `snapshot` first")
    return page.locator(f"aria-ref={ref}")
