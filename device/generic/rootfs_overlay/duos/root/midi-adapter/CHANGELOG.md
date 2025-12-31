# CHANGELOG - MIDI Adapter for MilkV Duo S

All notable changes to this project are documented in this file.

## [v2.1.0] - 2024-12-31

### 🚀 Major Features Added

#### Web-Based Configuration GUI
- **Complete web interface** for MIDI adapter configuration
  - Flask-based web server running on port 8080
  - Modern, responsive UI with real-time status monitoring
  - JSON editor with syntax highlighting and validation
  - Visual device overview showing all configured devices
  - Log viewer for troubleshooting and monitoring
  
- **Configuration Management**
  - Load and edit configuration through web interface
  - JSON validation before saving
  - Automatic backup creation on config changes
  - Hot-reload configuration without service restart
  - Download/upload configuration files
  
- **Service Control**
  - Real-time service status monitoring (updates every 5 seconds)
  - Reload button for hot-reloading configuration
  - Restart button for full service restart
  - View application logs in real-time
  
#### Separated Service Architecture
- **Main Application Service** (`S98midi-adapter`)
  - Handles all MIDI routing logic
  - GPIO button management
  - Device configuration and management
  - Independent operation without web GUI
  - PID file: `/var/run/midi-adapter.pid`
  - Log file: `/var/log/midi-adapter.log`
  
- **Web GUI Service** (`S99midi-webui`)
  - Separate Flask application
  - Configuration interface only
  - No impact on main MIDI routing
  - Can be started/stopped independently
  - PID file: `/var/run/midi-webui.pid`
  - Log file: `/var/log/midi-webui.log`

### 🔧 Technical Improvements

#### Service Management
- **SIGHUP Signal Handling**
  - Main application now responds to SIGHUP for config reload
  - Hot-reload without interrupting active MIDI connections
  - Graceful cleanup and reinitialization of devices
  
- **Enhanced Init Scripts**
  - Added `reload` command to main service init script
  - Improved error handling and status reporting
  - Better logging configuration
  - Proper PID file management

#### Buildroot Configuration
- **Added Flask and Dependencies**
  - `BR2_PACKAGE_PYTHON_FLASK=y` - Flask web framework
  - `BR2_PACKAGE_PYTHON_JINJA2=y` - Template engine
  - `BR2_PACKAGE_PYTHON_WERKZEUG=y` - WSGI utilities
  - `BR2_PACKAGE_PYTHON_CLICK=y` - CLI framework
  - `BR2_PACKAGE_PYTHON_ITSDANGEROUS=y` - Security utilities

### 📚 Documentation Updates

#### New Documentation
- **CHANGELOG.md** (this file)
  - Comprehensive change history
  - Detailed feature descriptions
  - Migration notes

- **WEB_GUI_README.md**
  - Web GUI setup and usage guide
  - API documentation
  - Troubleshooting guide
  - Screenshots and examples

#### Updated Documentation
- **README.md**
  - Added web GUI section
  - Updated service architecture documentation
  - Added port information (8080 for web UI)
  - Updated build instructions

### 🎯 Why These Changes?

#### Separation of Concerns
The separation of the web UI from the main application provides several benefits:

1. **Reliability**: Main MIDI routing continues even if web UI crashes
2. **Security**: Web UI can be disabled in production environments
3. **Performance**: No web server overhead when GUI is not needed
4. **Maintainability**: Easier to update UI without touching core logic
5. **Flexibility**: Can run main app on headless systems without web dependencies

#### Hot-Reload Capability
The SIGHUP signal handling enables configuration changes without service interruption:

1. **No Downtime**: MIDI routing continues during config reload
2. **Faster Iteration**: Test configuration changes immediately
3. **Better UX**: Web GUI reload button provides instant feedback
4. **Production-Friendly**: Update routing without affecting live performances

#### Web-Based Configuration
The web GUI addresses several user pain points:

1. **Accessibility**: Configure from any device with a web browser
2. **User-Friendly**: No need to manually edit JSON files
3. **Validation**: Real-time feedback on configuration errors
4. **Visibility**: See service status and logs in one place
5. **Safety**: Automatic backups prevent configuration loss

### 🔄 Migration from v2.0 to v2.1

#### Service Names Changed
- Old: `/etc/init.d/S99midi-adapter`
- New: `/etc/init.d/S98midi-adapter` (main app)
- New: `/etc/init.d/S99midi-webui` (web GUI)

#### Starting Services
```bash
# Start main MIDI adapter
/etc/init.d/S98midi-adapter start

# Start web GUI (optional)
/etc/init.d/S99midi-webui start

# Check status
/etc/init.d/S98midi-adapter status
/etc/init.d/S99midi-webui status
```

#### Reloading Configuration
```bash
# Hot-reload (preferred, no downtime)
/etc/init.d/S98midi-adapter reload

# Full restart (if hot-reload fails)
/etc/init.d/S98midi-adapter restart
```

#### Accessing Web GUI
1. Ensure web GUI service is running
2. Open browser to `http://<device-ip>:8080`
3. Default credentials: None (open access on port 8080)

**Security Note**: The web GUI runs without authentication. In production:
- Use firewall rules to restrict access
- Or disable web GUI service entirely
- Or implement authentication (requires custom modifications)

### 📝 Configuration Compatibility

#### Backward Compatible
All v2.0 configuration files work without modification in v2.1:
- Same JSON structure
- Same device types
- Same routing profiles
- No breaking changes

#### New Features Available
Web GUI adds new capabilities without changing config format:
- Visual editing (optional)
- Real-time validation
- Automatic backups
- Service control

### 🐛 Bug Fixes

- Fixed PID file handling in init scripts
- Improved error messages in web GUI API
- Enhanced logging configuration
- Better process cleanup on service stop

### 🔮 Future Enhancements

Potential features for v2.2:
- Authentication for web GUI
- HTTPS support
- Configuration templates
- Device auto-discovery wizard
- MIDI message logger in web GUI
- Performance metrics dashboard
- Mobile-optimized UI

---

## [v2.0.0] - 2024-12-25

### Initial Release Features
- Universal device-based configuration
- USB MIDI, DIN MIDI (UART), Network MIDI (RTP) support
- GPIO button controls
- Multiple routing profiles
- Direction control (input/output/both)
- MIDI debugging with `debug_midi` flag
- GitLab CI/CD pipeline
- Comprehensive documentation

---

## Development

### Contributing
When adding features:
1. Update this CHANGELOG with clear descriptions
2. Document WHY changes were made, not just WHAT
3. Include migration notes for breaking changes
4. Update all relevant documentation
5. Test on actual hardware before committing

### Versioning
- **v2.x.x**: Major version for significant architecture changes
- **v2.x.x**: Minor version for new features
- **v2.x.x**: Patch version for bug fixes

### Documentation Standards
- Always explain WHY alongside WHAT
- Include examples and use cases
- Provide migration paths for changes
- Update all affected documentation files
- Keep CHANGELOG up to date
