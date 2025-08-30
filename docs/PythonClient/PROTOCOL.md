# SmartKnob Protocol Specification

This document describes the complete SmartKnob communication protocol as implemented and verified through extensive testing.

## Protocol Overview

The SmartKnob uses a layered protocol stack for reliable serial communication:

```
┌─────────────────────────────────────────────────────────────┐
│ Application Layer: Commands, Responses, Log Messages       │
├─────────────────────────────────────────────────────────────┤
│ Serialization: Protocol Buffers (protobuf)                 │
├─────────────────────────────────────────────────────────────┤
│ Integrity: CRC32 Checksum (little-endian)                  │
├─────────────────────────────────────────────────────────────┤
│ Framing: COBS (Consistent Overhead Byte Stuffing)          │
├─────────────────────────────────────────────────────────────┤
│ Transport: Serial Communication (921600 baud, 8N1)         │
└─────────────────────────────────────────────────────────────┘
```

## Protocol Layers

### 1. Transport Layer

**Serial Configuration:**
- Baud rate: 921600
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

**Mode Switching:**
- Send ASCII 'q' character to switch from plaintext to protobuf mode
- Device acknowledges switch by beginning to send protobuf frames

### 2. Framing Layer (COBS)

**Purpose:** Provides reliable frame boundaries using null bytes (0x00) as delimiters.

**COBS Encoding Process:**
1. Take payload + CRC32 packet
2. Apply COBS encoding (eliminates all 0x00 bytes)
3. Append 0x00 delimiter

**COBS Decoding Process:**
1. Split incoming data on 0x00 delimiters
2. Apply COBS decoding to each frame
3. Result is payload + CRC32 packet

**Status:** ✅ **100% Working** - All frames decode successfully

### 3. Integrity Layer (CRC32)

**Purpose:** Ensures data integrity with checksum validation.

**CRC32 Details:**
- Algorithm: Standard CRC32 (polynomial 0xEDB88320)
- Initial value: 0
- Byte order: Little-endian
- Position: Appended to protobuf payload (last 4 bytes)

**Calculation:**
```python
import zlib
crc = zlib.crc32(payload) & 0xFFFFFFFF
packet = payload + struct.pack('<I', crc)
```

**Status:** ✅ **100% Working** - All checksums validate correctly

### 4. Serialization Layer (Protobuf)

**Purpose:** Structured message serialization using Protocol Buffers.

**Protocol Version:** 1 (validated in all messages)

**Message Types:**

**Outgoing (Host → Device):**
```protobuf
message ToSmartknob {
  uint32 protocol_version = 1;
  uint32 nonce = 2;
  oneof payload {
    RequestState request_state = 3;
    SmartKnobConfig smartknob_config = 4;
    SmartKnobCommand smartknob_command = 5;
    StrainCalibration strain_calibration = 6;
    Settings settings = 7;
  }
}
```

**Incoming (Device → Host):**
```protobuf
message FromSmartKnob {
  uint32 protocol_version = 1;
  oneof payload {
    Knob knob = 3;
    Ack ack = 4;
    Log log = 5;
    SmartKnobState smartknob_state = 6;
    MotorCalibState motor_calib_state = 7;
    StrainCalibState strain_calib_state = 8;
  }
}
```

**Status:** ✅ **100% Working** - All protobuf parsing succeeds

### 5. Application Layer

**Commands:**
```protobuf
enum SmartKnobCommand {
  GET_KNOB_INFO = 0;
  MOTOR_CALIBRATE = 1;
  STRAIN_CALIBRATE = 2;
}
```

**Message Flow:**
- Host sends commands with unique nonce
- Device should respond with ACK + requested data
- Log messages sent continuously by device

**Status:** 
- ✅ Command sending: Works correctly
- ❌ Command responses: Firmware doesn't respond

## Complete Message Flow

### Outgoing Message (Host → Device)

