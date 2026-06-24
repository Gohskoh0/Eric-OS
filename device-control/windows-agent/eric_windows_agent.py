"""
Eric — Windows Device Agent
----------------------------
A small always-on script that runs on your laptop and polls n8n for
pending device commands, then executes ONLY whitelisted actions.

Why polling, not a server: your laptop doesn't have a stable public
IP/port forwarding set up, and exposing one would be a security risk.
Polling outbound (laptop -> n8n) avoids opening any inbound port.

SECURITY MODEL — read before running:
- This script can only run actions in the ACTIONS dict below. It will
  NEVER eval() or exec() arbitrary text from the network. Every action
  is a named, pre-written Python function you control.
- Add new actions by writing a new function and registering it below.
  Do not add a generic "run shell command" action unless you fully
  trust the chain (n8n auth + your Telegram identity check) — that
  would let anyone who compromises n8n run arbitrary code on your laptop.

SETUP:
  pip install requests
  Set ERIC_N8N_HOST and ERIC_DEVICE_TOKEN below or as env vars.
  Run: python eric_windows_agent.py
  (Optional) Add to Windows Startup folder so it runs on boot.
"""

import os
import time
import subprocess
import requests

N8N_HOST = os.environ.get("ERIC_N8N_HOST", "https://your-app-name.onrender.com")
DEVICE_TOKEN = os.environ.get("ERIC_DEVICE_TOKEN", "REPLACE_WITH_SHARED_SECRET")
POLL_INTERVAL_SECONDS = 5

# ---- Whitelisted actions Eric is allowed to trigger on this laptop ----

def action_lock_screen(params):
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Screen locked"

def action_open_app(params):
    app = params.get("app", "")
    allowed_apps = {
        "notepad": "notepad.exe",
        "explorer": "explorer.exe",
        "calculator": "calc.exe",
        "vscode": "code",
        "chrome": "chrome",
    }
    exe = allowed_apps.get(app.lower())
    if not exe:
        return f"App '{app}' is not in the allowed list"
    subprocess.Popen(exe, shell=True)
    return f"Opened {app}"

def action_shutdown(params):
    # Disabled by default — uncomment only if you genuinely want remote shutdown.
    # subprocess.run(["shutdown", "/s", "/t", "30"])
    return "Shutdown action is disabled by default for safety. Edit the script to enable it."

def action_open_url(params):
    url = params.get("url", "")
    if not url.startswith("http"):
        return "Rejected: not a valid URL"
    subprocess.run(["start", url], shell=True)
    return f"Opened {url}"

ACTIONS = {
    "lock_screen": action_lock_screen,
    "open_app": action_open_app,
    "shutdown": action_shutdown,
    "open_url": action_open_url,
}

# ---- Polling loop ----

def poll_for_commands():
    try:
        resp = requests.get(
            f"{N8N_HOST}/webhook/eric-device-commands",
            headers={"Authorization": f"Bearer {DEVICE_TOKEN}"},
            params={"device": "windows_laptop"},
            timeout=10,
        )
        if resp.status_code == 200 and resp.json().get("command"):
            return resp.json()
    except requests.RequestException as e:
        print(f"[Eric agent] poll failed: {e}")
    return None

def report_result(command_id, result):
    try:
        requests.post(
            f"{N8N_HOST}/webhook/eric-device-result",
            json={"command_id": command_id, "result": result, "device": "windows_laptop"},
            headers={"Authorization": f"Bearer {DEVICE_TOKEN}"},
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[Eric agent] report failed: {e}")

def main():
    print("Eric Windows agent running. Listening for commands...")
    while True:
        cmd = poll_for_commands()
        if cmd:
            action_name = cmd.get("action")
            params = cmd.get("params", {})
            command_id = cmd.get("command_id")
            handler = ACTIONS.get(action_name)
            if handler:
                result = handler(params)
            else:
                result = f"Unknown action: {action_name}"
            print(f"[Eric agent] {action_name} -> {result}")
            report_result(command_id, result)
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
