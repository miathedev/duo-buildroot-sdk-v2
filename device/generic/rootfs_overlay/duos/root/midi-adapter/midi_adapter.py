#!/usr/bin/env python3
"""
MIDI Adapter for MilkV Duo S - Universal Device Configuration
Configurable adapter supporting multiple device types and routing profiles:
- USB MIDI + GPIO Buttons -> DIN MIDI (UART)
- USB MIDI + GPIO Buttons -> Network MIDI (Ethernet)
- OSC MIDI bridge support (experimental)

Version 2.0 - Universal device-based configuration
"""

import json
import os
import sys
import time
import subprocess
import threading
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('midi-adapter')


class Device:
    """Base class for all device types"""
    
    def __init__(self, device_id: str, config: Dict):
        self.device_id = device_id
        self.config = config
        self.enabled = config.get('enabled', False)
        self.alias = config.get('alias', device_id)
        self.device_type = config.get('type', 'unknown')
        
    def setup(self) -> bool:
        """Setup the device (override in subclasses)"""
        return True
    
    def cleanup(self):
        """Cleanup device resources (override in subclasses)"""
        pass


class UARTMIDIDevice(Device):
    """UART MIDI device (DIN MIDI)"""
    
    def __init__(self, device_id: str, config: Dict):
        super().__init__(device_id, config)
        self.uart_device = config.get('device', '/dev/ttyS4')
        self.baudrate = config.get('baudrate', 31250)
        self.direction = config.get('direction', 'output')  # input, output, or both
        self.alsa_port = None
        
    def setup(self) -> bool:
        """Configure UART for MIDI"""
        if not self.enabled:
            logger.info(f"UART MIDI device '{self.alias}' is disabled")
            return True
        
        try:
            # Configure UART with specified baudrate
            subprocess.run([
                'stty', '-F', self.uart_device,
                str(self.baudrate), 'raw', '-echo', '-echoe', '-echok'
            ], check=True)
            
            direction_str = self.direction if self.direction in ['input', 'output', 'both'] else 'output'
            logger.info(f"UART device '{self.alias}' configured: {self.uart_device} @ {self.baudrate} baud, direction={direction_str}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure UART device '{self.alias}': {e}")
            return False
    
    def get_alsa_port(self) -> Optional[str]:
        """Get ALSA port for this UART device
        
        Note: Automatic port discovery not yet implemented.
        Users should use ALSA port numbers directly in routing config.
        
        Returns:
            ALSA port string or None
        """
        # TODO: Implement dynamic ALSA port discovery for UART MIDI devices
        # This would involve parsing aconnect output to find the hardware
        # MIDI port associated with this UART device
        return self.alsa_port


