# GPIO Configuration Reference for MilkV Duo S MIDI Adapter

## Overview

This document provides guidance on configuring GPIO pins for button inputs on the MilkV Duo S MIDI adapter.

## GPIO Pin Mapping

The MilkV Duo S uses Linux GPIO numbers that may differ from the physical pin numbers on the board.

### Finding GPIO Numbers

#### Method 1: Using duo-pinmux (Recommended)
```bash
duo-pinmux -l
```

#### Method 2: Manual GPIO Discovery
```bash
# List all available GPIOs
ls /sys/class/gpio/
```

#### Method 3: Check Device Tree
```bash
# View GPIO configuration in device tree
cat /sys/firmware/devicetree/base/soc/gpio*/compatible
```

## Common GPIO Pin Numbers for Duo S

| Physical Pin | Function | GPIO Number | Notes |
|--------------|----------|-------------|-------|
| GP0          | GPIO     | 466         | General purpose I/O |
| GP1          | GPIO     | 467         | General purpose I/O |
| GP2          | GPIO     | 477         | General purpose I/O |
| GP3          | GPIO     | 478         | General purpose I/O |
| GP4          | GPIO     | 479         | General purpose I/O |
| GP5          | GPIO     | 480         | General purpose I/O |

**Note**: These numbers may vary. Always verify with `duo-pinmux -l` or check your specific board documentation.

## GPIO Button Wiring

### Simple Button Circuit

```
     3.3V ────┐
              │
             ┌┴┐
             │ │  10kΩ Pull-up
             └┬┘
              │
              ├──────── GPIO Pin
              │
           ┌──┴──┐
           │     │  Push Button (Normally Open)
           └──┬──┘
              │
             GND
```

### Recommended Setup
- Use pull-up resistors (10kΩ) to 3.3V
- Connect button between GPIO and GND
- Button press pulls GPIO LOW (falling edge)

## Configuring GPIO in Software

### 1. Export GPIO
```bash
echo 466 > /sys/class/gpio/export
```

### 2. Set Direction to Input
```bash
echo in > /sys/class/gpio/gpio466/direction
```

### 3. Configure Edge Detection
```bash
# Detect falling edge (button press)
echo falling > /sys/class/gpio/gpio466/edge

# Or both edges
echo both > /sys/class/gpio/gpio466/edge
```

### 4. Read GPIO Value
```bash
cat /sys/class/gpio/gpio466/value
# Returns: 0 (pressed) or 1 (not pressed)
```

## Configuration in config.json

Add GPIO buttons to your MIDI adapter configuration:

```json
{
  "gpio_buttons": [
    {
      "gpio": 466,
      "action": "toggle_routing",
      "comment": "Button 1: Toggle MIDI routing on/off"
    },
    {
      "gpio": 467,
      "action": "reconnect",
      "comment": "Button 2: Reconnect MIDI devices"
    },
    {
      "gpio": 477,
      "action": "custom_action",
      "comment": "Button 3: Custom action (modify code)"
    }
  ]
}
```

## Predefined Actions

The MIDI adapter supports the following button actions:

### `toggle_routing`
Toggles MIDI routing on/off. Useful for temporarily disabling MIDI output.

### `reconnect`
Re-establishes all MIDI connections. Useful if a USB MIDI device is disconnected and reconnected.

### Custom Actions
You can define custom actions by modifying the `handle_button_press` method in `midi_adapter.py`:

```python
def handle_button_press(self, gpio_num, action):
    if action == "my_custom_action":
        # Your code here
        logger.info("Custom action triggered!")
        # Example: Change MIDI channel
        # Example: Send MIDI program change
        # Example: Toggle LED
```

## Testing GPIO Buttons

### Interactive Test Script
```bash
#!/bin/bash
# test-gpio.sh

GPIO=466

# Export GPIO
echo $GPIO > /sys/class/gpio/export

# Set as input
echo in > /sys/class/gpio/gpio$GPIO/direction

# Monitor button presses
echo "Press button on GPIO $GPIO (Ctrl+C to exit)..."
while true; do
    VALUE=$(cat /sys/class/gpio/gpio$GPIO/value)
    if [ "$VALUE" = "0" ]; then
        echo "Button pressed!"
        sleep 0.5
    fi
    sleep 0.05
done
```

