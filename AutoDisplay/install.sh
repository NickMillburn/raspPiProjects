#!/usr/bin/env bash
# install.sh — Deploy the display scheduler on a Raspberry Pi
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Display Scheduler Installer ==="

# Verify we're on a Pi (or at least that vcgencmd exists)
if ! command -v vcgencmd &>/dev/null; then
    echo "WARNING: vcgencmd not found. This script is designed for Raspberry Pi OS."
    echo "Continuing anyway, but the service won't work without vcgencmd."
fi

# Copy files into place
echo "[1/4] Copying display_scheduler.py → /usr/local/bin/"
sudo cp "$SCRIPT_DIR/display_scheduler.py" /usr/local/bin/display_scheduler.py
sudo chmod +x /usr/local/bin/display_scheduler.py

echo "[2/4] Copying display-scheduler.service → /etc/systemd/system/"
sudo cp "$SCRIPT_DIR/display-scheduler.service" /etc/systemd/system/display-scheduler.service

echo "[3/4] Reloading systemd daemon"
sudo systemctl daemon-reload

echo "[4/4] Enabling and starting the service"
sudo systemctl enable --now display-scheduler.service

echo ""
echo "Done! The display scheduler is now running."
echo ""
echo "Useful commands:"
echo "  journalctl -u display-scheduler -f          # Watch live logs"
echo "  sudo systemctl status display-scheduler      # Check status"
echo "  sudo systemctl stop display-scheduler        # Stop (display turns back on)"
echo "  sudo systemctl disable display-scheduler     # Disable on boot"
echo "  vcgencmd display_power                       # Query current display state"
