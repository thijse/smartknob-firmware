# SmartKnob Implementation Details

This document describes the internal implementation of the SmartKnob connection library.

## Architecture Overview

The library is designed with a layered architecture that separates concerns and provides clean interfaces:

```
┌─────────────────────────────────────────────────────────────┐
│ Public API (smartknob/__init__.py)                         │
│ ├─ SmartKnobConnection (high-level interface)              │
│ ├─ connect_smartknob() (convenience function)              │
│ └─ find_smartknob_ports() (auto-detection)                 │
├─────────────────────────────────────────────────────────────┤
│ Connection Management (smartknob/connection.py)            │
│ ├─ Port discovery and filtering                            │
│ ├─ Connection lifecycle management                         │
│ └─ Error handling and retry logic                          │
├─────────────────────────────────────────────────────────────┤
│ Protocol Implementation (smartknob/protocol.py)            │
│ ├─ SmartKnobProtocol (core protocol handler)               │
│ ├─ Message encoding/decoding                               │
│ ├─ Queue management and retries                            │
│ └─ Background thread processing                            │
├─────────────────────────────────────────────────────────────┤
│ Generated Code (smartknob/proto_gen/)                      │
│ ├─ smartknob_pb2.py (message definitions)                  │
│ └─ settings_pb2.py (settings definitions)                  │
└─────────────────────────────────────────────────────────────┘
```

## Core Classes

### SmartKnobProtocol

The heart of the library, implementing the complete protocol stack.

**Key Features:**
- Thread-safe operation with background reading
- ACK-based message queuing with automatic retries
- Complete COBS+CRC32+Protobuf implementation
- Comprehensive error handling and statistics

**Threading Model:**
```python
Main Thread:
├─ Message sending (queued)
├─ Public API calls
└─ Statistics and control

Background Thread:
├─ Continuous serial reading
├─ Frame processing
├─ Message parsing
└─ Callback invocation
```

**Message Queue:**
- FIFO queue with nonce-based tracking
- Automatic retry after 250ms timeout
- Maximum 10 retries before dropping
- Queue overflow protection (max 10 messages)

### SmartKnobConnection

High-level connection manager providing a simple interface.

**Features:**
- Context manager support (`with` statement)
- Automatic protocol switching ('q' command)
- Connection lifecycle management
- Error handling and cleanup

**Usage Pattern:**
```python
with SmartKnobConnection("COM9") as knob:
    knob.set_message_callback(my_callback)
    knob.send_command(0)  # GET_KNOB_INFO
    # Automatic cleanup on exit
```

## Protocol Implementation Details

### Frame Processing Pipeline

**Incoming Data Flow:**
```python
Serial Bytes → Buffer Accumulation → Frame Splitting → COBS Decode → 
CRC32 Verify → Protobuf Parse → Message Dispatch → Callback
```

**Outgoing Data Flow:**
```python
Protobuf Message → Serialize → CRC32 Append → COBS Encode → 
Frame Delimiter → Queue → Serial Write → Retry Management
```

### COBS Implementation

Uses the standard `cobs` Python library:

```python
def _encode_frame(self, payload: bytes) -> bytes:
    # Add CRC32
    crc = self._calculate_crc32(payload)
    packet = payload + struct.pack('<I', crc)
    
    # COBS encode and add delimiter
    encoded = cobs.encode(packet)
    return encoded + b'\x00'

def _decode_frame(self, raw_frame: bytes) -> Optional[bytes]:
    # COBS decode
    packet = cobs.decode(raw_frame)
    
    # Verify CRC32
    payload = packet[:-4]
    received_crc = struct.unpack('<I', packet[-4:])[0]
    calculated_crc = self._calculate_crc32(payload)
    
    if received_crc == calculated_crc:
        return payload
    return None
```

### CRC32 Implementation

Standard CRC32 with little-endian byte order:

```python
def _calculate_crc32(self, data: bytes) -> int:
    return zlib.crc32(data) & 0xffffffff
```

**Key Points:**
- Uses Python's `zlib.crc32()` function
- Masks to 32-bit unsigned integer
- Little-endian packing: `struct.pack('<I', crc)`

### Message Queue Management

**Queue Entry Structure:**
```python
@dataclass
class QueueEntry:
    nonce: int              # Unique message identifier
    encoded_payload: bytes  # Pre-encoded frame
    timestamp: float        # Send timestamp
    retry_count: int = 0    # Number of retries
```

**Queue Operations:**
- Thread-safe with `threading.Lock()`
- FIFO ordering with retry priority
- Automatic cleanup on ACK receipt
- Overflow protection with queue clearing

### Statistics Tracking

Comprehensive statistics for debugging and monitoring:

```python
@dataclass
class ProtocolStats:
    messages_sent: int = 0      # Successfully sent messages
    messages_received: int = 0  # Successfully parsed messages
    acks_received: int = 0      # ACK messages received
    retries: int = 0           # Message retries
    crc_errors: int = 0        # CRC validation failures
    protocol_errors: int = 0   # Protocol/parsing errors
    log_messages: int = 0      # Log message count
    knob_messages: int = 0     # Knob info message count
    other_messages: int = 0    # Other message types
```

