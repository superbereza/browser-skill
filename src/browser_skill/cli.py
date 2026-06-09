"""Thin CLI client. Parses argv, ensures the daemon is up (auto-spawn), forwards
the command over the socket, and renders the reply.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

from . import protocol

USAGE = """browser — drive your own browser as you

Session:   launch [name] [--port N] [--profile DIR] | launch --list
           stop | quit | status | tabs | tab <idx|url-substr>
Look:      snapshot | text [ref] | html [ref] | screenshot [path] [--full]
Navigate:  goto <url> | back | forward | reload
Act:       click <ref|--selector CSS|--at x,y> [--offset x,y]
           type <ref> <text...> [--instant] | press <key>
           scroll <down|up|ref> | hover <ref> | select <ref> <value>
Tabs/IO:   new-tab [url] | close-tab [idx] | upload <ref> <path> | download <ref>
Misc:      wait <sec> | wait --for <css> | eval <js...> | dialog [--policy accept|dismiss]
Captcha:   captcha status | captcha solve [--method auto|click|api] | captcha ask-human [--message M]

Actions print a fresh snapshot by default; pass --no-snap to suppress.
"""

# command -> ordered positional arg names; a trailing '*' joins the remaining argv.
POSITIONALS = {
    "launch": ["name"],
    "goto": ["url"],
    "click": ["ref"],
    "type": ["ref", "text*"],
    "press": ["key"],
    "scroll": ["dir"],
    "hover": ["ref"],
    "select": ["ref", "value"],
    "text": ["ref"],
    "html": ["ref"],
    "tab": ["sel"],
    "new-tab": ["url"],
    "close-tab": ["idx"],
    "upload": ["ref", "path"],
    "download": ["ref"],
    "wait": ["sec"],
    "eval": ["js*"],
    "screenshot": ["path"],
    "captcha": ["sub"],
}

# flags that consume the next token as their value
_VALUE_FLAGS = {"selector", "profile", "method", "message", "port", "for",
                "timeout", "text", "policy", "path", "url"}
_BOOL_FLAGS = {"no-snap", "instant", "full", "list"}
_PAIR_FLAGS = {"at", "offset"}


def _pair(s: str):
    return [float(x) for x in s.replace(" ", "").split(",")]


def parse(cmd: str, rest: list[str]) -> dict:
    a: dict = {}
    pos: list[str] = []
    i = 0
    while i < len(rest):
        t = rest[i]
        if t.startswith("--"):
            key = t[2:]
            if key in _BOOL_FLAGS:
                a[key.replace("-", "_")] = True
                i += 1
            elif key in _PAIR_FLAGS:
                a[key] = _pair(rest[i + 1]); i += 2
            elif key in _VALUE_FLAGS:
                a[key.replace("-", "_")] = rest[i + 1]; i += 2
            else:  # unknown flag: best-effort value or bool
                if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
                    a[key.replace("-", "_")] = rest[i + 1]; i += 2
                else:
                    a[key.replace("-", "_")] = True; i += 1
        else:
            pos.append(t); i += 1

    for name, val in zip(POSITIONALS.get(cmd, []), _consume(POSITIONALS.get(cmd, []), pos)):
        if val is not None:
            a[name.rstrip("*")] = val
    return a


def _consume(names: list[str], pos: list[str]):
    """Yield one value per name; a '*' name swallows the rest joined by space."""
    out, idx = [], 0
    for n in names:
        if n.endswith("*"):
            out.append(" ".join(pos[idx:]) if idx < len(pos) else None)
            idx = len(pos)
        else:
            out.append(pos[idx] if idx < len(pos) else None)
            idx += 1
    return out


def ensure_daemon() -> None:
    if protocol.SOCKET_PATH.exists():
        try:
            protocol.send_request({"cmd": "ping"}, timeout=3)
            return
        except Exception:
            try:
                protocol.SOCKET_PATH.unlink()
            except Exception:
                pass
    protocol.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    log = open(protocol.LOG_PATH, "a")
    subprocess.Popen(
        [sys.executable, "-m", "browser_skill.daemon"],
        stdout=log, stderr=log, start_new_session=True, env=dict(os.environ),
    )
    for _ in range(160):  # up to ~40s (first run may import a heavy lib)
        if protocol.SOCKET_PATH.exists():
            try:
                protocol.send_request({"cmd": "ping"}, timeout=3)
                return
            except Exception:
                pass
        time.sleep(0.25)
    sys.exit(f"error: daemon did not start; see {protocol.LOG_PATH}")


def render(resp: dict) -> None:
    if not resp.get("ok"):
        sys.exit("✗ " + str(resp.get("error", "error")))
    if "output" in resp:
        print(resp["output"])
    if "snapshot" in resp:
        print(resp["snapshot"])
    if "snapshot_error" in resp:
        print(f"(snapshot failed: {resp['snapshot_error']})", file=sys.stderr)


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return
    cmd, rest = argv[0], argv[1:]
    args = parse(cmd, rest)
    # `stop` is special: don't auto-spawn just to stop a non-existent daemon
    if cmd == "stop" and not protocol.SOCKET_PATH.exists():
        print("daemon not running")
        return
    ensure_daemon()
    render(protocol.send_request({"cmd": cmd, "args": args}))


if __name__ == "__main__":
    main()
