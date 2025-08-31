# SmartKnob Python Client Guide

This guide explains how to connect to and interact with SmartKnob components using Python, with examples based on the clean toggle button monitor implementation.

## Overview

The SmartKnob Python client provides a high-level interface for:

- **Device Discovery**: Automatically finding SmartKnob devices
- **Connection Management**: Reliable serial communication with error handling
- **Component Control**: Creating and configuring interactive components
- **State Monitoring**: Real-time tracking of component state changes
- **Protocol Handling**: Automatic protobuf message encoding/decoding

## Quick Start

### Basic Connection Example

```python
#!/usr/bin/env python3
import asyncio
from smartknob.protocol import SmartKnobConnection
from smartknob.connection import find_smartknob_ports

async def simple_example():
    # Find SmartKnob device
    ports = find_smartknob_ports()
    if not ports:
        print("No SmartKnob found")
        return
    
    # Connect and use
    async with SmartKnobConnection(ports[0]) as connection:
        print(f"Connected to {ports[0]}")
        
        # Your code here
        await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(simple_example())
```

### Component Creation Example

```python
#!/usr/bin/env python3
import asyncio
from smartknob.protocol import SmartKnobConnection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

async def create_component_example():
    ports = find_smartknob_ports()
    async with SmartKnobConnection(ports[0]) as connection:
        
        # Create component message
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "my_toggle"
        to_smartknob.app_component.type = 0  # TOGGLE = 0
        to_smartknob.app_component.display_name = "My Toggle"
        
        # Configure toggle settings
        to_smartknob.app_component.toggle.off_label = "OFF"
        to_smartknob.app_component.toggle.on_label = "ON"
        to_smartknob.app_component.toggle.snap_point = 0.5
        to_smartknob.app_component.toggle.detent_strength_unit = 2.0
        to_smartknob.app_component.toggle.initial_state = False
        
        # Send to device
        await connection.protocol._enqueue_message(to_smartknob)
        print("Component created!")

if __name__ == "__main__":
    asyncio.run(create_component_example())
```

## Library Architecture

### Core Classes

#### SmartKnobConnection
High-level connection manager providing clean interface and automatic cleanup.

```python
class SmartKnobConnection:
    def __init__(self, port: str, baud: int = 921600)
    async def __aenter__(self) -> 'SmartKnobConnection'
    async def __aexit__(self, exc_type, exc_val, exc_tb)
    
    def set_message_callback(self, callback: Callable)
    async def send_command(self, command: int)
    async def stop()
```

**Features:**
- Context manager support (`async with`)
- Automatic protocol switching ('q' command)
- Connection lifecycle management
- Error handling and cleanup

#### SmartKnobProtocol
Low-level protocol implementation handling message encoding/decoding.

```python
class SmartKnobProtocol:
    def __init__(self, port: str, baud: int = 921600)
    async def start()
    async def stop()
    async def read_loop()
    async def _enqueue_message(self, message)
```

**Features:**
- Thread-safe operation with background reading
- ACK-based message queuing with automatic retries
- Complete COBS+CRC32+Protobuf implementation
- Comprehensive error handling and statistics

### Device Discovery

```python
from smartknob.connection import find_smartknob_ports

# Find all SmartKnob devices
ports = find_smartknob_ports()
print(f"Found SmartKnob devices on: {ports}")

# Manual port specification
port = "COM9"  # Windows
port = "/dev/ttyUSB0"  # Linux
```

The discovery function uses USB VID/PID filtering to identify SmartKnob devices automatically.

## Creating Components

### Toggle Component

The toggle component provides a two-state switch with haptic feedback:

```python
async def create_toggle(connection, component_id="toggle", title="Toggle", 
                       off_label="OFF", on_label="ON"):
    """Create a toggle component with custom labels."""
    
    # Create protobuf message
    to_smartknob = smartknob_pb2.ToSmartknob()
    to_smartknob.app_component.component_id = component_id
    to_smartknob.app_component.type = 0  # TOGGLE = 0
    to_smartknob.app_component.display_name = title
    
    # Configure toggle behavior
    to_smartknob.app_component.toggle.off_label = off_label
    to_smartknob.app_component.toggle.on_label = on_label
    to_smartknob.app_component.toggle.snap_point = 0.5          # 50% snap point
    to_smartknob.app_component.toggle.snap_point_bias = 0.0     # No bias
    to_smartknob.app_component.toggle.initial_state = False     # Start OFF
    to_smartknob.app_component.toggle.detent_strength_unit = 2.0 # Moderate haptic
    to_smartknob.app_component.toggle.off_led_hue = 0           # Red when OFF
    to_smartknob.app_component.toggle.on_led_hue = 120          # Green when ON
    
    # Send to device
    await connection.protocol._enqueue_message(to_smartknob)
    await asyncio.sleep(2.0)  # Wait for creation
```

### Configuration Parameters

