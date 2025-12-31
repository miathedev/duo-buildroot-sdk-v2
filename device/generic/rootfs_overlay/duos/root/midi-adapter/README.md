# USB MIDI to DIN MIDI and Network MIDI Adapter
## For MilkV Duo S (512MB RAM)

This configuration transforms the MilkV Duo S into a versatile MIDI adapter that can route MIDI messages between:
- **USB MIDI** devices (connected via USB Host)
- **DIN MIDI** output (via Hardware UART)
- **Network MIDI** (via Ethernet using RTP-MIDI protocol)
- **GPIO Buttons** for control and triggering
- **Web-Based Configuration** interface for easy setup

## Features

- ✅ USB MIDI input from any USB MIDI controller or keyboard
- ✅ DIN MIDI output via hardware UART (standard 5-pin DIN MIDI)
- ✅ Network MIDI over Ethernet (RTP-MIDI compatible)
- ✅ GPIO button support for custom control actions
- ✅ Flexible routing configuration via JSON
- ✅ **Web-based configuration GUI** (NEW in v2.1)
- ✅ **Hot-reload configuration** without service restart
- ✅ Real-time MIDI debugging and monitoring
- ✅ DHCP network configuration
- ✅ Automatic startup on boot
- ✅ Python-based, easy to customize

## Quick Start

### Access Web GUI (Easiest Method)
1. Power on your MilkV Duo S with the MIDI adapter image
2. Connect via Ethernet (DHCP will assign an IP)
3. Find device IP: Check your router or run `ip addr` on device
4. Open browser to `http://<device-ip>:8080`
5. Configure MIDI routing through the web interface!

**See [WEB_GUI_README.md](WEB_GUI_README.md) for detailed web GUI documentation.**

## Hardware Requirements

### MilkV Duo S Board
- **Model**: MilkV Duo S with 512MB RAM
- **USB**: USB Host capability (built-in)
- **Ethernet**: Built-in Ethernet port
- **UART**: Hardware UART for DIN MIDI output

### External Hardware
- **USB MIDI Device**: Any USB MIDI keyboard, controller, or interface
- **DIN MIDI Connection**: UART to MIDI optocoupler circuit (see schematics below)
- **GPIO Buttons** (optional): Momentary push buttons connected to GPIO pins
- **Ethernet Cable**: For Network MIDI functionality

## DIN MIDI Hardware Connection

DIN MIDI requires a simple optocoupler circuit connected to a UART port. Here's the standard MIDI output circuit:

```
UART TX (3.3V) ──┬─── 220Ω ───┬─── LED+ (6N138 Optocoupler)
                 │             │
                 │             └─── DIN Pin 5 (MIDI Current Source)
                 │
                 └─── GND ─────────── DIN Pin 2 (MIDI Shield)
                 
Optocoupler Output ──────────────── DIN Pin 4 (MIDI Signal)
                 
+5V ─────────────────────────────── DIN Pin 4 (via 220Ω)
```

**Note**: The standard MIDI baud rate is 31250 bps. The adapter automatically configures the UART.

### Recommended UART Port
- Default: `/dev/ttyS4` (configurable in `config.json`)
- Check your device tree for available UART ports

## Software Architecture

### Components

1. **Kernel Modules**
   - `snd-seq`: ALSA sequencer
   - `snd-seq-midi`: ALSA MIDI sequencer interface
   - `snd-rawmidi`: Raw MIDI interface
   - `snd-usb-midi`: USB MIDI driver
   - `snd-serial-u16550`: Serial UART MIDI driver (for DIN MIDI)

2. **ALSA Utilities**
   - `aconnect`: MIDI connection manager
   - `aseqnet`: Network MIDI server
   - `amidi`: Raw MIDI communication
   - `aplaymidi`, `arecordmidi`: MIDI file playback/recording
   - `aseqdump`: MIDI event monitoring

3. **MIDI Adapter Application** (`midi_adapter.py`)
   - Python 3 application
   - Manages MIDI routing
   - Handles GPIO button events
   - Configures UART and network MIDI
   - Responds to SIGHUP for configuration reload

4. **Web Configuration GUI** (`webui/app.py`) - NEW in v2.1
   - Flask-based web interface (Port 8080)
   - Real-time configuration editor
   - Service control and monitoring
   - Independent from main MIDI application
   - See [WEB_GUI_README.md](WEB_GUI_README.md) for details

### Service Architecture

The system runs two independent services:

