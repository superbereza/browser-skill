"""Compact, clickable page snapshot.

Base is Playwright's built-in ``aria_snapshot`` (see ADR
2026-06-09-builtin-aria-snapshot — we do NOT hand-roll an AX filter). We attach a
``[ref=eN]`` to each interactive line and return a ref-map so ``click e7`` resolves
back to a live locator via ``get_by_role``.
"""
from __future__ import annotations

import re

# Roles we expose as clickable refs.
INTERACTIVE = {
    "button", "link", "textbox", "searchbox", "checkbox", "radio", "combobox",
    "menuitem", "menuitemcheckbox", "menuitemradio", "tab", "option", "switch",
    "slider", "spinbutton",
}

# Matches an aria_snapshot YAML line:  `  - button "Найти билеты"` (name optional).
_LINE = re.compile(r'^(\s*)- ([a-z][a-z0-9-]*)(?:\s+"((?:[^"\\]|\\.)*)")?')


def _unescape(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def snapshot(page) -> tuple[str, dict]:
    """Return (text, refmap). refmap: ref -> {role, name, nth}."""
    aria = page.locator("html").aria_snapshot()
    lines, refs, counts, i = [], {}, {}, 0
    for ln in aria.splitlines():
        m = _LINE.match(ln)
        if m and m.group(2) in INTERACTIVE and m.group(3) is not None:
            role, name = m.group(2), _unescape(m.group(3))
            n = counts.get((role, name), 0)
            counts[(role, name)] = n + 1
            i += 1
            ref = f"e{i}"
            refs[ref] = {"role": role, "name": name, "nth": n}
            lines.append(f"{ln}  [ref={ref}]")
        else:
            lines.append(ln)
    return "\n".join(lines), refs


def locator_for(page, refs: dict, ref: str):
    """Resolve a ref to a live locator. Raises if the ref is unknown."""
    e = refs.get(ref)
    if not e:
        raise ValueError(f"unknown ref '{ref}' — run `snapshot` first")
    loc = page.get_by_role(e["role"], name=e["name"], exact=True)
    # disambiguate duplicates by the occurrence index recorded at snapshot time
    if e.get("nth"):
        loc = loc.nth(e["nth"])
    return loc
