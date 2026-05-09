#!/usr/bin/env python3
import json
import os
import signal
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HOST = "0.0.0.0"
PORT = 5050

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "allowed_launches.json"
LOG_DIR = Path.home() / "echo_runtime" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

running_processes = {}
running_logs = {}


def load_config():
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"actions": {}, "error": f"missing config: {CONFIG_FILE}"}
    except json.JSONDecodeError as exc:
        return {"actions": {}, "error": f"invalid json: {exc}"}


def json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def reap_finished_processes():
    finished = []
    for action, proc in list(running_processes.items()):
        if proc.poll() is not None:
            finished.append(action)
    for action in finished:
        running_processes.pop(action, None)


def log_reader(action, proc, log_path):
    with log_path.open("a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] START {action}\n")
        f.flush()
        for line in proc.stdout:
            f.write(line)
            f.flush()
        code = proc.wait()
        f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] EXIT {action} code={code}\n")
        f.flush()


def launch_action(action, spec):
    reap_finished_processes()

    if action in running_processes:
        return False, f"already running: {action}", None

    group = spec.get("exclusive_group")
    if group:
        config = load_config()
        for other, proc in running_processes.items():
            other_spec = config.get("actions", {}).get(other, {})
            if other_spec.get("exclusive_group") == group:
                return False, f"exclusive group busy: {group} already running {other}", None

    command = spec.get("command")
    if not isinstance(command, list) or not command:
        return False, f"no command configured for: {action}", None

    log_path = LOG_DIR / f"{action}.log"

    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
        cwd=str(Path.home()),
        env=os.environ.copy(),
    )

    running_processes[action] = proc
    running_logs[action] = str(log_path)

    thread = threading.Thread(target=log_reader, args=(action, proc, log_path), daemon=True)
    thread.start()

    return True, f"launched: {action}", proc.pid


def stop_action(action):
    reap_finished_processes()

    proc = running_processes.get(action)
    if proc is None:
        return False, f"not running: {action}"

    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        running_processes.pop(action, None)
        return False, f"already stopped: {action}"

    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=3)

    running_processes.pop(action, None)
    return True, f"stopped: {action}"


class EchoLaunchHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        json_response(self, 200, {"ok": True})

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def do_GET(self):
        reap_finished_processes()

        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route == "/logs":
            action = query.get("action", [""])[0]
            try:
                lines = int(query.get("lines", ["120"])[0])
            except ValueError:
                lines = 120

            if not action:
                return json_response(self, 400, {
                    "ok": False,
                    "error": "missing query parameter: action",
                })

            safe_actions = load_config().get("actions", {})
            if action not in safe_actions:
                return json_response(self, 404, {
                    "ok": False,
                    "error": f"unknown action: {action}",
                })

            log_path = LOG_DIR / f"{action}.log"
            if not log_path.exists():
                return json_response(self, 200, {
                    "ok": True,
                    "action": action,
                    "log": "",
                    "path": str(log_path),
                    "message": "log file does not exist yet",
                })

            content = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return json_response(self, 200, {
                "ok": True,
                "action": action,
                "path": str(log_path),
                "lines": content[-max(lines, 1):],
            })

        if route == "/health":
            return json_response(self, 200, {
                "ok": True,
                "service": "echo-launch-server",
                "port": PORT,
                "time": datetime.now().isoformat(timespec="seconds"),
            })

        if route == "/status":
            config = load_config()
            return json_response(self, 200, {
                "ok": "error" not in config,
                "running": sorted(running_processes.keys()),
                "pids": {k: v.pid for k, v in running_processes.items()},
                "logs": running_logs,
                "actions": config.get("actions", {}),
                "config_error": config.get("error"),
                "message": "Launch server is online.",
            })

        return json_response(self, 404, {
            "ok": False,
            "error": "not found",
            "path": self.path,
        })

    def do_POST(self):
        if self.path not in ("/launch", "/stop"):
            return json_response(self, 404, {
                "ok": False,
                "error": "not found",
                "path": self.path,
            })

        try:
            data = self.read_json_body()
        except json.JSONDecodeError as exc:
            return json_response(self, 400, {
                "ok": False,
                "error": f"invalid json: {exc}",
            })

        action = data.get("action")
        if not action or not isinstance(action, str):
            return json_response(self, 400, {
                "ok": False,
                "error": "missing string field: action",
            })

        config = load_config()
        actions = config.get("actions", {})
        spec = actions.get(action)

        if spec is None:
            return json_response(self, 404, {
                "ok": False,
                "error": f"unknown action: {action}",
            })

        if not spec.get("enabled", False):
            return json_response(self, 409, {
                "ok": False,
                "action": action,
                "error": f"action is disabled: {action}",
            })

        if self.path == "/launch":
            ok, message, pid = launch_action(action, spec)
            return json_response(self, 200 if ok else 409, {
                "ok": ok,
                "action": action,
                "pid": pid,
                "message": message,
            })

        if self.path == "/stop":
            ok, message = stop_action(action)
            return json_response(self, 200 if ok else 409, {
                "ok": ok,
                "action": action,
                "message": message,
            })

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {self.address_string()} {fmt % args}")


def main():
    server = ThreadingHTTPServer((HOST, PORT), EchoLaunchHandler)
    print(f"Echo launch server listening on http://{HOST}:{PORT}")
    print(f"Config: {CONFIG_FILE}")
    print(f"Logs: {LOG_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
