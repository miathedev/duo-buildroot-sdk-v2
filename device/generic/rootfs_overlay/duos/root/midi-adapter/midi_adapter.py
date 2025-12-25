#!/usr/bin/env python3
"""
MIDI Adapter for MilkV Duo S
Configurable adapter for:
- USB MIDI + GPIO Buttons -> DIN MIDI (UART)
- USB MIDI + GPIO Buttons -> Network MIDI (Ethernet)

This script manages MIDI routing between USB MIDI devices, hardware UART (DIN MIDI),
and network MIDI using ALSA sequencer.
"""

import json
import os
import sys
import time
import subprocess
import threading
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('midi-adapter')


class GPIOButton:
    """Handle GPIO button input"""
    
    def __init__(self, gpio_num, callback):
        """
        Initialize GPIO button
        
        Args:
            gpio_num: GPIO number
            callback: Function to call when button is pressed
        """
        self.gpio_num = gpio_num
        self.callback = callback
        self.gpio_path = f"/sys/class/gpio/gpio{gpio_num}"
        self.running = False
        self.thread = None
        
    def setup(self):
        """Export and configure GPIO as input"""
        try:
            # Export GPIO if not already exported
            if not os.path.exists(self.gpio_path):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write(str(self.gpio_num))
                time.sleep(0.1)
            
            # Set direction to input
            with open(f"{self.gpio_path}/direction", "w") as f:
                f.write("in")
            
            # Set edge to falling (button press)
            with open(f"{self.gpio_path}/edge", "w") as f:
                f.write("falling")
                
            logger.info(f"GPIO {self.gpio_num} configured as input")
            return True
        except Exception as e:
            logger.error(f"Failed to setup GPIO {self.gpio_num}: {e}")
            return False
    
    def start_monitoring(self):
        """Start monitoring GPIO button in a separate thread"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started monitoring GPIO {self.gpio_num}")
    
    def _monitor_loop(self):
        """Monitor GPIO value changes"""
        last_value = "1"
        
        while self.running:
            try:
                with open(f"{self.gpio_path}/value", "r") as f:
                    value = f.read().strip()
                
                # Detect falling edge (button press)
                if last_value == "1" and value == "0":
                    logger.info(f"Button press detected on GPIO {self.gpio_num}")
                    self.callback(self.gpio_num)
                
                last_value = value
                time.sleep(0.05)  # 50ms polling
                
            except Exception as e:
                logger.error(f"Error monitoring GPIO {self.gpio_num}: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


class MIDIAdapter:
    """Main MIDI adapter class"""
    
    def __init__(self, config_path="/root/midi-adapter/config.json"):
        """
        Initialize MIDI adapter
        
        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = config_path
        self.config = {}
        self.gpio_buttons = []
        self.running = False
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return True
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return False
    
    def setup_uart_midi(self):
        """Configure UART for DIN MIDI output"""
        uart_config = self.config.get('uart_midi', {})
        
        if not uart_config.get('enabled', False):
            logger.info("UART MIDI is disabled")
            return True
        
        uart_device = uart_config.get('device', '/dev/ttyS4')
        
        # Configure UART for MIDI (31250 baud)
        try:
            # Use stty to configure UART
            subprocess.run([
                'stty', '-F', uart_device,
                '31250', 'raw', '-echo', '-echoe', '-echok'
            ], check=True)
            
            logger.info(f"UART {uart_device} configured for MIDI (31250 baud)")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure UART: {e}")
            return False
    
    def setup_alsa_sequencer(self):
        """Set up ALSA sequencer and load kernel modules"""
        try:
            # Load snd-seq module if not already loaded
            subprocess.run(['modprobe', 'snd-seq'], check=False)
            subprocess.run(['modprobe', 'snd-seq-midi'], check=False)
            subprocess.run(['modprobe', 'snd-rawmidi'], check=False)
            
            time.sleep(1)
            
            logger.info("ALSA sequencer modules loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load ALSA sequencer modules: {e}")
            return False
    
    def list_midi_ports(self):
        """List available ALSA MIDI ports"""
        try:
            result = subprocess.run(
                ['aconnect', '-l'],
                capture_output=True,
                text=True,
                check=False
            )
            
            logger.info("Available MIDI ports:")
            logger.info(result.stdout)
            return result.stdout
        except Exception as e:
            logger.error(f"Failed to list MIDI ports: {e}")
            return ""
    
    def setup_midi_routing(self):
        """Set up MIDI routing based on configuration"""
        routing_config = self.config.get('routing', [])
        
        for route in routing_config:
            source = route.get('source')
            destination = route.get('destination')
            
            if source and destination:
                try:
                    subprocess.run(
                        ['aconnect', source, destination],
                        check=True
                    )
                    logger.info(f"MIDI route established: {source} -> {destination}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to establish route {source} -> {destination}: {e}")
    
    def start_network_midi(self):
        """Start network MIDI server using aseqnet"""
        network_config = self.config.get('network_midi', {})
        
        if not network_config.get('enabled', False):
            logger.info("Network MIDI is disabled")
            return True
        
        port = network_config.get('port', 5004)
        
        try:
            # Start aseqnet in server mode
            subprocess.Popen(
                ['aseqnet', '-s', '-p', str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            logger.info(f"Network MIDI server started on port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start network MIDI server: {e}")
            return False
    
    def setup_gpio_buttons(self):
        """Set up GPIO buttons based on configuration"""
        gpio_config = self.config.get('gpio_buttons', [])
        
        for button_config in gpio_config:
            gpio_num = button_config.get('gpio')
            action = button_config.get('action')
            
            if gpio_num is not None:
                button = GPIOButton(gpio_num, lambda g: self.handle_button_press(g, action))
                
                if button.setup():
                    button.start_monitoring()
                    self.gpio_buttons.append(button)
                    logger.info(f"GPIO button {gpio_num} configured with action: {action}")
    
    def handle_button_press(self, gpio_num, action):
        """
        Handle button press events
        
        Args:
            gpio_num: GPIO number that was pressed
            action: Action to perform (from config)
        """
        logger.info(f"Button pressed on GPIO {gpio_num}, action: {action}")
        
        # Add custom button actions here
        if action == "toggle_routing":
            logger.info("Toggle routing action triggered")
            # Implement routing toggle logic
        elif action == "reconnect":
            logger.info("Reconnect action triggered")
            self.setup_midi_routing()
    
    def run(self):
        """Main run loop"""
        logger.info("=== MIDI Adapter for MilkV Duo S ===")
        
        # Load configuration
        if not self.load_config():
            logger.error("Failed to load configuration, exiting")
            return 1
        
        # Setup ALSA sequencer
        if not self.setup_alsa_sequencer():
            logger.error("Failed to setup ALSA sequencer")
            return 1
        
        time.sleep(2)
        
        # List available MIDI ports
        self.list_midi_ports()
        
        # Setup UART MIDI
        self.setup_uart_midi()
        
        # Setup Network MIDI
        self.start_network_midi()
        
        # Setup GPIO buttons
        self.setup_gpio_buttons()
        
        # Setup MIDI routing
        time.sleep(1)
        self.setup_midi_routing()
        
        logger.info("MIDI Adapter running... Press Ctrl+C to exit")
        
        # Keep running
        self.running = True
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        # Stop GPIO monitoring
        for button in self.gpio_buttons:
            button.stop()
        
        logger.info("Cleanup complete")


def main():
    """Main entry point"""
    config_path = "/root/midi-adapter/config.json"
    
    # Check if custom config path provided
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    adapter = MIDIAdapter(config_path)
    return adapter.run()


if __name__ == "__main__":
    sys.exit(main())
