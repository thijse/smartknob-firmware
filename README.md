# SmartKnob Firmware with Python Backend Integration

A minimal, streamlined SmartKnob firmware designed for seamless Python backend communication and app development.

## Overview

This repository provides a simplified SmartKnob firmware focused on **serial communication with Python backends**. Unlike the original WiFi/MQTT-based implementations, this codebase eliminates networking complexity and provides a clean, direct communication channel between SmartKnob hardware and Python applications.

**Key Features:**
- **Serial-only communication** - No WiFi/MQTT overhead
- **Clean Python library** - Full protocol implementation with auto-detection
- **Simplified firmware** - Removed Home Assistant integration for minimal codebase
- **Direct app control** - Python backends can directly interact with SmartKnob apps
- **Comprehensive examples** - Ready-to-use Python examples and tests

## Quick Start

### 1. Flash the Firmware

Using PlatformIO in Visual Studio Code:

1. Open this project folder in VSCode with PlatformIO installed
2. Connect your SmartKnob via USB-C
3. Select the appropriate build environment for your hardware
4. Click "Upload and Monitor" in PlatformIO tasks

**Boot Mode:** If the device isn't detected, hold both BOOT and EN/RST buttons, then release EN/RST.

### 2. Python Backend Setup

```bash
cd smartknob-connection2
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
python regenerate_protobuf.py
```

### 3. Connect and Control

```python
from smartknob import connect_smartknob

# Auto-detect and connect (no port needed!)
with connect_smartknob() as knob:
    def on_message(msg):
        msg_type = msg.WhichOneof("payload")
        if msg_type == 'log':
            print(f"SmartKnob: {msg.log.msg}")
    
    knob.set_message_callback(on_message)
    knob.send_command(0)  # GET_KNOB_INFO
    
    # Your Python backend logic here
    time.sleep(5)
```

## Architecture

### Firmware (Serial-Only Mode)

The firmware has been streamlined to focus on core functionality:

- **Apps**: Climate, Blinds, Light Dimmer, Switch, Stopwatch
- **Communication**: Serial protocol with protobuf messages
- **No networking**: WiFi/MQTT code removed for simplicity
- **Conditional compilation**: `SERIAL_ONLY_MODE` flag controls features

### Python Library (`smartknob-connection2/`)

Complete protocol implementation with:

- **Auto-detection**: Finds SmartKnob devices automatically via USB VID/PID
- **Protocol stack**: COBS framing + CRC32 validation + Protobuf parsing
- **Connection management**: High-level API for easy integration
- **Comprehensive tests**: Protocol validation and device discovery tests

```
smartknob-connection2/
├── smartknob/              # Main library
│   ├── protocol.py         # Core COBS+CRC32+Protobuf implementation
│   ├── connection.py       # High-level connection management
│   └── proto_gen/          # Generated protobuf classes
├── tests/                  # Validation tests
├── examples/               # Usage examples
└── Documentation/          # Technical specifications
```

## Use Cases

This codebase is ideal for:

- **IoT backends** controlling SmartKnob interfaces
- **Home automation** systems with direct device communication
- **Prototyping** interactive applications with haptic feedback
- **Educational projects** learning embedded-Python communication
- **Custom applications** requiring precise knob control

## Hardware Compatibility

Based on the original SmartKnob design with support for:

- ESP32-S3 based controllers
- Various motor and sensor configurations
- USB serial communication
- Standard SmartKnob mechanical assembly

## Development

### Firmware Development

1. Use PlatformIO in VSCode
2. Modify apps in `firmware/src/apps/`
3. Serial communication handled automatically
4. Build and flash using PlatformIO tasks

### Python Development

1. Modify library in `smartknob-connection2/smartknob/`
2. Add examples in `examples/`
3. Run tests: `python tests/test_protocol_audit.py`
4. Regenerate protobuf if needed: `python regenerate_protobuf.py`

## Testing

Verify your setup:

```bash
# Test protocol implementation
python tests/test_protocol_audit.py

# Test device connectivity
python tests/test_connection.py

# Test auto-detection
python tests/test_device_discovery.py

# Monitor live data
python examples/basic_monitoring.py
```

## Documentation

- **[Protocol Specification](smartknob-connection2/Documentation/PROTOCOL.md)** - Technical protocol details
- **[Implementation Guide](smartknob-connection2/Documentation/IMPLEMENTATION.md)** - Library architecture
- **[Troubleshooting](smartknob-connection2/Documentation/TROUBLESHOOTING.md)** - Common issues and solutions

## Differences from Original

This fork focuses on **simplicity and Python integration**:

**Removed:**
- WiFi/MQTT networking stack
- Home Assistant integration
- Web interface dependencies
- Complex onboarding flows

**Added:**
- Serial-only communication mode
- Complete Python protocol library
- Auto-detection capabilities
- Comprehensive testing suite
- Clean examples and documentation

## Contributing

This project welcomes contributions focused on:

- Python library improvements
- Additional app examples
- Protocol enhancements
- Documentation updates
- Testing and validation

## License

This project maintains the open-source spirit of the original SmartKnob design. See [LICENSE](LICENSE.md) for details.

## Acknowledgments

Based on [ScottBez1's original SmartKnob](https://github.com/scottbez1/smartknob/) design and [SeedLabs' development kit](https://github.com/SeedLabs-it/smartknob-firmware). This fork focuses specifically on Python backend integration and simplified communication.
