#!/usr/bin/env python3
"""
SmartKnob Toggle Button State Monitor

Clean interface that only shows toggle state changes with the configured labels.
"""

import sys
import os
import time
import logging
import anyio
import serial
from datetime import datetime

# Add smartknob-connection2 directory to path for imports
connection_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, connection_path)

from smartknob.protocol import SmartKnobConnection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

# Suppress logging except for errors
logging.basicConfig(level=logging.ERROR)

def reset_esp32(port, baud=921600):
    """Reset ESP32 by toggling DTR and RTS lines."""
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

class ToggleStateMonitor:
    """Clean toggle state monitoring."""
    
    def __init__(self, connection, off_label="OFF", on_label="ON"):
        self.connection = connection
        self.off_label = off_label
        self.on_label = on_label
        self.last_position = None
        self.component_active = False
        
    def on_message(self, msg):
        """Handle incoming messages from the device."""
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

    async def create_toggle_component(self, component_id="toggle", title="Toggle", off_label="OFF", on_label="ON"):
        """Create a toggle component with specified labels."""
        self.off_label = off_label
        self.on_label = on_label
        
        # Create AppComponent message
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = component_id
        to_smartknob.app_component.type = 0  # TOGGLE = 0
        to_smartknob.app_component.display_name = title
        
        # Configure toggle
        to_smartknob.app_component.toggle.off_label = off_label
        to_smartknob.app_component.toggle.on_label = on_label
        to_smartknob.app_component.toggle.snap_point = 0.5  # 50% snap point
        to_smartknob.app_component.toggle.snap_point_bias = 0.0  # No bias
        to_smartknob.app_component.toggle.initial_state = False  # Start OFF
        to_smartknob.app_component.toggle.detent_strength_unit = 2.0  # Moderate haptic feedback
        to_smartknob.app_component.toggle.off_led_hue = 0    # Red when OFF
        to_smartknob.app_component.toggle.on_led_hue = 120   # Green when ON
        
        # Send message
        await self.connection.protocol._enqueue_message(to_smartknob)
        
        # Wait for component creation
        await anyio.sleep(2.0)
        
        return True

    async def monitor_toggle_state(self, duration_seconds=None):
        """Monitor toggle state changes."""
        print(f"Toggle State Monitor - {self.off_label} / {self.on_label}")
        print("=" * 50)
        print("Rotate the knob to toggle between states.")
        print("Press Ctrl+C to stop monitoring.")
        print("")
        
        start_time = anyio.current_time()
        
        try:
            if duration_seconds:
                while (anyio.current_time() - start_time) < duration_seconds:
                    await anyio.sleep(0.1)
            else:
                # Run indefinitely
                while True:
                    await anyio.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nStopped by user")

async def main():
    """Main function for clean toggle monitoring."""
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Connecting to SmartKnob on {port}...")
    
    # Reset for clean state
    reset_esp32(port)
    
    try:
        # Connect and start monitoring
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected!")
            
            # Create monitor with custom labels
            monitor = ToggleStateMonitor(connection, off_label="Aan", on_label="Uit")
            
            # Set up message handler
            connection.set_message_callback(monitor.on_message)
            
            # Start protocol read loop
            async with anyio.create_task_group() as tg:
                # Start protocol read loop
                tg.start_soon(connection.protocol.read_loop)
                
                # Wait for initial connection
                await anyio.sleep(1.0)
                
                # Create toggle component
                await monitor.create_toggle_component(
                    component_id="clean_toggle",
                    title="Toggle Monitor", 
                    off_label="Aan",
                    on_label="Uit"
                )
                
                # Monitor state changes
                await monitor.monitor_toggle_state()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped")
    except Exception as e:
        print(f"\n💥 Error: {e}")