```
1. Create ToSmartknob protobuf message
   ├─ Set protocol_version = 1
   ├─ Set unique nonce
   └─ Set command/config payload

2. Serialize protobuf → bytes
   └─ payload = message.SerializeToString()

3. Calculate CRC32
   ├─ crc = zlib.crc32(payload) & 0xFFFFFFFF
   └─ packet = payload + struct.pack('<I', crc)

4. COBS encode
   └─ encoded = cobs.encode(packet)

5. Add frame delimiter
   └─ frame = encoded + b'\x00'

6. Send over serial
   └─ serial.write(frame)
```

### Incoming Message (Device → Host)

```
1. Receive bytes from serial
   └─ Accumulate in buffer

2. Split on frame delimiter
   └─ frames = buffer.split(b'\x00')

3. COBS decode each frame
   └─ packet = cobs.decode(frame)

4. Verify CRC32
   ├─ payload = packet[:-4]
   ├─ received_crc = struct.unpack('<I', packet[-4:])[0]
   ├─ calculated_crc = zlib.crc32(payload) & 0xFFFFFFFF
   └─ assert received_crc == calculated_crc

5. Parse protobuf
   ├─ message = FromSmartKnob()
   ├─ message.ParseFromString(payload)
   └─ assert message.protocol_version == 1

6. Process message
   └─ Handle based on message.WhichOneof("payload")
```

## Verified Protocol Behavior

Based on extensive testing with protocol audit tools:

### Working Components ✅

1. **COBS Encoding/Decoding**: 100% success rate
   - All frames decode without errors
   - Frame boundaries correctly identified
   - No data corruption observed

2. **CRC32 Validation**: 100% success rate
   - All checksums validate correctly
   - No integrity errors detected
   - Proper little-endian byte order

3. **Protobuf Parsing**: 100% success rate
   - All messages parse successfully
   - Protocol version consistently = 1
   - Message structure matches specification

4. **Message Reception**: Continuous log messages
   - ~4-5 messages per second
   - Contains sensor data and system information
   - Proper message type identification

### Current Limitations ❌

1. **Command Responses**: Firmware doesn't respond
   - GET_KNOB_INFO command sent correctly
   - No 'knob' message received in response
   - Only 'log' messages observed
   - No 'ack' messages for sent commands

2. **Bidirectional Communication**: Incomplete
   - Host → Device: Working (commands sent)
   - Device → Host: Partial (only log messages)
   - Missing: Command responses, ACK messages

## Protocol Statistics

From a typical 5-second capture:

```
Total frames captured: 22
COBS decoded:          22 (100.0%)
CRC32 valid:           22 (100.0%)
Protobuf parsed:       22 (100.0%)
Message types:         {'log': 22}
Protocol versions:     {1: 22}
```

## Implementation Notes

### Queue Management

The protocol implements ACK-based queue management:
- Outgoing messages queued with unique nonces
- Retry after 250ms if no ACK received
- Maximum 10 retries before dropping message
- Queue overflow protection (max 10 messages)

### Threading

- Background thread for continuous reading
- Thread-safe queue operations
- Proper cleanup on disconnect

### Error Handling

- CRC32 validation with error counting
- Protocol version validation
- Graceful handling of malformed frames
- Comprehensive logging for debugging

## Troubleshooting

### Common Issues

1. **No data received**: Check baud rate (921600) and port name
2. **CRC errors**: Verify little-endian byte order in CRC calculation
3. **COBS decode errors**: Check frame delimiter handling (0x00)
4. **Protobuf parse errors**: Ensure correct .proto files and generation

### Debug Tools

1. **Protocol Audit**: `test_protocol_audit.py` validates all layers
2. **Connection Test**: `test_connection.py` verifies basic connectivity
3. **Raw Capture**: Capture and analyze raw bytes for debugging

## Future Work

Once firmware command response issues are resolved:

1. Implement full bidirectional communication
2. Add application-level command/response patterns
3. Implement configuration management
4. Add motor control and sensor reading APIs
5. Create higher-level application interfaces

## References

- COBS Specification: [Wikipedia](https://en.wikipedia.org/wiki/Consistent_Overhead_Byte_Stuffing)
- Protocol Buffers: [Google Developers](https://developers.google.com/protocol-buffers)
- CRC32 Algorithm: [RFC 3309](https://tools.ietf.org/html/rfc3309)
