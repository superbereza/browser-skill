"""The persistent daemon (see ADR 2026-06-09-daemon-not-stateless-cli).

Holds one Patchright `connect_over_cdp` session, the current page, and the snapshot
ref-map in memory. Serves newline-delimited JSON over a unix socket, one command at
a time. Auto-shuts down after `idle_minutes` with no command.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time

from . import captcha, driver, protocol
from . import snapshot as snap

_ACCEPT_POLL = 30  # seconds; also the idle-check granularity


def _import_sync_playwright():
    try:
        from patchright.sync_api import sync_playwright  # stealth fork (preferred)
        return sync_playwright
    except Exception:
        from playwright.sync_api import sync_playwright  # fallback
        return sync_playwright


class Daemon:
    def __init__(self, idle_minutes: float):
        self.cfg = protocol.load_config()
        self.idle = idle_minutes * 60
        self.pw = None
        self.browser = None
        self.context = None
        self.page = None
        self.app = None
        self.profile_dir = None
        self.refs: set = set()  # valid ref ids from the most recent AI snapshot
        self.last = time.time()
        self._stop = False
        self._quit_browser = False
        self._dialog = None
        self._dialog_policy = "dismiss"
        self._dialog_prompt = None

    # ---- lifecycle ----------------------------------------------------------
    def start(self) -> None:
        self.pw = _import_sync_playwright()().start()
        self._serve()

    def _attach(self, port: int) -> None:
        self.browser = self.pw.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self._wire_dialogs(self.page)

    def _wire_dialogs(self, page) -> None:
        def handler(dialog):
            self._dialog = {"type": dialog.type, "message": dialog.message}
            try:
                if self._dialog_policy == "accept":
                    dialog.accept(self._dialog_prompt or "")
                else:
                    dialog.dismiss()
            except Exception:
                pass
            self._dialog_policy = "dismiss"  # one-shot
            self._dialog_prompt = None
        try:
            page.on("dialog", handler)
        except Exception:
            pass

    def _cleanup(self) -> None:
        try:
            if self._quit_browser and self.profile_dir:
                driver.kill_instance(self.profile_dir)  # only our dedicated instance
        except Exception:
            pass
        try:
            if self.pw:
                self.pw.stop()
        except Exception:
            pass

    # ---- serve loop ---------------------------------------------------------
    def _serve(self) -> None:
        protocol.RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        if protocol.SOCKET_PATH.exists():
            protocol.SOCKET_PATH.unlink()
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(str(protocol.SOCKET_PATH))
        srv.listen(8)
        srv.settimeout(_ACCEPT_POLL)
        protocol.PID_PATH.write_text(str(os.getpid()))
        try:
            while not self._stop:
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    if time.time() - self.last > self.idle:
                        break
                    continue
                self._handle(conn)
                self.last = time.time()
        finally:
            self._cleanup()
            srv.close()
            for p in (protocol.SOCKET_PATH, protocol.PID_PATH):
                try:
                    p.unlink()
                except Exception:
                    pass

    def _handle(self, conn) -> None:
        conn.settimeout(180)
        buf = b""
        try:
            while not buf.endswith(b"\n"):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buf += chunk
            req = json.loads(buf.decode() or "{}")
            resp = self._dispatch(req.get("cmd", ""), req.get("args", {}) or {})
        except Exception as e:
            resp = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        try:
            conn.sendall((json.dumps(resp) + "\n").encode())
        finally:
            conn.close()

    # ---- dispatch -----------------------------------------------------------
    def _dispatch(self, cmd: str, a: dict) -> dict:
        if cmd == "ping":
            return {"ok": True, "output": "pong"}
        if cmd == "stop":
            self._stop = True
            return {"ok": True, "output": "daemon stopping (browser left running)"}
        if cmd == "quit":
            self._stop = True
            self._quit_browser = True
            return {"ok": True, "output": "daemon stopping + closing browser"}
        if cmd == "launch":
            return self._cmd_launch(a)
        if cmd == "status":
            return self._cmd_status()

        if self.page is None:
            return {"ok": False, "error": "not attached — run `launch` first"}
        handler = getattr(self, f"_cmd_{cmd.replace('-', '_')}", None)
        if handler is None:
            return {"ok": False, "error": f"unknown command: {cmd}"}
        return handler(a)

    def _snap_reply(self, output=None, a=None) -> dict:
        r = {"ok": True}
        if output is not None:
            r["output"] = output
        if not (a or {}).get("no_snap"):
            try:
                text, self.refs = snap.snapshot(self.page)
                r["snapshot"] = text
            except Exception as e:
                r["snapshot_error"] = str(e)
        return r

    # ---- commands -----------------------------------------------------------
    def _cmd_launch(self, a: dict) -> dict:
        if a.get("list"):
            return {"ok": True, "output": "\n".join(self.cfg["browsers"].keys())}
        name = a.get("name") or self.cfg["default_browser"]
        b = self.cfg["browsers"].get(name)
        if not b:
            return {"ok": False, "error": f"unknown browser '{name}'. "
                    f"configured: {list(self.cfg['browsers'])}"}
        port = int(a.get("port") or self.cfg["port"])
        profile_dir = a.get("profile") or str(protocol.CONFIG_DIR / "profiles" / name)
        os.makedirs(profile_dir, exist_ok=True)
        self.app = b["app"]
        self.profile_dir = profile_dir
        action, note = driver.ensure_browser(self.app, port, profile_dir)
        self._attach(port)
        return self._snap_reply(output=f"{action}: {note}; attached {self.page.url}", a=a)

    def _cmd_status(self) -> dict:
        if self.page is None:
            return {"ok": True, "output": "not attached"}
        return {"ok": True, "output": json.dumps({"url": self.page.url, "title": self.page.title()})}

    def _cmd_snapshot(self, a: dict) -> dict:
        text, self.refs = snap.snapshot(self.page)
        return {"ok": True, "snapshot": text}

    def _cmd_text(self, a: dict) -> dict:
        if a.get("ref"):
            return {"ok": True, "output": snap.locator_for(self.page, self.refs, a["ref"]).inner_text()}
        return {"ok": True, "output": self.page.inner_text("body")}

    def _cmd_html(self, a: dict) -> dict:
        if a.get("ref"):
            return {"ok": True, "output": snap.locator_for(self.page, self.refs, a["ref"]).inner_html()}
        return {"ok": True, "output": self.page.content()}

    def _cmd_screenshot(self, a: dict) -> dict:
        path = a.get("path") or str(protocol.RUNTIME_DIR / "screenshot.png")
        self.page.screenshot(path=path, full_page=bool(a.get("full")))
        return {"ok": True, "output": path}

    def _cmd_goto(self, a: dict) -> dict:
        self.page.goto(a["url"])
        return self._snap_reply(output=f"at {self.page.url}", a=a)

    def _cmd_back(self, a: dict) -> dict:
        self.page.go_back()
        return self._snap_reply(a=a)

    def _cmd_forward(self, a: dict) -> dict:
        self.page.go_forward()
        return self._snap_reply(a=a)

    def _cmd_reload(self, a: dict) -> dict:
        self.page.reload()
        return self._snap_reply(a=a)

    def _cmd_click(self, a: dict) -> dict:
        if a.get("at"):
            x, y = a["at"]
            self.page.mouse.click(float(x), float(y))
        elif a.get("selector"):
            loc = self.page.locator(a["selector"])
            if a.get("offset"):
                ox, oy = a["offset"]
                box = loc.bounding_box()
                self.page.mouse.click(box["x"] + float(ox), box["y"] + float(oy))
            else:
                loc.click()
        elif a.get("ref"):
            snap.locator_for(self.page, self.refs, a["ref"]).click()
        else:
            return {"ok": False, "error": "click needs <ref> | --selector <css> | --at x,y"}
        return self._snap_reply(a=a)

    def _cmd_type(self, a: dict) -> dict:
        if a.get("ref"):
            loc = snap.locator_for(self.page, self.refs, a["ref"])
        elif a.get("selector"):
            loc = self.page.locator(a["selector"])
        else:
            return {"ok": False, "error": "type needs <ref> | --selector <css>"}
        text = a.get("text", "")
        if a.get("instant"):
            loc.fill(text)
        else:
            loc.click()
            loc.press_sequentially(text, delay=30)
        return self._snap_reply(a=a)

    def _cmd_press(self, a: dict) -> dict:
        self.page.keyboard.press(a["key"])
        return self._snap_reply(a=a)

    def _cmd_scroll(self, a: dict) -> dict:
        d = a.get("dir", "down")
        if d in ("down", "up"):
            self.page.mouse.wheel(0, 800 if d == "down" else -800)
        else:  # treat as a ref to scroll into view
            snap.locator_for(self.page, self.refs, d).scroll_into_view_if_needed()
        return self._snap_reply(a=a)

    def _cmd_hover(self, a: dict) -> dict:
        snap.locator_for(self.page, self.refs, a["ref"]).hover()
        return self._snap_reply(a=a)

    def _cmd_select(self, a: dict) -> dict:
        snap.locator_for(self.page, self.refs, a["ref"]).select_option(a["value"])
        return self._snap_reply(a=a)

    def _cmd_tabs(self, a: dict) -> dict:
        lines = []
        for i, p in enumerate(self.context.pages):
            mark = "*" if p is self.page else " "
            try:
                title = p.title()
            except Exception:
                title = ""
            lines.append(f"{mark} {i}  {p.url}  {title!r}")
        return {"ok": True, "output": "\n".join(lines)}

    def _cmd_tab(self, a: dict) -> dict:
        sel = a.get("sel")
        pages = self.context.pages
        target = None
        if sel is not None and str(sel).isdigit() and 0 <= int(sel) < len(pages):
            target = pages[int(sel)]
        elif sel:
            target = next((p for p in pages if sel in p.url), None)
        if target is None:
            return {"ok": False, "error": f"no tab matched '{sel}'"}
        self.page = target
        self._wire_dialogs(self.page)
        self.page.bring_to_front()
        return self._snap_reply(output=f"switched to {self.page.url}", a=a)

    def _cmd_new_tab(self, a: dict) -> dict:
        self.page = self.context.new_page()
        self._wire_dialogs(self.page)
        if a.get("url"):
            self.page.goto(a["url"])
        return self._snap_reply(a=a)

    def _cmd_close_tab(self, a: dict) -> dict:
        pages = self.context.pages
        idx = a.get("idx")
        target = pages[int(idx)] if idx is not None and str(idx).isdigit() else self.page
        target.close()
        self.page = self.context.pages[0] if self.context.pages else None
        if self.page:
            self._wire_dialogs(self.page)
        return self._snap_reply(a=a)

    def _cmd_upload(self, a: dict) -> dict:
        snap.locator_for(self.page, self.refs, a["ref"]).set_input_files(a["path"])
        return self._snap_reply(a=a)

    def _cmd_download(self, a: dict) -> dict:
        with self.page.expect_download() as dl:
            snap.locator_for(self.page, self.refs, a["ref"]).click()
        d = dl.value
        dest = a.get("path") or str(protocol.RUNTIME_DIR / d.suggested_filename)
        d.save_as(dest)
        return self._snap_reply(output=dest, a=a)

    def _cmd_dialog(self, a: dict) -> dict:
        if a.get("policy"):
            self._dialog_policy = a["policy"]
            self._dialog_prompt = a.get("text")
            return {"ok": True, "output": f"next dialog will be {a['policy']}ed"}
        return {"ok": True, "output": json.dumps(self._dialog or {})}

    def _cmd_wait(self, a: dict) -> dict:
        if a.get("for"):
            self.page.wait_for_selector(a["for"], timeout=int(float(a.get("timeout", 30))) * 1000)
        else:
            self.page.wait_for_timeout(float(a.get("sec", 1)) * 1000)
        return self._snap_reply(a=a)

    def _cmd_eval(self, a: dict) -> dict:
        # Return a string result RAW (no JSON quoting) so e.g. `return x+','+y`
        # yields `815,176`, pipeable straight into `click --at`. Non-strings
        # (objects/numbers/bool/None) get clean, single-encoded JSON.
        val = self.page.evaluate(a["js"])
        out = val if isinstance(val, str) else json.dumps(val, default=str)
        return {"ok": True, "output": out}

    def _cmd_captcha(self, a: dict) -> dict:
        sub = a.get("sub", "status")
        if sub == "status":
            return {"ok": True, "output": json.dumps(captcha.detect(self.page))}
        if sub == "ask-human":
            return {"ok": True, "output": json.dumps(captcha.ask_human(self.page, a.get("message")))}
        if sub == "solve":
            res = captcha.solve(self.page, a.get("method", "auto"))
            if res.get("error"):
                return {"ok": False, "error": res["error"]}
            return {"ok": True, "output": json.dumps(res)}
        return {"ok": False, "error": f"unknown captcha subcommand: {sub}"}


def main() -> None:
    ap = argparse.ArgumentParser(prog="browser-daemon")
    ap.add_argument("--idle", type=float, default=None, help="idle minutes before auto-shutdown")
    args = ap.parse_args()
    cfg = protocol.load_config()
    idle = args.idle if args.idle is not None else cfg["idle_minutes"]
    Daemon(idle).start()


if __name__ == "__main__":
    main()
