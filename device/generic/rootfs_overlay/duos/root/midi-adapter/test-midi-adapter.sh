#!/bin/bash
# MIDI Adapter Test Script for MilkV Duo S
# This script tests the MIDI adapter functionality

echo "=== MilkV Duo S MIDI Adapter Test ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test functions
test_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

test_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

test_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test 1: Check kernel modules
echo "Test 1: Checking ALSA MIDI kernel modules..."
MODULES="snd_seq snd_seq_midi snd_rawmidi"
MODULE_OK=true
for mod in $MODULES; do
    if lsmod | grep -q "^$mod"; then
        test_pass "Module $mod is loaded"
    else
        test_fail "Module $mod is NOT loaded"
        MODULE_OK=false
    fi
done

if [ "$MODULE_OK" = false ]; then
    echo "  Attempting to load modules..."
    modprobe snd-seq
    modprobe snd-seq-midi
    modprobe snd-rawmidi
fi

echo ""

# Test 2: Check ALSA utilities
echo "Test 2: Checking ALSA MIDI utilities..."
UTILS="aconnect aseqnet amidi aplaymidi arecordmidi aseqdump"
for util in $UTILS; do
    if command -v $util &> /dev/null; then
        test_pass "$util is installed"
    else
        test_fail "$util is NOT installed"
    fi
done

echo ""

# Test 3: Check MIDI ports
echo "Test 3: Checking MIDI ports..."
if command -v aconnect &> /dev/null; then
    PORT_COUNT=$(aconnect -l | grep -c "client")
    if [ $PORT_COUNT -gt 0 ]; then
        test_pass "Found $PORT_COUNT MIDI port(s)"
        echo "Available MIDI ports:"
        aconnect -l
    else
        test_warn "No MIDI ports found (plug in USB MIDI device)"
    fi
else
    test_fail "aconnect not available"
fi

echo ""

# Test 4: Check USB host mode
echo "Test 4: Checking USB host mode..."
if [ -f /proc/cviusb/otg_role ]; then
    USB_ROLE=$(cat /proc/cviusb/otg_role)
    if [ "$USB_ROLE" = "host" ]; then
        test_pass "USB is in HOST mode"
    else
        test_warn "USB is in $USB_ROLE mode (should be 'host')"
    fi
else
    test_warn "Cannot determine USB mode (/proc/cviusb/otg_role not found)"
fi

echo ""

# Test 5: Check network connectivity
echo "Test 5: Checking network connectivity..."
if ip addr show eth0 | grep -q "inet "; then
    IP_ADDR=$(ip addr show eth0 | grep "inet " | awk '{print $2}')
    test_pass "Ethernet has IP: $IP_ADDR"
else
    test_warn "Ethernet interface eth0 has no IP address"
fi

echo ""

# Test 6: Check network MIDI server
echo "Test 6: Checking network MIDI server (aseqnet)..."
if ps aux | grep -v grep | grep -q aseqnet; then
    test_pass "aseqnet is running"
else
    test_warn "aseqnet is NOT running"
fi

echo ""

# Test 7: Check UART device
echo "Test 7: Checking UART device for DIN MIDI..."
UART_DEV="/dev/ttyS4"
if [ -e "$UART_DEV" ]; then
    test_pass "UART device $UART_DEV exists"
    
    # Check UART configuration
    if command -v stty &> /dev/null; then
        BAUD=$(stty -F $UART_DEV speed 2>/dev/null)
        if [ "$BAUD" = "31250" ]; then
            test_pass "UART is configured for MIDI (31250 baud)"
        else
            test_warn "UART baud rate is $BAUD (MIDI requires 31250)"
        fi
    fi
else
    test_fail "UART device $UART_DEV does NOT exist"
fi

echo ""

# Test 8: Check MIDI adapter service
echo "Test 8: Checking MIDI adapter service..."
if [ -f /etc/init.d/S99midi-adapter ]; then
    test_pass "MIDI adapter init script exists"
    
    if [ -f /var/run/midi-adapter.pid ]; then
        PID=$(cat /var/run/midi-adapter.pid)
        if ps -p $PID > /dev/null 2>&1; then
            test_pass "MIDI adapter is running (PID: $PID)"
        else
            test_warn "MIDI adapter PID file exists but process is not running"
        fi
    else
        test_warn "MIDI adapter is not running"
    fi
else
    test_fail "MIDI adapter init script NOT found"
fi

echo ""

# Test 9: Check configuration file
echo "Test 9: Checking MIDI adapter configuration..."
CONFIG="/root/midi-adapter/config.json"
if [ -f "$CONFIG" ]; then
    test_pass "Configuration file exists: $CONFIG"
    
    # Validate JSON
    if command -v python3 &> /dev/null; then
        if python3 -m json.tool "$CONFIG" > /dev/null 2>&1; then
            test_pass "Configuration JSON is valid"
        else
            test_fail "Configuration JSON is INVALID"
        fi
    fi
else
    test_fail "Configuration file NOT found: $CONFIG"
fi

echo ""

# Test 10: Check USB MIDI devices
echo "Test 10: Checking for USB MIDI devices..."
if command -v lsusb &> /dev/null; then
    USB_MIDI=$(lsusb | grep -i "midi\|audio")
    if [ -n "$USB_MIDI" ]; then
        test_pass "USB MIDI/Audio device detected:"
        echo "$USB_MIDI"
    else
        test_warn "No USB MIDI devices found"
        echo "  All USB devices:"
        lsusb
    fi
else
    test_warn "lsusb command not available"
fi

echo ""
echo "=== Test Summary ==="
echo "Review the results above. GREEN = Pass, YELLOW = Warning, RED = Fail"
echo ""
echo "Next steps:"
echo "1. If USB MIDI device not detected, check USB connection"
echo "2. If MIDI adapter is not running, start it: /etc/init.d/S99midi-adapter start"
echo "3. Check configuration: nano /root/midi-adapter/config.json"
echo "4. Monitor MIDI events: aseqdump -p <port>"
echo "5. View full documentation: cat /root/midi-adapter/README.md"
echo ""