### Using Python Test Script
```python
#!/usr/bin/env python3
import time

GPIO_NUM = 466
GPIO_PATH = f"/sys/class/gpio/gpio{GPIO_NUM}"

# Export GPIO
with open("/sys/class/gpio/export", "w") as f:
    f.write(str(GPIO_NUM))

# Set direction
with open(f"{GPIO_PATH}/direction", "w") as f:
    f.write("in")

print(f"Monitoring GPIO {GPIO_NUM}...")
last_value = "1"

while True:
    with open(f"{GPIO_PATH}/value", "r") as f:
        value = f.read().strip()
    
    if last_value == "1" and value == "0":
        print("Button pressed!")
    
    last_value = value
    time.sleep(0.05)
```

## Multiple Buttons Configuration Example

### Hardware Setup
```
Button 1 (GP0/466) - Toggle routing
Button 2 (GP1/467) - Reconnect devices  
Button 3 (GP2/477) - Emergency MIDI panic (all notes off)
Button 4 (GP3/478) - Change preset
```

### Configuration
```json
{
  "gpio_buttons": [
    {
      "gpio": 466,
      "action": "toggle_routing",
      "label": "Route Toggle"
    },
    {
      "gpio": 467,
      "action": "reconnect",
      "label": "Reconnect"
    },
    {
      "gpio": 477,
      "action": "midi_panic",
      "label": "MIDI Panic"
    },
    {
      "gpio": 478,
      "action": "change_preset",
      "label": "Preset Change"
    }
  ]
}
```

## Troubleshooting

### GPIO Already in Use
```bash
# Check what's using the GPIO
cat /sys/kernel/debug/gpio

# Force unexport and re-export
echo 466 > /sys/class/gpio/unexport
echo 466 > /sys/class/gpio/export
```

### Button Not Responding
1. Check physical connections
2. Verify GPIO number is correct
3. Test with multimeter (should read 0V when pressed, 3.3V when released)
4. Check pull-up resistor value (should be 10kΩ)

### GPIO Permission Issues
```bash
# Add to gpio group (if exists)
usermod -a -G gpio root

# Or set permissions
chmod 666 /sys/class/gpio/export
chmod 666 /sys/class/gpio/unexport
```

### Bouncing Issues
If buttons trigger multiple times, add debouncing in software:
- Already implemented in `midi_adapter.py` with 50ms polling
- Can be adjusted in the `_monitor_loop` method

## Advanced: Interrupt-based GPIO

For better responsiveness, consider using Linux GPIO interrupts:

```python
import select

# After configuring edge detection
with open(f"{GPIO_PATH}/value", "rb") as f:
    poller = select.poll()
    poller.register(f, select.POLLPRI | select.POLLERR)
    
    while True:
        events = poller.poll()
        f.seek(0)
        value = f.read().strip()
        print(f"GPIO changed: {value}")
```

## Safety Considerations

⚠️ **Important**: 
- Never connect GPIO pins directly to voltages > 3.3V
- Always use current-limiting resistors
- Use ESD protection for external connections
- Keep wire lengths short to avoid interference
- Use proper grounding

## References

- [MilkV Duo S GPIO Documentation](https://milkv.io/docs/duo/getting-started/gpio)
- [Linux GPIO Sysfs Interface](https://www.kernel.org/doc/Documentation/gpio/sysfs.txt)
- [duo-pinmux Tool Documentation](https://github.com/milkv-duo/duo-examples)

## Need Help?

If you encounter issues with GPIO configuration:
1. Check board documentation for your specific GPIO layout
2. Verify connections with a multimeter
3. Test GPIO in isolation before integrating with MIDI adapter
4. Ask for help on MilkV Community Forum

Happy MIDI controlling! 🎛️