#### Toggle Configuration
```python
# Haptic feedback settings
toggle.detent_strength_unit = 2.0    # 0.0 = no haptic, 4.0 = very strong
toggle.snap_point = 0.5              # Threshold for state change (0.5-1.0)
toggle.snap_point_bias = 0.0         # Asymmetric snap behavior

# Visual settings  
toggle.off_label = "OFF"             # Text shown in OFF state
toggle.on_label = "ON"               # Text shown in ON state
toggle.initial_state = False         # Start in OFF state

# LED settings
toggle.off_led_hue = 0               # Hue when OFF (0=red, 120=green, 240=blue)
toggle.on_led_hue = 120              # Hue when ON
```

#### Motor Configuration
```python
# The component automatically configures motor behavior:
motor_config = {
    'position': 0,                    # Current position (0 or 1)
    'min_position': 0,                # Minimum position (OFF)
    'max_position': 1,                # Maximum position (ON)
    'position_width_radians': 1.047,  # 60 degrees per position
    'detent_strength_unit': 2.0,      # Haptic strength
    'snap_point': 0.5,                # State change threshold
    'led_hue': 0                      # Current LED color
}
```

## State Monitoring

### Message Handling

Set up a message callback to monitor device state:

```python
def message_handler(msg):
    """Handle incoming messages from SmartKnob."""
    msg_type = msg.WhichOneof("payload")
    
    if msg_type == 'log':
        # Device log messages
        print(f"LOG: {msg.log.msg}")
        
    elif msg_type == 'smartknob_state':
        # Knob position updates
        state = msg.smartknob_state
        print(f"Position: {state.current_position}")
        
    elif msg_type == 'ack':
        # Command acknowledgments
        print(f"ACK: {msg.ack.nonce}")

# Set the callback
connection.set_message_callback(message_handler)
```

### Clean State Monitoring

Based on `use_toggle_button.py`, here's a clean state monitor implementation:

```python
#!/usr/bin/env python3
"""
Clean SmartKnob component state monitor.
"""

import asyncio
from datetime import datetime
from smartknob.protocol import SmartKnobConnection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

class ComponentStateMonitor:
    """Clean component state monitoring."""
    
    def __init__(self, connection, off_label="OFF", on_label="ON"):
        self.connection = connection
        self.off_label = off_label
        self.on_label = on_label
        self.last_position = None
        self.component_active = False
        
    def on_message(self, msg):
        """Handle incoming messages from device."""
        msg_type = msg.WhichOneof("payload")
        
        if msg_type == 'log':
            message = msg.log.msg
            # Check for component activation
            if 'Component mode active' in message:
                self.component_active = True
                
        elif msg_type == 'smartknob_state':
            if self.component_active:
                state = msg.smartknob_state
                current_position = state.current_position
                
                # Only print when position actually changes
                if self.last_position is not None and current_position != self.last_position:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    state_name = self.on_label if current_position > 0 else self.off_label
                    print(f"[{timestamp}] {state_name} ({current_position})")
                
                self.last_position = current_position

    async def create_component(self, component_id="monitor", title="Monitor"):
        """Create a toggle component for monitoring."""
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = component_id
        to_smartknob.app_component.type = 0  # TOGGLE
        to_smartknob.app_component.display_name = title
        
        # Configure with specified labels
        to_smartknob.app_component.toggle.off_label = self.off_label
        to_smartknob.app_component.toggle.on_label = self.on_label
        to_smartknob.app_component.toggle.snap_point = 0.5
        to_smartknob.app_component.toggle.detent_strength_unit = 2.0
        to_smartknob.app_component.toggle.initial_state = False
        
        await self.connection.protocol._enqueue_message(to_smartknob)
        await asyncio.sleep(2.0)

    async def monitor_forever(self):
        """Monitor state changes indefinitely."""
        print(f"State Monitor - {self.off_label} / {self.on_label}")
        print("=" * 50)
        print("Rotate the knob to change states.")
        print("Press Ctrl+C to stop monitoring.")
        print("")
        
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\\nStopped by user")

async def main():
    """Main monitoring function."""
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    print(f"📡 Connecting to SmartKnob on {ports[0]}...")
    
    async with SmartKnobConnection(ports[0]) as connection:
        print("✅ Connected!")
        
        # Create monitor with custom labels
        monitor = ComponentStateMonitor(connection, off_label="Disabled", on_label="Enabled")
        
        # Set up message handler
        connection.set_message_callback(monitor.on_message)
        
        # Start protocol and create component
        async with asyncio.create_task_group() as tg:
            tg.start_soon(connection.protocol.read_loop)
            
            await asyncio.sleep(1.0)  # Wait for connection
            
            await monitor.create_component("state_monitor", "State Monitor")
            await monitor.monitor_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main)
    except KeyboardInterrupt:
        print("\\n⏹️ Stopped")
```

## Advanced Usage

### Protocol Management

```python
# Manual protocol control
async with anyio.create_task_group() as tg:
    # Start background reading
    tg.start_soon(connection.protocol.read_loop)
    
    # Wait for connection establishment
    await anyio.sleep(1.0)
    
    # Send commands
    await connection.send_command(0)  # GET_KNOB_INFO
    
    # The task group ensures cleanup
```

### Error Handling

