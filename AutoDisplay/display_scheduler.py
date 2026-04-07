#!/usr/bin/env python3
"""
display_scheduler.py — Raspberry Pi 4 HDMI Display Scheduler

Turns the HDMI output off at 5:00 PM and back on at 7:00 AM daily.
The Pi remains fully accessible over SSH/VNC/Tailscale while the display is off.

Uses `vcgencmd display_power` which talks to the VideoCore GPU via the
kernel mailbox interface. This is the same mechanism `tvservice` uses
under the hood, but display_power is simpler and works reliably on Pi 4.

    display_power 0  →  HDMI signal stops, TV shows "No Signal"
    display_power 1  →  HDMI signal resumes at the previously configured resolution

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
from datetime import datetime

# ── Configuration ────────────────────────────────────────────────────────────
OFF_HOUR = 17   # 5:00 PM — display turns OFF
ON_HOUR  = 7    # 7:00 AM — display turns ON
POLL_INTERVAL_SECONDS = 60  # How often to check the time
# ─────────────────────────────────────────────────────────────────────────────


def log(msg: str) -> None:
    """Print a timestamped log line (captured by journald when run as a service)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def set_display_power(on: bool) -> bool:
    """
    Set the HDMI display power state via vcgencmd.

    Returns True if the command succeeded, False otherwise.
    vcgencmd talks to the VideoCore IV/VI GPU through /dev/vcio (the kernel
    mailbox char device). It doesn't need X or Wayland running — works on a
    headless console boot too.
    """
    state = "1" if on else "0"
    try:
        result = subprocess.run(
            ["vcgencmd", "display_power", state],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            log(f"ERROR: vcgencmd returned {result.returncode}: {result.stderr.strip()}")
            return False
        log(f"Display {'ON' if on else 'OFF'} (vcgencmd display_power {state})")
        return True
    except FileNotFoundError:
        log("ERROR: vcgencmd not found — is this running on a Raspberry Pi?")
        return False
    except subprocess.TimeoutExpired:
        log("ERROR: vcgencmd timed out")
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
        # This avoids spamming vcgencmd every 60 seconds — we only talk
        # to the GPU twice a day (at the two transition points).
        if desired_state != current_state:
            if set_display_power(desired_state):
                current_state = desired_state
            # If the command failed, we'll retry next poll cycle since
            # current_state still differs from desired_state.


if __name__ == "__main__":
    main()
