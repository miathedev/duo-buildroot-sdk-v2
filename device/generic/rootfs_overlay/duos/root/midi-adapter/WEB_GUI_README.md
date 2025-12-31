# MIDI Adapter Web GUI - User Guide

## Overview

The MIDI Adapter Web GUI provides a user-friendly interface for configuring and monitoring your MIDI routing adapter. It runs as a separate service from the main MIDI application, ensuring that your MIDI routing continues uninterrupted even if you're modifying the configuration.

## Features

### 🎛️ Configuration Management
- **JSON Editor**: Edit configuration with syntax highlighting
- **Visual Device Overview**: See all devices at a glance
- **Real-time Validation**: Check configuration before saving
- **Automatic Backups**: Every save creates a timestamped backup

### 📊 Monitoring
- **Service Status**: Real-time status updates every 5 seconds
- **Log Viewer**: View recent application logs
- **Device Status**: See which devices are enabled/disabled

### 🔄 Control
- **Reload Configuration**: Apply changes without restarting (hot-reload)
- **Restart Service**: Full service restart when needed
- **Manual Validation**: Test configuration before applying

## Accessing the Web GUI

### Default Access
```
URL: http://<device-ip>:8080
Port: 8080
Authentication: None (open access)
```

### Finding Your Device IP
```bash
# On the device
ip addr show eth0

# Or check router/DHCP server
```

### Starting the Web GUI Service
```bash
# Start web GUI
/etc/init.d/S99midi-webui start

# Check if running
/etc/init.d/S99midi-webui status

# Stop web GUI
/etc/init.d/S99midi-webui stop
```

## Using the Web Interface

### Main Dashboard

The interface consists of four main tabs:

#### 1. 📝 JSON Editor Tab
- Edit the complete configuration as JSON
- Full syntax highlighting and formatting
- Buttons:
  - **✓ Validate**: Check JSON syntax and structure
  - **💾 Save Configuration**: Write changes to disk
  - **↻ Reload from File**: Discard changes and reload

**Usage Flow:**
1. Edit the JSON in the text area
2. Click "Validate" to check for errors
3. Click "Save Configuration" to write to disk
4. Click "Reload Config" in the header to apply changes

#### 2. 📊 Visual Editor Tab
- Card-based view of all devices
- Shows device type, status, and properties
- Quick overview without editing JSON

**Information Displayed:**
- Device name and alias
- Device type (USB, UART, Network, GPIO, OSC)
- Enabled/disabled status
- Device-specific configuration (baudrate, IP, GPIO number, etc.)

#### 3. 📋 Logs Tab
- View recent application logs
- Scroll through log history
- Refresh button to load latest entries

**Tips:**
- Shows last 200 log lines by default
- Use Ctrl+F to search within logs
- Useful for troubleshooting routing issues

#### 4. ℹ️ About Tab
- Version information
- Feature list
- Quick reference

### Header Controls

Located at the top of every page:

#### Status Indicator
- **Green Dot (pulsing)**: Service is running
- **Red Dot**: Service is stopped
- Updates automatically every 5 seconds

#### Action Buttons
- **🔄 Reload Config**: Hot-reload without restart (SIGHUP)
- **⚡ Restart Service**: Full service restart
- **↻ Refresh**: Manually refresh service status

## Configuration Workflow

### Typical Workflow
1. **Edit Configuration**
   - Switch to JSON Editor tab
   - Make your changes
   - Click "Validate" to check for errors

2. **Save Changes**
   - Click "Save Configuration"
   - Backup is automatically created
   - Wait for success message

3. **Apply Changes**
   - Click "Reload Config" in header
   - Or restart service if hot-reload fails
   - Check logs for any issues

### Hot-Reload vs Restart

#### Hot-Reload (Recommended)
- **Command**: Reload Config button
- **How it works**: Sends SIGHUP signal
- **Pros**: No downtime, MIDI continues
- **Cons**: Some changes may require restart

```bash
# Equivalent command line
kill -HUP $(cat /var/run/midi-adapter.pid)
```

#### Full Restart
- **Command**: Restart Service button
- **How it works**: Stops and starts service
- **Pros**: Guaranteed clean state
- **Cons**: Brief interruption (2-3 seconds)

```bash
# Equivalent command line
/etc/init.d/S98midi-adapter restart
```

## API Reference

The web GUI exposes a REST API that can be used programmatically:

### GET /api/config
Get current configuration.

**Response:**
```json
{
  "success": true,
  "config": { ... }
}
```

### POST /api/config
Update configuration.

**Request Body:**
```json
{
  "devices": { ... },
  "routing_profiles": { ... },
  "settings": { ... }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration saved successfully"
}
```

### GET /api/status
Get service status.

**Response:**
```json
{
  "success": true,
  "status": {
    "running": true,
    "message": "MIDI Adapter is running (PID: 1234)"
  }
}
```

### POST /api/reload
Reload configuration (hot-reload).

**Response:**
```json
{
  "success": true,
  "message": "Configuration reload signal sent"
}
```

### POST /api/restart
Restart service.

**Response:**
```json
{
  "success": true,
  "message": "Service restarted successfully"
}
```

### POST /api/validate
Validate configuration JSON.

**Request Body:**
```json
{
  "devices": { ... },
  "routing_profiles": { ... },
  "settings": { ... }
}
```

