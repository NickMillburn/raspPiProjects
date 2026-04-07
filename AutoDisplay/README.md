# Display Scheduler for Raspberry Pi 4

A lightweight Python daemon that automatically turns off the HDMI output on a Raspberry Pi 4 at a scheduled time each evening and turns it back on in the morning. The Pi itself stays fully operational — SSH, VNC, Tailscale, and any other remote access continues to work normally while the display is off.

## How It Works

The script uses `vcgencmd display_power`, a Raspberry Pi-specific command that talks directly to the VideoCore GPU through the kernel mailbox interface (`/dev/vcio`). When the display is turned off, the GPU stops generating an HDMI signal entirely — the connected TV will show "No Signal" or enter standby. When turned back on, the signal resumes at the previously configured resolution with no reconfiguration needed.

The daemon runs a simple polling loop that checks the system clock every 60 seconds. It tracks whether the display is currently on or off and only issues a `vcgencmd` call when the state needs to change, so it only talks to the GPU twice per day (at the two transition points). If the Pi reboots in the middle of the off window, the script sets the correct state immediately on startup.

When the service is stopped (via `systemctl stop` or a system shutdown), a signal handler catches `SIGTERM`/`SIGINT` and restores the display before exiting, so you'll never accidentally leave the HDMI stuck off.

## Default Schedule

| Time     | Action            |
|----------|-------------------|
| 5:00 PM  | Display turns OFF |
| 7:00 AM  | Display turns ON  |

To change the schedule, edit `OFF_HOUR` and `ON_HOUR` at the top of `display_scheduler.py`, then restart the service.

## Installation

```bash
git clone https://github.com/<your-username>/display-scheduler.git
cd display-scheduler
bash install.sh
```

The install script does the following:
1. Copies `display_scheduler.py` to `/usr/local/bin/`
2. Copies `display-scheduler.service` to `/etc/systemd/system/`
3. Reloads the systemd daemon
4. Enables and starts the service

## Useful Commands

```bash
# Watch live logs
journalctl -u display-scheduler -f

# Check service status
sudo systemctl status display-scheduler

# Stop the service (display turns back on automatically)
sudo systemctl stop display-scheduler

# Disable the service from starting on boot
sudo systemctl disable display-scheduler

# Re-enable and start
sudo systemctl enable --now display-scheduler

# Manually query the current display power state
vcgencmd display_power
```

## Updating

After pulling changes from the repo:

```bash
cd display-scheduler
bash install.sh
```

The install script will overwrite the existing files and restart the service.

## Requirements

- Raspberry Pi 4 (or any Pi with `vcgencmd` support)
- Raspberry Pi OS (Raspbian)
- Python 3.7+
- No additional Python packages required (uses only the standard library)

## File Overview

| File                         | Purpose                                              |
|------------------------------|------------------------------------------------------|
| `display_scheduler.py`       | The main daemon script                               |
| `display-scheduler.service`  | systemd unit file for running as a boot service      |
| `install.sh`                 | One-step installer that deploys and enables the service |

## License

Do whatever you want with it.
