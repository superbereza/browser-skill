"""Shared paths, config, and the tiny socket request helper.

Client (`cli`) and server (`daemon`) speak newline-delimited JSON over a unix
socket. One request → one response, both single JSON objects terminated by '\n'.
"""
from __future__ import annotations

import json
import os
import pathlib
import socket
import tempfile

CONFIG_DIR = pathlib.Path(os.path.expanduser("~/.browser-skill"))
CONFIG_FILE = CONFIG_DIR / "config.json"
TELEMETRY_FILE = CONFIG_DIR / "captcha.log"

RUNTIME_DIR = pathlib.Path(tempfile.gettempdir()) / "browser-skill"
SOCKET_PATH = RUNTIME_DIR / "daemon.sock"
PID_PATH = RUNTIME_DIR / "daemon.pid"
LOG_PATH = RUNTIME_DIR / "daemon.log"

# macOS app names per browser key. Extend in ~/.browser-skill/config.json.
DEFAULT_CONFIG = {
    "default_browser": "yandex",
    "port": 9222,
    "idle_minutes": 15,
    "browsers": {
        "yandex": {"app": "Yandex"},
        "chrome": {"app": "Google Chrome"},
        "chromium": {"app": "Chromium"},
        "brave": {"app": "Brave Browser"},
        "edge": {"app": "Microsoft Edge"},
    },
    # captcha solver (tier 3) — off until a key is set
    "captcha": {"solver_service": "2captcha", "solver_api_key": None},
}


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    if CONFIG_FILE.exists():
        try:
            user = json.loads(CONFIG_FILE.read_text())
            _deep_update(cfg, user)
        except Exception:
            pass
    return cfg


def _deep_update(base: dict, extra: dict) -> None:
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v


def send_request(payload: dict, timeout: float = 180) -> dict:
    """Send one request to the daemon, return its response dict."""
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(str(SOCKET_PATH))
    try:
        s.sendall((json.dumps(payload) + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    finally:
        s.close()
    return json.loads(buf.decode() or "{}")