**Response (success):**
```json
{
  "success": true,
  "message": "Configuration is valid"
}
```

**Response (errors):**
```json
{
  "success": false,
  "errors": ["Missing required section: devices"]
}
```

### GET /api/logs?lines=100
Get recent log entries.

**Parameters:**
- `lines`: Number of lines to return (default: 100)

**Response:**
```json
{
  "success": true,
  "logs": "2024-12-31 10:00:00 - midi-adapter - INFO - Starting..."
}
```

## Troubleshooting

### Web GUI Won't Start

**Check if Flask is installed:**
```bash
python3 -c "import flask" && echo "Flask installed" || echo "Flask missing"
```

**Install Flask manually:**
```bash
pip3 install flask
```

**Check service logs:**
```bash
cat /var/log/midi-webui.log
```

### Cannot Access Web Interface

**Check if service is running:**
```bash
/etc/init.d/S99midi-webui status
```

**Check if port 8080 is open:**
```bash
netstat -tlnp | grep 8080
```

**Check firewall:**
```bash
# If using iptables
iptables -L -n | grep 8080

# Allow port 8080
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

### Configuration Not Applying

**Try hot-reload first:**
1. Click "Reload Config" button
2. Check logs for errors
3. Verify service is running

**If hot-reload fails, use restart:**
1. Click "Restart Service" button
2. Wait 3-5 seconds
3. Refresh status
4. Check logs

**Verify file permissions:**
```bash
ls -l /root/midi-adapter/config.json
# Should be readable/writable
chmod 644 /root/midi-adapter/config.json
```

### Backups and Recovery

**Find backup files:**
```bash
ls -lt /root/midi-adapter/config.json.backup.*
```

**Restore from backup:**
```bash
cp /root/midi-adapter/config.json.backup.YYYYMMDD_HHMMSS /root/midi-adapter/config.json
/etc/init.d/S98midi-adapter reload
```

## Security Considerations

### Network Access
The web GUI runs without authentication on port 8080. Consider:

**1. Firewall Rules**
```bash
# Allow only from local network
iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP
```

**2. Disable When Not Needed**
```bash
# Stop web GUI in production
/etc/init.d/S99midi-webui stop

# Disable autostart
rm /etc/init.d/S99midi-webui
```

**3. VPN Access Only**
- Use WireGuard or OpenVPN
- Access web GUI only through VPN
- Keep port 8080 closed on public interface

### File Permissions
```bash
# Secure configuration files
chmod 600 /root/midi-adapter/config.json
chown root:root /root/midi-adapter/config.json

# Web GUI can still read/write as root
```

## Advanced Usage

### Remote API Access

**Using curl:**
```bash
# Get configuration
curl http://device-ip:8080/api/config

# Reload configuration
curl -X POST http://device-ip:8080/api/reload

# Validate configuration
curl -X POST http://device-ip:8080/api/validate \
  -H "Content-Type: application/json" \
  -d @config.json
```

### Automation Scripts

**Auto-reload on file change:**
```bash
#!/bin/bash
# watch-config.sh
CONFIG="/root/midi-adapter/config.json"
LAST_MODIFIED=$(stat -c %Y "$CONFIG")

while true; do
  CURRENT=$(stat -c %Y "$CONFIG")
  if [ "$CURRENT" != "$LAST_MODIFIED" ]; then
    echo "Config changed, reloading..."
    kill -HUP $(cat /var/run/midi-adapter.pid)
    LAST_MODIFIED=$CURRENT
  fi
  sleep 5
done
```

### Multiple Instances

To run multiple MIDI adapters with separate web GUIs:

1. Copy configuration to different directory
2. Modify web GUI app.py to use different config path
3. Change port number in app.py (e.g., 8081, 8082)
4. Create separate init scripts with different PIDs

## Screenshots

### Main Dashboard
![Dashboard with status indicator and action buttons]

### JSON Editor
![Syntax-highlighted JSON editor with validation]

### Visual Device Overview
![Card-based device view with status indicators]

### Log Viewer
![Terminal-style log display with color coding]

## Tips and Best Practices

1. **Always Validate First**
   - Use the validate button before saving
   - Catch syntax errors early

2. **Use Hot-Reload**
   - Faster than restart
   - No interruption to MIDI routing
   - Check logs after reload

3. **Keep Backups**
   - Backups are created automatically
   - Clean old backups periodically
   - Test restore procedure

4. **Monitor Logs**
   - Check logs after configuration changes
   - Look for error messages
   - Use logs for debugging routing issues

5. **Test Incrementally**
   - Make small changes
   - Test after each change
   - Easier to identify problems

## Getting Help

### Check Logs
```bash
# Web GUI logs
tail -f /var/log/midi-webui.log

# Main application logs
tail -f /var/log/midi-adapter.log
```

### Documentation
- Main README: `/root/midi-adapter/README.md`
- Quick Start: `/root/midi-adapter/QUICKSTART.md`
- GPIO Reference: `/root/midi-adapter/GPIO_REFERENCE.md`
- Changelog: `/root/midi-adapter/CHANGELOG.md`

### Support Resources
- GitHub Issues: Check repository for known issues
- Documentation: Read all docs in `/root/midi-adapter/`
- Examples: See `/root/midi-adapter/examples/` for config samples
