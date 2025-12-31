# MIDI Adapter Configuration Examples

This directory contains example configuration files for different use cases.

## Available Examples

### 1. `config-network-only.json`
**Use Case**: USB MIDI to Network MIDI bridge only
- ✅ Network MIDI enabled
- ❌ DIN MIDI disabled
- ❌ No GPIO buttons

**Best for**: Wireless MIDI over Ethernet/WiFi to computers and DAWs

### 2. `config-uart-only.json`
**Use Case**: USB MIDI to DIN MIDI converter only
- ✅ DIN MIDI enabled
- ❌ Network MIDI disabled
- ❌ No GPIO buttons

**Best for**: Connecting modern USB MIDI devices to vintage hardware with DIN MIDI

### 3. `config-full-featured.json`
**Use Case**: Complete MIDI router with all features
- ✅ DIN MIDI enabled
- ✅ Network MIDI enabled
- ✅ GPIO button controls

**Best for**: Professional MIDI routing with multiple outputs and control options

## Using These Examples

### Copy an example to use as your main config:
```bash
cp /root/midi-adapter/examples/config-network-only.json /root/midi-adapter/config.json
/etc/init.d/S99midi-adapter restart
```

### Switch between configurations:
```bash
# Use network-only config
cp /root/midi-adapter/examples/config-network-only.json /root/midi-adapter/config.json
/etc/init.d/S99midi-adapter restart

# Switch to UART-only config
cp /root/midi-adapter/examples/config-uart-only.json /root/midi-adapter/config.json
/etc/init.d/S99midi-adapter restart
```

## Customizing Configurations

Before using any example:

1. **Find your MIDI port numbers**:
   ```bash
   aconnect -l
   ```

2. **Update the routing section** with actual port numbers:
   ```json
   "routing": [
     {
       "source": "14:0",  # Your USB MIDI port
       "destination": "20:0"  # Your destination port
     }
   ]
   ```

3. **Adjust GPIO numbers** (if using buttons):
   ```bash
   duo-pinmux -l  # List available GPIO pins
   ```

4. **Verify UART device** (if using DIN MIDI):
   ```bash
   ls -l /dev/ttyS*
   ```

## Creating Your Own Configuration

Start with an example and modify:
```bash
cp /root/midi-adapter/examples/config-full-featured.json /root/midi-adapter/my-config.json
nano /root/midi-adapter/my-config.json
# Edit as needed
python3 /root/midi-adapter/midi_adapter.py /root/midi-adapter/my-config.json
```

## Testing Configurations

Test a configuration without affecting the running service:
```bash
# Stop the service
/etc/init.d/S99midi-adapter stop

# Test your config manually
python3 /root/midi-adapter/midi_adapter.py /root/midi-adapter/examples/config-network-only.json

# If it works, make it permanent
cp /root/midi-adapter/examples/config-network-only.json /root/midi-adapter/config.json
/etc/init.d/S99midi-adapter start
```

## Configuration Parameters Reference

### uart_midi
- `enabled`: true/false - Enable DIN MIDI output
- `device`: UART device path (e.g., /dev/ttyS4)

### network_midi
- `enabled`: true/false - Enable Network MIDI
- `port`: TCP port number (default: 5004)

### gpio_buttons
Array of button objects:
- `gpio`: GPIO number
- `action`: Action to perform ("toggle_routing", "reconnect", or custom)

### routing
Array of routing rules:
- `source`: Source ALSA MIDI port (e.g., "14:0")
- `destination`: Destination ALSA MIDI port (e.g., "20:0")

## Troubleshooting

If a configuration doesn't work:

1. **Validate JSON syntax**:
   ```bash
   python3 -m json.tool /root/midi-adapter/config.json
   ```

2. **Check MIDI ports exist**:
   ```bash
   aconnect -l
   ```

3. **View error messages**:
   ```bash
   /etc/init.d/S99midi-adapter stop
   python3 /root/midi-adapter/midi_adapter.py
   ```

4. **Test UART device**:
   ```bash
   stty -F /dev/ttyS4 -a
   ```

## More Information

- See `/root/midi-adapter/README.md` for full documentation
- See `/root/midi-adapter/GPIO_REFERENCE.md` for GPIO details
- See `/root/midi-adapter/QUICKSTART.md` for setup guide
