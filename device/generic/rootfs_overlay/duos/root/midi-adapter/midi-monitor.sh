#!/bin/bash
# MIDI Monitor Utility for MilkV Duo S
# Quick utility to monitor MIDI activity

echo "=== MIDI Monitor Utility ==="
echo ""

# Function to display menu
show_menu() {
    echo "Available Options:"
    echo "1. List all MIDI ports"
    echo "2. Monitor MIDI events (all ports)"
    echo "3. Monitor specific MIDI port"
    echo "4. Show MIDI routing connections"
    echo "5. Test MIDI output"
    echo "6. Exit"
    echo ""
}

# Function to list MIDI ports
list_ports() {
    echo "--- MIDI Ports ---"
    aconnect -l
    echo ""
}

# Function to monitor all MIDI
monitor_all() {
    echo "Monitoring all MIDI ports... (Press Ctrl+C to stop)"
    aseqdump
}

# Function to monitor specific port
monitor_port() {
    echo "Available ports:"
    aconnect -l | grep "client"
    echo ""
    read -p "Enter port number (e.g., 14:0): " PORT
    echo "Monitoring port $PORT... (Press Ctrl+C to stop)"
    aseqdump -p "$PORT"
}

# Function to show routing
show_routing() {
    echo "--- Current MIDI Connections ---"
    aconnect -l
    echo ""
    echo "Use 'aconnect <source> <destination>' to create connections"
    echo "Use 'aconnect -d <source> <destination>' to disconnect"
    echo ""
}

# Function to test MIDI output
test_output() {
    echo "Available output ports:"
    aconnect -o
    echo ""
    read -p "Enter destination port (e.g., 20:0): " DEST
    
    if [ -n "$DEST" ]; then
        echo "Sending test MIDI note (Middle C) to port $DEST..."
        # Create temporary MIDI file with a note
        TMPFILE="/tmp/test_midi.mid"
        
        # Simple MIDI note using aplaymidi if available
        if command -v aplaymidi &> /dev/null; then
            # Generate a simple MIDI file
            echo "Playing test note..."
            # Note: This requires a MIDI file. Alternative is to use amidi
        fi
        
        # Alternative: Use amidi to send raw MIDI
        if command -v amidi &> /dev/null; then
            # Send Note On, Middle C (60), Velocity 64
            echo "Sending Note On..."
            echo -ne '\x90\x3C\x40' | amidi -p "$DEST" -s 2>/dev/null
            sleep 1
            # Send Note Off
            echo "Sending Note Off..."
            echo -ne '\x80\x3C\x00' | amidi -p "$DEST" -s 2>/dev/null
        else
            echo "amidi not available for testing"
        fi
    fi
    echo ""
}

# Main loop
while true; do
    show_menu
    read -p "Select option (1-6): " CHOICE
    echo ""
    
    case $CHOICE in
        1)
            list_ports
            ;;
        2)
            monitor_all
            ;;
        3)
            monitor_port
            ;;
        4)
            show_routing
            ;;
        5)
            test_output
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            echo ""
            ;;
    esac
done
