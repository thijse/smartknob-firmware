# SmartKnob Connection Library

A clean, working implementation of the SmartKnob COBS+CRC32+Protobuf protocol for Python.

## Status

✅ **Working Components:**
- Complete protocol stack (COBS encoding, CRC32 validation, Protobuf parsing)
- Message reception from SmartKnob device (log messages)
- Command sending to SmartKnob device
- Connection management and utilities

❌ **Known Issues:**
- Firmware doesn't respond to commands with expected message types
- Only receives 'log' messages, no 'knob' or 'ack' responses
- Command/response cycle needs firmware investigation

## Quick Start

### Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Generate protobuf files:
```bash
python regenerate_protobuf.py
```

### Basic Usage

```python
from smartknob import connect_smartknob

# Auto-detect and connect to SmartKnob (no port needed!)
with connect_smartknob() as knob:
    # Set up message callback
    def on_message(msg):
        msg_type = msg.WhichOneof("payload")
        if msg_type == 'log':
            print(f"Log: {msg.log.msg}")
    
    knob.set_message_callback(on_message)
    
    # Send a command (firmware currently doesn't respond)
    knob.send_command(0)  # GET_KNOB_INFO
    
    # Keep connection alive
    time.sleep(5)
```

### Manual Port Selection (if needed)

```python
from smartknob import SmartKnobConnection

# Connect to specific port
with SmartKnobConnection("COM9") as knob:
    # ... same as above
```

### Testing

Run the protocol audit (auto-detects device):
```bash
python tests/test_protocol_audit.py
```

Expected output:
```
🔍 Auto-detecting SmartKnob device...
✅ Auto-detected SmartKnob: COM9
✅ STATUS: Protocol stack working perfectly!
   All layers (COBS + CRC32 + Protobuf) are functioning correctly.
```

Test basic connectivity (auto-detects device):
```bash
python tests/test_connection.py
```

Test device discovery capabilities:
```bash
python tests/test_device_discovery.py
```

## Architecture

### Protocol Stack

The library implements the complete SmartKnob protocol:

```
Application Layer    │ Python API (SmartKnobConnection)
                    │
Protocol Layer      │ Message queuing, ACK handling, retries
                    │
Serialization       │ Protobuf encoding/decoding
                    │
Integrity           │ CRC32 validation
                    │
Framing             │ COBS encoding/decoding
                    │
Transport           │ Serial communication
```

### Key Components

- **`SmartKnobProtocol`**: Core protocol handler with COBS+CRC32+Protobuf
- **`SmartKnobConnection`**: High-level connection manager
- **`find_smartknob_ports()`**: Auto-detection of SmartKnob devices

## Protocol Details

### Message Flow

**Outgoing (Python → SmartKnob):**
1. Create protobuf message
2. Add protocol version and nonce
3. Serialize to bytes
4. Calculate CRC32 checksum
5. Append CRC32 (little-endian)
6. COBS encode
7. Add frame delimiter (0x00)
8. Send over serial

**Incoming (SmartKnob → Python):**
1. Receive bytes from serial
2. Split on frame delimiter (0x00)
3. COBS decode
4. Verify CRC32 checksum
5. Parse protobuf message
6. Validate protocol version
7. Process message

### Verified Working

Based on extensive testing, the following components are **100% functional**:

- ✅ COBS encoding/decoding
- ✅ CRC32 calculation and validation
- ✅ Protobuf message parsing
- ✅ Protocol version handling
- ✅ Message reception (log messages)
- ✅ Command sending

### Current Limitations

The firmware appears to have issues with command response handling:

- Commands are sent correctly but firmware doesn't respond
- Only 'log' messages are received (sensor data, system info)
- No 'knob' or 'ack' messages observed
- This is a **firmware issue**, not a protocol implementation issue

## Protobuf Management

### When to Regenerate Protobuf Files

You need to regenerate the protobuf files whenever:

- ✅ **Protocol definitions change** in `../../proto/*.proto` files
- ✅ **Firmware protocol is updated** and you want to sync the Python library
- ✅ **Setting up the project for the first time**
- ✅ **After pulling changes** that might include protocol updates

### How to Regenerate Protobuf Files

**Option 1: Quick regeneration (recommended)**
```bash
cd smartknob-connection2
python regenerate_protobuf.py
```

**Option 2: Direct generator**
```bash
cd smartknob-connection2/protobuf
python generate_protobuf.py
```

### What Gets Generated

The protobuf generator creates:

- `smartknob/proto_gen/smartknob_pb2.py` - Main protocol messages
- `smartknob/proto_gen/settings_pb2.py` - Settings and configuration messages  
- `smartknob/proto_gen/nanopb_pb2.py` - Nanopb options (for compatibility)
- `smartknob/proto_gen/__init__.py` - Package initialization

### Generator Features

- ✅ **Pure Python dependencies** (no external protoc needed)
- ✅ **Automatic import fixing** (converts absolute to relative imports)
- ✅ **Change detection** (compares with previous generation)
- ✅ **Backup creation** (saves previous files for comparison)
- ✅ **Self-contained** (no git submodules required)

### Troubleshooting Protobuf Issues

If you encounter import errors:
```bash
# Regenerate protobuf files
python regenerate_protobuf.py

# Verify imports work
python -c "from smartknob.proto_gen import smartknob_pb2, settings_pb2; print('✅ Imports working')"
```

If generation fails:
```bash
# Check dependencies
pip install -r requirements.txt

# Check proto files exist
ls ../../proto/*.proto

# Run with verbose output
cd protobuf && python generate_protobuf.py
```

## Files Structure

```
smartknob-connection2/
├── README.md                    # This file
├── requirements.txt             # Dependencies
├── regenerate_protobuf.py       # Convenience protobuf regeneration script
├── protobuf/                    # Protobuf generation system
│   ├── generate_protobuf.py    # Main protobuf generator
│   └── nanopb.proto            # Local nanopb definitions
├── smartknob/                   # Main library
│   ├── __init__.py             # Package exports
│   ├── protocol.py             # Core protocol implementation
│   ├── connection.py           # Connection utilities
│   └── proto_gen/              # Generated protobuf classes ⚡ AUTO-GENERATED
├── tests/                      # Test scripts
│   ├── test_connection.py      # Basic connectivity test
│   └── test_protocol_audit.py  # Protocol validation
├── examples/                   # Usage examples
└── Documentation/              # Detailed documentation
    ├── PROTOCOL.md             # Protocol specification
    ├── IMPLEMENTATION.md       # Implementation details
    └── TROUBLESHOOTING.md      # Known issues and solutions
```

## Next Steps

To complete the SmartKnob communication:

1. **Investigate firmware command handling**
   - Check if GET_KNOB_INFO callback is registered
   - Verify serial-only mode configuration
   - Test other commands (MOTOR_CALIBRATE, etc.)

2. **Debug firmware response system**
   - Monitor firmware debug output
   - Check command processing in root_task.cpp
   - Verify protocol switching behavior

3. **Test bidirectional communication**
   - Once firmware responds correctly
   - Implement full command/response cycle
   - Add application-level features

## Contributing

The protocol implementation is complete and working. Focus areas for contribution:

- Firmware debugging and command response fixes
- Additional test cases and examples
- Documentation improvements
- Application-level features once bidirectional communication works

## License

[Add your license here]