```python
async def robust_connection():
    """Example with comprehensive error handling."""
    ports = find_smartknob_ports()
    if not ports:
        raise ConnectionError("No SmartKnob devices found")
    
    try:
        async with SmartKnobConnection(ports[0]) as connection:
            # Set up message handler
            connection.set_message_callback(your_handler)
            
            # Start protocol with task group
            async with asyncio.create_task_group() as tg:
                tg.start_soon(connection.protocol.read_loop)
                
                # Your application logic here
                await your_application_logic(connection)
                
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except asyncio.TimeoutError:
        print("Connection timeout")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

### Device Reset

```python
import serial
import time

def reset_smartknob(port, baud=921600):
    """Reset SmartKnob by toggling DTR and RTS lines."""
    try:
        ser = serial.Serial(port, baud, timeout=1)
        ser.dtr = False  # DTR low
        ser.rts = True   # RTS high (active)
        time.sleep(0.1)  # Hold for 100ms
        ser.rts = False  # RTS low (inactive) - releases reset
        time.sleep(0.1)  # Brief delay
        ser.close()
        time.sleep(2.0)  # ESP32 boot time
        return True
    except Exception:
        return False

# Use before connecting
reset_smartknob("COM9")
```

## Component Types

### Current Components

#### Toggle Component (Type 0)
Two-state switch with configurable labels and haptic feedback.

```python
to_smartknob.app_component.type = 0  # TOGGLE
```

**Configuration:**
- `off_label`, `on_label`: Display text for each state
- `snap_point`: Threshold for state changes (0.5-1.0)
- `detent_strength_unit`: Haptic feedback strength (0.0-4.0)
- `initial_state`: Starting state (True/False)
- `off_led_hue`, `on_led_hue`: LED colors for each state

### Future Components

The architecture supports additional component types:

```python
# Future component types (examples)
COMPONENT_TYPE_SLIDER = 1     # Linear value selection
COMPONENT_TYPE_ENCODER = 2    # Continuous rotation
COMPONENT_TYPE_MENU = 3       # Menu navigation
COMPONENT_TYPE_DIAL = 4       # Circular value input
```

## Troubleshooting

### Common Issues

#### No Device Found
```python
ports = find_smartknob_ports()
if not ports:
    # Check USB connection
    # Verify device is powered
    # Check USB drivers
    # Try manual port specification
    pass
```

#### Connection Timeout
```python
# Increase timeout in connection
connection = SmartKnobConnection(port, timeout=10.0)

# Or add retry logic
for attempt in range(3):
    try:
        async with SmartKnobConnection(port) as conn:
            # Success
            break
    except asyncio.TimeoutError:
        if attempt == 2:
            raise
        await asyncio.sleep(1.0)
```

#### Message Send Failures
```python
# Check ACK reception
def handle_ack(msg):
    if msg.WhichOneof("payload") == 'ack':
        print(f"Message acknowledged: {msg.ack.nonce}")

connection.set_message_callback(handle_ack)
```

### Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or use specific logger
logger = logging.getLogger('smartknob')
logger.setLevel(logging.DEBUG)
```

### Protocol Analysis

```python
def debug_message_handler(msg):
    """Debug handler that prints all message details."""
    msg_type = msg.WhichOneof("payload")
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    print(f"[{timestamp}] {msg_type}: {msg}")
    
    if msg_type == 'smartknob_state':
        state = msg.smartknob_state
        print(f"  Position: {state.current_position}")
        print(f"  Sub-position: {state.sub_position_unit:.3f}")
        print(f"  Config ID: {state.config.id}")
```

## Best Practices

### 1. Use Context Managers
Always use `async with` for automatic cleanup:

```python
async with SmartKnobConnection(port) as connection:
    # Connection automatically closed on exit
    pass
```

### 2. Handle Task Groups Properly
Use task groups for concurrent operations:

```python
async with asyncio.create_task_group() as tg:
    tg.start_soon(connection.protocol.read_loop)
    tg.start_soon(your_main_logic)
    # All tasks cleaned up automatically
```

### 3. Implement Robust Error Handling
```python
try:
    await risky_operation()
except specific.Exception as e:
    # Handle specific errors
    logger.error(f"Operation failed: {e}")
    # Implement recovery logic
```

### 4. Use Appropriate Sleep Intervals
```python
# For state monitoring
await asyncio.sleep(0.1)  # 100ms - responsive

# For component creation
await asyncio.sleep(2.0)  # 2s - allow device processing

# For connection establishment  
await asyncio.sleep(1.0)  # 1s - protocol handshake
```

### 5. Validate Component Configuration
```python
def validate_toggle_config(config):
    """Validate toggle configuration before sending."""
    assert 0.5 <= config.snap_point <= 1.0, "snap_point must be 0.5-1.0"
    assert 0.0 <= config.detent_strength_unit <= 4.0, "detent_strength must be 0.0-4.0"
    assert 0 <= config.off_led_hue <= 255, "led_hue must be 0-255"
    assert 0 <= config.on_led_hue <= 255, "led_hue must be 0-255"
```

This guide provides everything needed to create sophisticated SmartKnob client applications with reliable communication and clean state monitoring.
