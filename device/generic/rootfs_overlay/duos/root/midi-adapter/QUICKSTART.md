# Quick Start Guide - MIDI Adapter for MilkV Duo S

## What You Need

1. MilkV Duo S board (512MB RAM)
2. SD card (16GB or larger)
3. USB MIDI keyboard/controller
4. Ethernet cable (for Network MIDI)
5. Power supply (5V)
6. Optional: GPIO buttons and wiring for custom controls
7. Optional: UART to MIDI circuit for DIN MIDI output

## Step 1: Build or Download the Image

### Option A: Build from Source
```bash
git clone https://github.com/miathedev/duo-buildroot-sdk-v2.git
cd duo-buildroot-sdk-v2
./build.sh lunch
# Select: milkv-duos-glibc-arm64-sd
./build.sh
```

### Option B: Download Pre-built Image
(If available from releases)

## Step 2: Flash to SD Card

```bash
# On Linux/macOS
sudo dd if=out/milkv-duos-glibc-arm64-sd_*.img of=/dev/sdX bs=4M status=progress
sudo sync

# On Windows
# Use Etcher or Win32DiskImager
```

Replace `/dev/sdX` with your SD card device.

## Step 3: First Boot

1. Insert SD card into MilkV Duo S
2. Connect Ethernet cable
3. Connect USB MIDI device
4. Power on the board
5. Wait 30-60 seconds for boot

## Step 4: Find the Board's IP Address

**Option 1**: Check your router's DHCP client list
**Option 2**: Use network scanner like `nmap`:
```bash
nmap -sn 192.168.1.0/24 | grep -B 2 "milkv"
```

## Step 5: Connect via SSH

```bash
ssh root@<board-ip-address>
# Default password: milkv
```

## Step 6: Verify MIDI Setup

```bash
# List MIDI ports
aconnect -l

# Should show:
# - USB MIDI device (if connected)
# - UART MIDI port (for DIN MIDI)
# - Network MIDI port
```

Example output:
```
client 14: 'USB MIDI Keyboard' [type=kernel]
    0 'USB MIDI Keyboard MIDI 1'
client 128: 'aseqnet' [type=user]
    0 'Network'
```

## Step 7: Test MIDI Routing

### Test USB to Network MIDI:
```bash
# Monitor MIDI events
aseqdump -p 14:0
# Play some notes on your USB MIDI keyboard
```

### Create Manual Routing:
```bash
# Route USB MIDI to Network MIDI
aconnect 14:0 128:0
```

## Step 8: Configure for Your Setup

Edit the configuration file:
```bash
nano /root/midi-adapter/config.json
```

Update routing section with your actual port numbers (from `aconnect -l`):
```json
{
  "routing": [
    {
      "source": "14:0",
      "destination": "128:0"
    }
  ]
}
```

Restart the adapter:
```bash
/etc/init.d/S99midi-adapter restart
```

## Step 9: Connect Network MIDI Client

### macOS:
1. Open **Audio MIDI Setup**
2. Window → Show MIDI Studio (Cmd+2)
3. Double-click **Network** icon
4. Click **+** to add new session
5. Enter board's IP address
6. Click **Connect**

### Windows:
1. Download and install **rtpMIDI**
2. Add new session with board's IP address
3. Connect to session

## Step 10: Test Complete Setup

1. Play notes on USB MIDI keyboard
2. Check they arrive on your computer via Network MIDI
3. Use in your DAW (Ableton, Logic, FL Studio, etc.)

## Common Use Cases

### USB MIDI Wireless Bridge
Route USB MIDI to Network MIDI for wireless MIDI over WiFi/Ethernet

### MIDI Merger
Connect multiple USB MIDI devices and merge to one output

### MIDI Router with GPIO Control
Use GPIO buttons to change routing on the fly

## Troubleshooting Quick Tips

**USB MIDI not detected:**
```bash
lsusb  # Should show your MIDI device
dmesg | grep -i midi
```

**Network MIDI not working:**
```bash
ping <your-computer-ip>  # Test network
ps aux | grep aseqnet    # Check if running
```

**MIDI Adapter not starting:**
```bash
/etc/init.d/S99midi-adapter status
python3 /root/midi-adapter/midi_adapter.py  # Run manually to see errors
```

## Next Steps

- Read full documentation in `/root/midi-adapter/README.md`
- Customize GPIO buttons for your needs
- Set up DIN MIDI hardware output
- Create custom routing configurations

## Getting Help

- Check logs: `dmesg | grep -i midi`
- View adapter logs: Run manually to see output
- Community: [MilkV Community Forum](https://community.milkv.io/)
- Report issues on GitHub repository

Enjoy your MIDI adapter! 🎹🎵