#### Main MIDI Adapter Service
- **Init Script**: `/etc/init.d/S98midi-adapter`
- **PID File**: `/var/run/midi-adapter.pid`
- **Log File**: `/var/log/midi-adapter.log`
- **Purpose**: Handles all MIDI routing and device management
- **Commands**:
  ```bash
  /etc/init.d/S98midi-adapter start    # Start service
  /etc/init.d/S98midi-adapter stop     # Stop service
  /etc/init.d/S98midi-adapter restart  # Full restart
  /etc/init.d/S98midi-adapter reload   # Hot-reload config (SIGHUP)
  /etc/init.d/S98midi-adapter status   # Check status
  ```

#### Web GUI Service (Optional)
- **Init Script**: `/etc/init.d/S99midi-webui`
- **PID File**: `/var/run/midi-webui.pid`
- **Log File**: `/var/log/midi-webui.log`
- **Purpose**: Provides web-based configuration interface
- **Port**: 8080 (HTTP)
- **Commands**:
  ```bash
  /etc/init.d/S99midi-webui start     # Start web GUI
  /etc/init.d/S99midi-webui stop      # Stop web GUI
  /etc/init.d/S99midi-webui restart   # Restart web GUI
  /etc/init.d/S99midi-webui status    # Check status
  ```

**Note**: Main MIDI adapter works independently. Web GUI is optional.

## Building the Image

### Prerequisites
- Linux development machine (Ubuntu 20.04+ recommended)
- At least 50GB free disk space
- Required packages installed (see buildroot-sdk documentation)

### Build Steps

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/miathedev/duo-buildroot-sdk-v2.git
   cd duo-buildroot-sdk-v2
   ```

2. **Select the board configuration**:
   ```bash
   ./build.sh lunch
   ```
   Select: `milkv-duos-glibc-arm64-sd`

3. **Build the image**:
   ```bash
   ./build.sh
   ```
   This will take 30-60 minutes depending on your system.

4. **Flash to SD card**:
   ```bash
   sudo dd if=out/milkv-duos-glibc-arm64-sd_*.img of=/dev/sdX bs=4M status=progress
   sudo sync
   ```
   Replace `/dev/sdX` with your SD card device.

## Configuration

### Main Configuration File

The MIDI adapter is configured via `/root/midi-adapter/config.json`:

```json
{
  "uart_midi": {
    "enabled": true,
    "device": "/dev/ttyS4"
  },
  
  "network_midi": {
    "enabled": true,
    "port": 5004
  },
  
  "gpio_buttons": [
    {
      "gpio": 466,
      "action": "toggle_routing"
    }
  ],
  
  "routing": [
    {
      "source": "14:0",
      "destination": "20:0",
      "comment": "USB MIDI to DIN MIDI"
    },
    {
      "source": "14:0",
      "destination": "128:0",
      "comment": "USB MIDI to Network MIDI"
    }
  ]
}
```

### Configuration Parameters

#### UART MIDI
- **enabled**: Enable/disable DIN MIDI output
- **device**: UART device path (e.g., `/dev/ttyS4`)

#### Network MIDI
- **enabled**: Enable/disable network MIDI server
- **port**: TCP port for network MIDI (default: 5004)

#### GPIO Buttons
Array of button configurations:
- **gpio**: GPIO number (use `duo-pinmux` to find pin numbers)
- **action**: Action to perform on button press
  - `toggle_routing`: Toggle MIDI routing on/off
  - `reconnect`: Re-establish MIDI connections

#### Routing
Array of MIDI routing rules:
- **source**: Source ALSA MIDI port (e.g., "14:0")
- **destination**: Destination ALSA MIDI port (e.g., "20:0")

### Finding MIDI Port Numbers

After booting the board, connect via SSH and run:

```bash
aconnect -l
```

This will show all available ALSA MIDI ports:

```
client 14: 'USB MIDI Device' [type=kernel]
    0 'USB MIDI Device MIDI 1'
client 20: 'UART MIDI' [type=kernel]
    0 'UART MIDI MIDI 1'
client 128: 'Client-128' [type=user]
    0 'Network MIDI'
```

Use these numbers in your routing configuration.

### GPIO Pin Mapping

To find GPIO numbers for your board:

```bash
# List available GPIOs
ls /sys/class/gpio/

