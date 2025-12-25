# Milk-V Duo series buildroot SDK V2

```
./build.sh lunch
```

For more detailed documentation, please refer to: [https://milkv.io/docs/duo/getting-started/buildroot-sdk](https://milkv.io/docs/duo/getting-started/buildroot-sdk)

## 🎹 MIDI Adapter Configuration

This repository includes a complete configuration for building a **USB MIDI to DIN MIDI and Network MIDI adapter** for the MilkV Duo S (512MB RAM).

### Features
- USB MIDI input from keyboards and controllers
- DIN MIDI output via hardware UART
- Network MIDI over Ethernet (RTP-MIDI)
- GPIO button support for custom controls
- Flexible JSON-based configuration
- Auto-start on boot

### Quick Start
1. Build the `milkv-duos-glibc-arm64-sd` configuration
2. Flash to SD card
3. Connect USB MIDI device and Ethernet
4. Access via SSH and configure `/root/midi-adapter/config.json`

📖 **Full Documentation**: [MIDI_ADAPTER.md](MIDI_ADAPTER.md)