## Error Handling Strategy

### Graceful Degradation

The library is designed to continue operating despite errors:

1. **CRC Errors**: Log warning, increment counter, continue
2. **COBS Errors**: Skip frame, continue processing
3. **Protobuf Errors**: Log error, increment counter, continue
4. **Serial Errors**: Mark port unavailable, attempt recovery

### Error Recovery

**Connection Recovery:**
- Automatic port availability detection
- Graceful handling of disconnection
- Clean resource cleanup

**Protocol Recovery:**
- Frame synchronization on errors
- Buffer clearing on corruption
- Retry mechanism for failed sends

### Logging Strategy

Structured logging with appropriate levels:

```python
logger.debug()   # Frame-level details, verbose output
logger.info()    # Connection events, major operations
logger.warning() # Recoverable errors, retries
logger.error()   # Serious errors, connection failures
```

## Performance Considerations

### Memory Management

- Efficient buffer handling with `bytearray`
- Minimal memory allocation in hot paths
- Proper cleanup of resources

### Threading Efficiency

- Single background thread for reading
- Non-blocking main thread operations
- Minimal lock contention

### Protocol Efficiency

- Pre-encoded message caching
- Efficient frame boundary detection
- Optimized CRC32 calculation

## Testing Strategy

### Unit Testing

Each component is designed for testability:

- **Protocol Layer**: Mock serial interface
- **Connection Layer**: Dependency injection
- **Utilities**: Pure functions with clear inputs/outputs

### Integration Testing

Real hardware testing with comprehensive validation:

- **Protocol Audit**: Validates all protocol layers
- **Connection Test**: Verifies basic connectivity
- **Statistics Validation**: Ensures accurate counting

### Test Coverage

Key areas covered by tests:

1. **COBS Encoding/Decoding**: 100% success validation
2. **CRC32 Calculation**: Checksum verification
3. **Protobuf Parsing**: Message structure validation
4. **Queue Management**: Retry and timeout behavior
5. **Error Handling**: Graceful failure modes

## Configuration Options

### Protocol Parameters

```python
PROTOBUF_PROTOCOL_VERSION = 1    # Protocol version
RETRY_TIMEOUT_MS = 250           # Retry timeout
MAX_RETRIES = 10                 # Maximum retry attempts
MAX_QUEUE_SIZE = 10              # Queue overflow limit
```

### Serial Parameters

```python
DEFAULT_BAUD = 921600            # Default baud rate
DEFAULT_TIMEOUT = 0              # Non-blocking reads
```

## Extension Points

### Custom Message Handlers

```python
def custom_handler(message):
    msg_type = message.WhichOneof("payload")
    if msg_type == 'log':
        # Custom log processing
        pass

protocol.on_message = custom_handler
```

### Custom Connection Logic

```python
class CustomConnection(SmartKnobConnection):
    def connect(self):
        # Custom connection logic
        return super().connect()
```

### Protocol Extensions

The protocol implementation can be extended for:

- Custom message types
- Alternative transport layers
- Enhanced error recovery
- Performance optimizations

## Debugging Tools

### Built-in Diagnostics

```python
# Get protocol statistics
stats = protocol.get_stats()
print(f"Messages sent: {stats['messages_sent']}")
print(f"CRC errors: {stats['crc_errors']}")

# Clear statistics
protocol.clear_stats()
```

### External Tools

- **Protocol Audit**: Comprehensive protocol validation
- **Raw Capture**: Binary data analysis
- **Connection Test**: Basic connectivity verification

## Known Limitations

### Current Constraints

1. **Single Connection**: One device per protocol instance
2. **Serial Only**: No network transport support
3. **Fixed Protocol**: Version 1 only
4. **Threading Model**: Single background thread

### Future Improvements

1. **Multi-device Support**: Connection pooling
2. **Transport Abstraction**: Network protocols
3. **Protocol Negotiation**: Version detection
4. **Performance Optimization**: Async I/O

## Dependencies

### Core Dependencies

- **pyserial**: Serial communication
- **cobs**: COBS encoding/decoding
- **protobuf**: Message serialization

### Development Dependencies

- **pytest**: Unit testing framework

### System Requirements

- **Python 3.7+**: Modern Python features
- **Windows/Linux/Mac**: Cross-platform support
- **Serial Port**: Hardware or virtual COM port

## Maintenance Notes

### Code Organization

- **Single Responsibility**: Each class has one purpose
- **Clear Interfaces**: Well-defined public APIs
- **Comprehensive Documentation**: Inline and external docs
- **Type Hints**: Full type annotation

### Version Management

- **Semantic Versioning**: Major.Minor.Patch
- **Backward Compatibility**: Maintain API stability
- **Deprecation Warnings**: Gradual API changes

### Quality Assurance

- **Code Review**: All changes reviewed
- **Testing**: Comprehensive test coverage
- **Documentation**: Keep docs current
- **Performance**: Monitor and optimize
