#!/bin/sh
set -e

# Sometimes hiddev node might be held by a stale driver claim
# Attempt to reset it if possible.
if [ -n "$UPS_MANUFACTURER" ]; then
    for d in /sys/bus/usb/devices/*/manufacturer; do
        if grep -q "$UPS_MANUFACTURER" "$d" 2>/dev/null; then
            USB_DEV=$(basename $(dirname "$d"))
            echo "Resetting USB device: $USB_DEV"
            echo "$USB_DEV" > /sys/bus/usb/drivers/usb/unbind
            sleep 2
            echo "$USB_DEV" > /sys/bus/usb/drivers/usb/bind
            echo "Waiting for device to re-enumerate..."
            timeout=10
            while [ $timeout -gt 0 ] && ! ls /dev/usb/hiddev* >/dev/null 2>&1; do
                sleep 1
                timeout=$((timeout - 1))
            done
            echo "USB reset complete"
            break
        fi
    done
fi

for f in /template/*; do
    bn=$(basename "$f")
    envsubst < "$f" > /etc/nut/"$bn"
done

upsdrvctl -u root start

exec "$@"
