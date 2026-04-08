#!/usr/bin/env python3
"""
display_scheduler.py — Raspberry Pi 4 HDMI Display Scheduler

Turns the HDMI output off at 5:00 PM and back on at 7:00 AM daily.
The Pi remains fully accessible over SSH/VNC/Tailscale while the display is off.

Uses `wlr-randr` to toggle the HDMI output on a Wayland compositor. This is
required on Debian Trixie where vcgencmd display_power reports success but
doesn't actually control the display.

    wlr-randr --output HDMI-A-1 --off   →  HDMI output disabled, TV shows "No Signal"
    wlr-randr --output HDMI-A-1 --on    →  HDMI output re-enabled at previous resolution

Because wlr-randr needs to talk to the Wayland compositor, it must run as
the same user that owns the desktop session. The systemd service runs as
the 'numnuts' user and sets the WAYLAND_DISPLAY and XDG_RUNTIME_DIR
environment variables so the command can reach the compositor socket.

Install:
    sudo cp display_scheduler.py /usr/local/bin/display_scheduler.py
    sudo chmod +x /usr/local/bin/display_scheduler.py
    sudo cp display-scheduler.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now display-scheduler.service

Logs:
    journalctl -u display-scheduler.service -f
"""

import subprocess
import time
import signal
import sys
import os
from datetime import datetime

# ── Configuration ────────────────────────────────────────────────────────────
OFF_HOUR = 17   # 5:00 PM — display turns OFF
ON_HOUR  = 7    # 7:00 AM — display turns ON
POLL_INTERVAL_SECONDS = 60  # How often to check the time

# HDMI output name as reported by wlr-randr. On a Pi 4 with a single
# HDMI cable this is typically HDMI-A-1. If your setup differs, run
# `wlr-randr` with no arguments to list available outputs.
HDMI_OUTPUT = "HDMI-A-1"

# The logged-in desktop user and their Wayland socket info.
# wlr-randr must talk to the compositor, which means it needs to run
# as the user who owns the Wayland session (or at least with the right
# environment variables pointing to that user's runtime dir).
DESKTOP_USER = "numnuts"
WAYLAND_DISPLAY = "wayland-0"
# ─────────────────────────────────────────────────────────────────────────────


def get_wayland_env() -> dict:
    """
    Build the environment dict needed for wlr-randr to find the compositor.

    wlr-randr communicates with the Wayland compositor through a Unix socket
    at $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY. When run from a systemd service,
    these variables aren't set automatically, so we construct them:

      XDG_RUNTIME_DIR = /run/user/<uid>    (standard systemd-logind path)
      WAYLAND_DISPLAY = wayland-0          (default compositor socket name)

    We merge these into the current environment so other things like PATH
    are preserved.
    """
    try:
        result = subprocess.run(
            ["id", "-u", DESKTOP_USER],
            capture_output=True, text=True, timeout=5,
        )
        uid = result.stdout.strip()
    except Exception:
        uid = "1000"  # fallback for typical first user

    env = os.environ.copy()
    env["XDG_RUNTIME_DIR"] = f"/run/user/{uid}"
    env["WAYLAND_DISPLAY"] = WAYLAND_DISPLAY
    return env


def log(msg: str) -> None:
    """Print a timestamped log line (captured by journald when run as a service)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def set_display_power(on: bool) -> bool:
    """
    Toggle the HDMI output via wlr-randr.

    Returns True if the command succeeded, False otherwise.

    wlr-randr is a command-line utility for wlroots-based Wayland compositors.
    It sends requests over the Wayland protocol to enable/disable outputs,
    change resolution, etc. — similar to xrandr for X11.

    --on  re-enables the output (resumes the HDMI signal)
    --off disables the output (TV sees no signal, compositor stops rendering to it)
    """
    flag = "--on" if on else "--off"
    try:
        result = subprocess.run(
            ["wlr-randr", "--output", HDMI_OUTPUT, flag],
            capture_output=True,
            text=True,
            timeout=10,
            env=get_wayland_env(),
        )
        if result.returncode != 0:
            log(f"ERROR: wlr-randr returned {result.returncode}: {result.stderr.strip()}")
            return False
        log(f"Display {'ON' if on else 'OFF'} (wlr-randr --output {HDMI_OUTPUT} {flag})")
        return True
    except FileNotFoundError:
        log("ERROR: wlr-randr not found — install it with: sudo apt install wlr-randr")
        return False
    except subprocess.TimeoutExpired:
        log("ERROR: wlr-randr timed out")
        return False


def should_display_be_on(now: datetime) -> bool:
    """
    Determine whether the display should be on at the given time.

    The OFF window spans midnight:
        5:00 PM (17:00) ──► midnight ──► 7:00 AM (07:00)

    So the display should be OFF when:
        hour >= 17  OR  hour < 7

    And ON when:
        7 <= hour < 17
    """
    hour = now.hour
    return ON_HOUR <= hour < OFF_HOUR


def main() -> None:
    log(f"Starting display scheduler (OFF at {OFF_HOUR}:00, ON at {ON_HOUR}:00)")
    log(f"Poll interval: {POLL_INTERVAL_SECONDS}s")
    log(f"Output: {HDMI_OUTPUT} | User: {DESKTOP_USER} | Wayland: {WAYLAND_DISPLAY}")

    # ── Graceful shutdown ────────────────────────────────────────────────
    # When the service stops (or you Ctrl-C), turn the display back on
    # so you don't leave it stuck off after uninstalling.
    def shutdown(signum, frame):
        log(f"Caught signal {signum}, restoring display and exiting")
        set_display_power(True)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # ── Set initial state ────────────────────────────────────────────────
    # If the Pi just booted at 3 AM, we want the display off immediately
    # rather than waiting for the next poll to notice.
    current_state = should_display_be_on(datetime.now())
    set_display_power(current_state)
    log(f"Initial state: display {'ON' if current_state else 'OFF'}")

    # ── Main loop ────────────────────────────────────────────────────────
    while True:
        time.sleep(POLL_INTERVAL_SECONDS)

        desired_state = should_display_be_on(datetime.now())

        # Only issue a command when the state actually changes.
        # This avoids calling wlr-randr every 60 seconds — we only talk
        # to the compositor twice a day (at the two transition points).
        if desired_state != current_state:
            if set_display_power(desired_state):
                current_state = desired_state
            # If the command failed, we'll retry next poll cycle since
            # current_state still differs from desired_state.


if __name__ == "__main__":
    main()