class NetworkMIDIDevice(Device):
    """Network MIDI device (RTP-MIDI)"""
    
    def __init__(self, device_id: str, config: Dict):
        super().__init__(device_id, config)
        self.target_ip = config.get('target_ip', '')
        self.port = config.get('port', 5004)
        self.multicast = config.get('multicast', False)
        self.direction = config.get('direction', 'both')  # input, output, or both
        self.process = None
        self.alsa_port = None
        
    def setup(self) -> bool:
        """Start network MIDI server or client"""
        if not self.enabled:
            logger.info(f"Network MIDI device '{self.alias}' is disabled")
            return True
        
        try:
            # Start aseqnet in server mode (empty target_ip) or client mode
            if self.target_ip:
                # Client mode - connect to specific IP
                cmd = ['aseqnet', '-p', str(self.port), self.target_ip]
                mode_str = "client"
                logger.info(f"Network MIDI '{self.alias}' connecting to {self.target_ip}:{self.port}, direction={self.direction}")
            else:
                # Server mode - listen for connections
                cmd = ['aseqnet', '-s', '-p', str(self.port)]
                mode_str = "server"
                logger.info(f"Network MIDI '{self.alias}' server started on port {self.port}, direction={self.direction}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(1)  # Give aseqnet time to create ALSA port
            return True
        except Exception as e:
            logger.error(f"Failed to start network MIDI '{self.alias}': {e}")
            return False
    
    def cleanup(self):
        """Stop network MIDI process"""
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                    logger.info(f"Network MIDI '{self.alias}' stopped")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Network MIDI '{self.alias}' did not terminate gracefully, forcing kill")
                    self.process.kill()
                    self.process.wait()
            except Exception as e:
                logger.error(f"Error stopping network MIDI '{self.alias}': {e}")
    
    def get_alsa_port(self) -> Optional[str]:
        """Get ALSA port for this network device
        
        Note: Automatic port discovery not yet implemented.
        Users should use ALSA port numbers directly in routing config.
        
        Returns:
            ALSA port string or None
        """
        # TODO: Implement dynamic ALSA port discovery for aseqnet
        # This would involve parsing aconnect output to find the client
        # port created by the aseqnet process
        return self.alsa_port


class GPIOInputDevice(Device):
    """GPIO input device (buttons, pedals, etc.)"""
    
    def __init__(self, device_id: str, config: Dict):
        super().__init__(device_id, config)
        self.gpio_num = config.get('gpio')
        self.pull = config.get('pull', 'up')
        self.trigger = config.get('trigger', 'falling')
        self.debounce_ms = config.get('debounce_ms', 50)
        self.action = config.get('action', '')
        self.target = config.get('target', 'all')
        self.gpio_path = f"/sys/class/gpio/gpio{self.gpio_num}"
        self.running = False
        self.thread = None
        self.callback = None
        
    def setup(self) -> bool:
        """Setup GPIO as input"""
        if not self.enabled or self.gpio_num is None:
            logger.info(f"GPIO device '{self.alias}' is disabled or has no GPIO number")
            return True
        
        try:
            # Export GPIO if not already exported
            if not os.path.exists(self.gpio_path):
                with open("/sys/class/gpio/export", "w") as f:
                    f.write(str(self.gpio_num))
                time.sleep(0.1)
            
            # Set direction to input
            with open(f"{self.gpio_path}/direction", "w") as f:
                f.write("in")
            
            # Note: GPIO pull-up/pull-down configuration is typically done via
            # device tree or hardware configuration. The 'pull' parameter in config
            # documents the expected hardware configuration.
            
            # Set edge detection based on trigger configuration
            edge_map = {
                'falling': 'falling',
                'rising': 'rising',
                'both': 'both'
            }
            edge = edge_map.get(self.trigger, 'falling')
            
            with open(f"{self.gpio_path}/edge", "w") as f:
                f.write(edge)
                
            logger.info(f"GPIO device '{self.alias}' configured: GPIO{self.gpio_num}, trigger={self.trigger} (pull={self.pull} expected in hardware)")
            return True
        except Exception as e:
            logger.error(f"Failed to setup GPIO device '{self.alias}': {e}")
            return False
    
    def start_monitoring(self, callback):
        """Start monitoring GPIO in a separate thread"""
        self.callback = callback
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started monitoring GPIO device '{self.alias}'")
    
    def _monitor_loop(self):
        """Monitor GPIO value changes with debouncing"""
        last_value = "1" if self.pull == "up" else "0"
        last_trigger_time = 0
        debounce_sec = self.debounce_ms / 1000.0
        
        while self.running:
            try:
                with open(f"{self.gpio_path}/value", "r") as f:
                    value = f.read().strip()
                
                current_time = time.time()
                
                # Check for trigger condition
                triggered = False
                if self.trigger == 'falling' and last_value == "1" and value == "0":
                    triggered = True
                elif self.trigger == 'rising' and last_value == "0" and value == "1":
                    triggered = True
                elif self.trigger == 'both' and last_value != value:
                    triggered = True
                
                # Apply debouncing
                if triggered and (current_time - last_trigger_time) >= debounce_sec:
                    logger.info(f"GPIO trigger on '{self.alias}' (GPIO {self.gpio_num})")
                    if self.callback:
                        self.callback(self.device_id, self.action, self.target)
                    last_trigger_time = current_time
                
                last_value = value
                time.sleep(0.01)  # 10ms polling for responsiveness
                
            except Exception as e:
                logger.error(f"Error monitoring GPIO '{self.alias}': {e}")
                time.sleep(1)
    
    def cleanup(self):
        """Stop monitoring GPIO"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


class OSCMIDIDevice(Device):
    """OSC to MIDI bridge (experimental)"""
    
    def __init__(self, device_id: str, config: Dict):
        super().__init__(device_id, config)
        self.target_ip = config.get('target_ip', '127.0.0.1')
        self.target_port = config.get('target_port', 8000)
        self.listen_port = config.get('listen_port', 9000)
        self.direction = config.get('direction', 'both')  # input, output, or both
        
    def setup(self) -> bool:
        """Setup OSC MIDI bridge"""
        if not self.enabled:
            logger.info(f"OSC MIDI device '{self.alias}' is disabled")
            return True
        
        logger.warning(f"OSC MIDI device '{self.alias}' is experimental and requires python-osc package")
        logger.info(f"OSC MIDI '{self.alias}': target={self.target_ip}:{self.target_port}, listen={self.listen_port}, direction={self.direction}")
        # OSC implementation would require python-osc library
        # Not implemented in this version
        return True


class USBMIDIDevice(Device):
    """USB MIDI device (external USB MIDI controller/keyboard)"""
    
    def __init__(self, device_id: str, config: Dict):
        super().__init__(device_id, config)
        self.port_pattern = config.get('port_pattern', '')
        self.alsa_port = None
        
    def setup(self) -> bool:
        """Setup USB MIDI device"""
        if not self.enabled:
            logger.info(f"USB MIDI device '{self.alias}' is disabled")
            return True
        
        logger.info(f"USB MIDI device '{self.alias}' configured (auto-discovered)")
        logger.info(f"  Pattern: {self.port_pattern if self.port_pattern else 'any USB MIDI device'}")
        # USB MIDI devices are automatically handled by the kernel
        # The ALSA port will be auto-discovered when the device is connected
        return True
    
    def get_alsa_port(self) -> Optional[str]:
        """Get ALSA port for this USB MIDI device
        
        Note: Auto-discovery not yet implemented.
        Users should use explicit ALSA port numbers in routing if needed,
        or this can be enhanced to parse aconnect output.
        
        Returns:
            ALSA port string or None
        """
        # TODO: Implement dynamic ALSA port discovery for USB MIDI devices
        # This would involve parsing aconnect output to find USB MIDI ports
        # matching the port_pattern (if specified)
        return self.alsa_port


class MIDIAdapter:
    """Main MIDI adapter with universal device configuration"""
    
    def __init__(self, config_path="/root/midi-adapter/config.json"):
        """Initialize MIDI adapter"""
        self.config_path = config_path
        self.config = {}
        self.devices: Dict[str, Device] = {}
        self.device_ports: Dict[str, str] = {}  # alias -> ALSA port mapping
        self.routing_profiles = {}
        self.active_profile = None
        self.running = False
        
    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Set log level from config
            log_level = self.config.get('settings', {}).get('log_level', 'INFO')
            logger.setLevel(getattr(logging, log_level, logging.INFO))
            
            logger.info(f"Configuration loaded from {self.config_path}")
            logger.info(f"Config version: {self.config.get('version', '1.0')}")
            return True
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return False
    
    def setup_devices(self) -> bool:
        """Setup all configured devices"""
        devices_config = self.config.get('devices', {})
        
        if not devices_config:
            logger.warning("No devices configured")
            return True
        
        device_type_map = {
            'uart_midi': UARTMIDIDevice,
            'network_midi_rtp': NetworkMIDIDevice,
            'gpio_input': GPIOInputDevice,
            'osc_midi': OSCMIDIDevice,
            'usb_midi': USBMIDIDevice
        }
        
        for device_id, device_config in devices_config.items():
            device_type = device_config.get('type')
            
            if device_type not in device_type_map:
                logger.warning(f"Unknown device type '{device_type}' for device '{device_id}'")
                continue
            
            # Create device instance
            device_class = device_type_map[device_type]
            device = device_class(device_id, device_config)
            
            # Setup device
            if device.setup():
                self.devices[device_id] = device
                logger.info(f"Device '{device.alias}' ({device_type}) initialized")
            else:
                logger.error(f"Failed to initialize device '{device_id}'")
        
        return len(self.devices) > 0
    
    def setup_alsa_sequencer(self) -> bool:
        """Set up ALSA sequencer and load kernel modules"""
        try:
            subprocess.run(['modprobe', 'snd-seq'], check=False)
            subprocess.run(['modprobe', 'snd-seq-midi'], check=False)
            subprocess.run(['modprobe', 'snd-rawmidi'], check=False)
            
            time.sleep(1)
            logger.info("ALSA sequencer modules loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load ALSA sequencer modules: {e}")
            return False
    
    def discover_alsa_ports(self):
        """Discover ALSA MIDI ports and map device aliases
        
        Note: Automatic ALSA port discovery for device aliases is not yet implemented.
        Users should use ALSA port numbers (e.g., "14:0") in routing configuration.
        Device aliases will be resolved if the device's get_alsa_port() method is implemented.
        
        Future enhancement: Parse aconnect output to automatically map device names to ports.
        """
        try:
            result = subprocess.run(
                ['aconnect', '-l'],
                capture_output=True,
                text=True,
                check=False
            )
            
            logger.info("Available ALSA MIDI ports:")
            logger.info(result.stdout)
            
            # TODO: Implement automatic port discovery
            # Parse aconnect output to map device names/aliases to ALSA port numbers
            # Example parsing:
            # - Look for "client 14: 'USB MIDI Device'" to extract port "14:0"
            # - Look for aseqnet process ports for network MIDI devices
            # - Store mappings in self.device_ports for use in resolve_port()
            
            return result.stdout
        except Exception as e:
            logger.error(f"Failed to list MIDI ports: {e}")
            return ""
    
    def resolve_port(self, port_ref: str) -> Optional[str]:
        """Resolve port reference to ALSA port number
        
        Args:
            port_ref: Can be ALSA port (14:0) or device alias (din_midi)
        
        Returns:
            ALSA port string or None
        """
        # Check if it's already an ALSA port format (number:number)
        if ':' in port_ref:
            parts = port_ref.split(':')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return port_ref
        
        # Check if it's a device alias
        if port_ref in self.device_ports:
            return self.device_ports[port_ref]
        
        # Check if it's a device ID
        if port_ref in self.devices:
            device = self.devices[port_ref]
            if hasattr(device, 'get_alsa_port'):
                alsa_port = device.get_alsa_port()
                if alsa_port:
                    return alsa_port
        
        logger.warning(f"Could not resolve port reference: {port_ref}")
        return port_ref  # Return as-is and let aconnect handle it
    
    def setup_routing_profile(self, profile_name: str) -> bool:
        """Setup MIDI routing for a specific profile"""
        profiles = self.config.get('routing_profiles', {})
        
        if profile_name not in profiles:
            logger.error(f"Routing profile '{profile_name}' not found")
            return False
        
        profile = profiles[profile_name]
        
        if not profile.get('enabled', False):
            logger.info(f"Routing profile '{profile_name}' is disabled")
            return True
        
        logger.info(f"Setting up routing profile: {profile_name}")
        logger.info(f"  Description: {profile.get('description', 'N/A')}")
        
        routes = profile.get('routes', [])
        success_count = 0
        
        for route in routes:
            if not route.get('enabled', True):
                continue
            
            source = route.get('source')
            destination = route.get('destination')
            
            if not source or not destination:
                logger.warning(f"Invalid route in profile '{profile_name}': missing source or destination")
                continue
            
            # Resolve source and destination to ALSA ports
            source_port = self.resolve_port(source)
            dest_port = self.resolve_port(destination)
            
            if source_port and dest_port:
                try:
                    subprocess.run(
                        ['aconnect', source_port, dest_port],
                        check=True,
                        capture_output=True
                    )
                    logger.info(f"  Route: {source} ({source_port}) -> {destination} ({dest_port})")
                    success_count += 1
                except subprocess.CalledProcessError as e:
                    logger.warning(f"  Failed to establish route {source} -> {destination}: {e}")
        
        logger.info(f"Routing profile '{profile_name}' setup complete: {success_count}/{len(routes)} routes established")
        return success_count > 0
    
    def setup_gpio_monitoring(self):
        """Start monitoring GPIO input devices"""
        for device_id, device in self.devices.items():
            if isinstance(device, GPIOInputDevice) and device.enabled:
                device.start_monitoring(self.handle_gpio_event)
    
    def handle_gpio_event(self, device_id: str, action: str, target: str):
        """Handle GPIO button/pedal events"""
        logger.info(f"GPIO event from '{device_id}': action={action}, target={target}")
        
        if action == "toggle_routing":
            logger.info("Toggle routing action triggered")
            # Implement routing toggle logic here
            # Could toggle between profiles or enable/disable routes
            
        elif action == "reconnect":
            logger.info("Reconnect action triggered")
            # Re-establish all MIDI connections
            if self.active_profile:
                self.setup_routing_profile(self.active_profile)
                
        elif action == "switch_profile":
            logger.info("Profile switch action triggered")
            # Switch to next profile or specific profile
            
        else:
            logger.info(f"Custom action '{action}' triggered (not implemented)")
    
    def run(self) -> int:
        """Main run loop"""
        logger.info("=" * 50)
        logger.info("MIDI Adapter for MilkV Duo S - v2.0")
        logger.info("Universal Device Configuration")
        logger.info("=" * 50)
        
        # Load configuration
        if not self.load_config():
            logger.error("Failed to load configuration, exiting")
            return 1
        
        # Setup ALSA sequencer
        if not self.setup_alsa_sequencer():
            logger.error("Failed to setup ALSA sequencer")
            return 1
        
        time.sleep(2)
        
        # Discover ALSA ports
        self.discover_alsa_ports()
        
        # Setup devices
        if not self.setup_devices():
            logger.error("Failed to setup devices")
            return 1
        
        # Get active profile from settings
        settings = self.config.get('settings', {})
        self.active_profile = settings.get('active_profile', 'default')
        auto_connect = settings.get('auto_connect', True)
        
        # Setup GPIO monitoring
        self.setup_gpio_monitoring()
        
        # Setup routing if auto_connect is enabled
        if auto_connect:
            time.sleep(1)
            self.setup_routing_profile(self.active_profile)
        else:
            logger.info("Auto-connect is disabled, skipping routing setup")
        
        logger.info("=" * 50)
        logger.info("MIDI Adapter is running... Press Ctrl+C to exit")
        logger.info("=" * 50)
        
        # Keep running
        self.running = True
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nShutting down...")
            self.cleanup()
        
        return 0
    
    def cleanup(self):
        """Clean up all resources"""
        self.running = False
        
        # Cleanup all devices
        for device in self.devices.values():
            device.cleanup()
        
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
