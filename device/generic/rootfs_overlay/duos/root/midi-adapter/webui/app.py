#!/usr/bin/env python3
"""
MIDI Adapter Web GUI - Configuration Interface
A web-based configuration interface for the MIDI Adapter application.

This is a separate service from the main MIDI adapter application,
providing a user-friendly interface for configuration management.

Features:
- View and edit device configurations
- Manage routing profiles
- Reload configuration without restart
- Real-time status monitoring
- Configuration validation

Port: 8080 (HTTP)
"""

import json
import os
import sys
import subprocess
import logging
import signal
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('midi-webui')

# Configuration
CONFIG_FILE = '/root/midi-adapter/config.json'
PIDFILE = '/var/run/midi-adapter.pid'
LOG_FILE = '/var/log/midi-adapter.log'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'midi-adapter-secret-key-change-in-production'


def load_config():
    """Load configuration from JSON file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None


def save_config(config):
    """Save configuration to JSON file"""
    try:
        # Validate JSON structure
        json_str = json.dumps(config, indent=2)
        
        # Create backup
        backup_file = f"{CONFIG_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(CONFIG_FILE):
            subprocess.run(['cp', CONFIG_FILE, backup_file], check=True)
        
        # Write new config
        with open(CONFIG_FILE, 'w') as f:
            f.write(json_str)
        
        logger.info(f"Configuration saved successfully (backup: {backup_file})")
        return True
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        return False


def get_service_status():
    """Get status of MIDI adapter service"""
    try:
        result = subprocess.run(['/etc/init.d/S98midi-adapter', 'status'],
                                capture_output=True, text=True, timeout=5)
        return {
            'running': 'running' in result.stdout.lower(),
            'message': result.stdout.strip()
        }
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return {'running': False, 'message': f'Error: {str(e)}'}


def reload_service():
    """Reload MIDI adapter service configuration"""
    try:
        # Send HUP signal to reload
        if os.path.exists(PIDFILE):
            with open(PIDFILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGHUP)
            return True, "Configuration reload signal sent"
        else:
            return False, "Service is not running"
    except Exception as e:
        logger.error(f"Failed to reload service: {e}")
        return False, str(e)


def restart_service():
    """Restart MIDI adapter service"""
    try:
        result = subprocess.run(['/etc/init.d/S98midi-adapter', 'restart'],
                                capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        logger.error(f"Failed to restart service: {e}")
        return False, str(e)


@app.route('/')
def index():
    """Main page - configuration interface"""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """API: Get current configuration"""
    config = load_config()
    if config:
        return jsonify({'success': True, 'config': config})
    else:
        return jsonify({'success': False, 'error': 'Failed to load configuration'}), 500


@app.route('/api/config', methods=['POST'])
def update_config():
    """API: Update configuration"""
    try:
        new_config = request.json
        
        # Validate required sections
        required_sections = ['devices', 'routing_profiles', 'settings']
        for section in required_sections:
            if section not in new_config:
                return jsonify({
                    'success': False,
                    'error': f'Missing required section: {section}'
                }), 400
        
        # Save configuration
        if save_config(new_config):
            return jsonify({
                'success': True,
                'message': 'Configuration saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save configuration'
            }), 500
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """API: Get service status"""
    status = get_service_status()
    return jsonify({'success': True, 'status': status})


@app.route('/api/reload', methods=['POST'])
def reload_config():
    """API: Reload configuration without restart"""
    success, message = reload_service()
    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/restart', methods=['POST'])
def restart():
    """API: Restart MIDI adapter service"""
    success, message = restart_service()
    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """API: Get recent log entries"""
    try:
        lines = int(request.args.get('lines', 100))
        if os.path.exists(LOG_FILE):
            result = subprocess.run(['tail', '-n', str(lines), LOG_FILE],
                                    capture_output=True, text=True, timeout=5)
            return jsonify({
                'success': True,
                'logs': result.stdout
            })
        else:
            return jsonify({
                'success': True,
                'logs': 'Log file not found'
            })
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/validate', methods=['POST'])
def validate_config():
    """API: Validate configuration JSON"""
    try:
        config = request.json
        
        # Validate JSON structure
        if not isinstance(config, dict):
            return jsonify({
                'success': False,
                'error': 'Configuration must be a JSON object'
            }), 400
        
        # Check required sections
        required_sections = ['devices', 'routing_profiles', 'settings']
        errors = []
        
        for section in required_sections:
            if section not in config:
                errors.append(f'Missing required section: {section}')
        
        # Validate devices section
        if 'devices' in config and not isinstance(config['devices'], dict):
            errors.append('devices section must be an object')
        
        # Validate routing_profiles section
        if 'routing_profiles' in config and not isinstance(config['routing_profiles'], dict):
            errors.append('routing_profiles section must be an object')
        
        # Validate settings section
        if 'settings' in config and not isinstance(config['settings'], dict):
            errors.append('settings section must be an object')
        
        if errors:
            return jsonify({
                'success': False,
                'errors': errors
            }), 400
        else:
            return jsonify({
                'success': True,
                'message': 'Configuration is valid'
            })
    except Exception as e:
        logger.error(f"Failed to validate config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting MIDI Adapter Web GUI on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