# Or use duo-pinmux tool
duo-pinmux -l
```

Example GPIO numbers for common pins on Duo S:
- GP0: 466
- GP1: 467
- GP2: 477
- GP3: 478

(Consult the MilkV Duo S pinout diagram for your specific setup)

## Network Configuration

### DHCP (Default)
By default, the board obtains an IP address via DHCP:

```bash
# Check IP address
ip addr show eth0
```

### Static IP (Optional)
Edit `/etc/network/interfaces`:

```
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
```

Then restart networking:
```bash
/etc/init.d/S40network restart
```

## Usage

### Automatic Start
The MIDI adapter starts automatically on boot via the init script at `/etc/init.d/S99midi-adapter`.

### Manual Control

Start the adapter:
```bash
/etc/init.d/S99midi-adapter start
```

Stop the adapter:
```bash
/etc/init.d/S99midi-adapter stop
```

Restart the adapter:
```bash
/etc/init.d/S99midi-adapter restart
```

Check status:
```bash
/etc/init.d/S99midi-adapter status
```

### Running Manually
```bash
python3 /root/midi-adapter/midi_adapter.py /root/midi-adapter/config.json
```

### Viewing Logs
```bash
# View system log
dmesg | grep -i midi

# Monitor MIDI events
aseqdump -p 14:0  # Replace 14:0 with your USB MIDI port
```

## Network MIDI Clients

### macOS
1. Open **Audio MIDI Setup**
2. Go to **MIDI Studio** (Cmd+2)
3. Double-click **Network** icon
4. Add a new session with your board's IP address and port 5004

### Windows
Use RTP-MIDI compatible software like:
- **rtpMIDI** by Tobias Erichsen
- Configure with board IP and port 5004

### Linux
```bash
# Connect to network MIDI
aconnect <local-port> <network-port>
```

### iOS/iPad
Use apps like **MIDI Network Setup** to connect to the board's IP address.

## Troubleshooting

### USB MIDI Device Not Detected
```bash
# Check USB devices
lsusb

# Check kernel messages
dmesg | tail -20

# Verify USB host mode
cat /proc/cviusb/otg_role
# Should show: host
```

### No MIDI Ports Visible
```bash
# Load MIDI modules manually
modprobe snd-seq
modprobe snd-seq-midi
modprobe snd-rawmidi
modprobe snd-usb-midi

# List MIDI ports
aconnect -l
```

### Network MIDI Not Working
```bash
# Check if aseqnet is running
ps aux | grep aseqnet

# Check network connectivity
ping <client-ip>

# Verify firewall (if any)
iptables -L
```

### GPIO Buttons Not Working
```bash
# Check GPIO export
ls /sys/class/gpio/gpio466  # Replace with your GPIO number

# Manually test GPIO
echo 466 > /sys/class/gpio/export
echo in > /sys/class/gpio/gpio466/direction
cat /sys/class/gpio/gpio466/value
```

### UART MIDI Not Working
```bash
# Check UART device exists
ls -l /dev/ttyS*

# Verify UART configuration
stty -F /dev/ttyS4 -a

# Send test MIDI message
echo -ne '\x90\x3C\x40' > /dev/ttyS4  # Note On, Middle C
```

## Advanced Configuration

### Custom MIDI Routing Scripts
Create custom routing scripts in `/root/midi-adapter/scripts/`:

```bash
#!/bin/sh
# custom-routing.sh
aconnect 14:0 20:0  # USB to DIN MIDI
aconnect 14:0 128:0 # USB to Network MIDI
```

### Multiple USB MIDI Devices
The system supports multiple USB MIDI devices. They will appear as separate ALSA ports. Update your routing configuration accordingly.

### MIDI Filtering
Use `aconnect` with ALSA plugins for MIDI filtering, transposition, etc.

## Development

### Modifying the Python Application
Edit `/root/midi-adapter/midi_adapter.py` and restart the service:

```bash
/etc/init.d/S99midi-adapter restart
```

### Adding Custom Button Actions
Edit the `handle_button_press` method in `midi_adapter.py`:

```python
def handle_button_press(self, gpio_num, action):
    if action == "my_custom_action":
        # Your custom code here
        pass
```

## Performance and Latency

- **MIDI Latency**: < 5ms (typical)
- **CPU Usage**: < 5% (idle), < 15% (active MIDI)
- **RAM Usage**: ~50MB
- **Network MIDI Latency**: Depends on network (typically 5-20ms on LAN)

## References

- [MilkV Duo S Documentation](https://milkv.io/docs/duo)
- [ALSA Sequencer Documentation](https://www.alsa-project.org/alsa-doc/alsa-lib/seq.html)
- [MIDI Specification](https://www.midi.org/specifications)
- [RTP-MIDI RFC 6295](https://datatracker.ietf.org/doc/html/rfc6295)

## License

This configuration and code are released under the same license as the duo-buildroot-sdk-v2 project.

## Contributing

Improvements and bug fixes are welcome! Please submit issues and pull requests to the repository.

## Support

For issues specific to this MIDI adapter configuration, please open an issue on the repository.

For general MilkV Duo S support, visit the [MilkV Community Forum](https://community.milkv.io/).
