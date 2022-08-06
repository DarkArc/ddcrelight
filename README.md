## Requirements

- A yoctopuce light sensor (https://www.yoctopuce.com)
- ddcutil

## Setup

A udev rule is likely required to allow the tool to run as non-root. The
following can be added as the file `/etc/udev/rules.d/50-yoctopuce.rules`:

```
# udev rules to allow write access to all users for Yoctopuce USB devices
SUBSYSTEM=="usb", ATTR{idVendor}=="24e0", MODE="0666"
```

Additionally, udev rules must be configured for ddcutil to operate without root
permissions:

```
https://www.ddcutil.com/i2c_permissions/
```

Then a timer should be configured to update the brightness at the desired
checking interval.  For instance, to adjust brightness every minute:

ddcrelight.service:
```
[Unit]
Description=Update monitor brightness intelligently using light sensors.

[Service]
ExecStart=<path-to-script>/ddcrelight
```

ddcrelight.timer:
```
[Unit]
Description=Run ddcrelight every minute.

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```
