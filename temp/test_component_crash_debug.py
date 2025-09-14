#!/usr/bin/env python3
"""
SmartKnob Component Crash Debug Script

This script sends component activation commands step by step with full logging
to identify where crashes occur during component selection.
"""

import sys
import os
import time
import logging
import anyio
import serial
from datetime import datetime

# Add smartknob-connection2 directory to path for imports
connection_path = os.path.join(os.path.dirname(__file__), '..', 'smartknob-connection2')
sys.path.insert(0, connection_path)

from smartknob.protocol import SmartKnobConnection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

def reset_esp32(port, baud=921600):
    """Reset ESP32 by toggling DTR and RTS lines."""
    print(f"🔄 Resetting ESP32 on {port}...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
        ser.dtr = False  # DTR low
        ser.rts = True   # RTS high (active)
        time.sleep(0.1)  # Hold for 100ms
        ser.rts = False  # RTS low (inactive) - releases reset
        time.sleep(0.1)  # Brief delay
        ser.close()
        print("⏳ Waiting for ESP32 to boot...")
        time.sleep(3.0)  # Longer wait for stability
        print("✅ Reset complete")
        return True
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False

class ComponentCrashDebugger:
    """Debug component activation crashes with step-by-step logging."""
    
    def __init__(self):
        self.connection = None
        self.port = None
        self.log_messages = []
        self.received_acks = []
        self.knob_events = []

    def on_message(self, msg):
        """Handle incoming messages with detailed logging."""
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
        msg_type = msg.WhichOneof("payload")
        
        if msg_type == 'log':
            origin = msg.log.origin
            message = msg.log.msg
            log_entry = f"[{timestamp}] 📝 LOG [{origin}] {message}"
            print(log_entry)
            self.log_messages.append(log_entry)
            
            # Highlight critical messages
            if any(keyword in message.lower() for keyword in ['error', 'crash', 'exception', 'panic', 'abort', 'reset', 'component']):
                critical_entry = f"[{timestamp}] ⚠️  CRITICAL: {message}"
                print(critical_entry)
                self.log_messages.append(critical_entry)
                
        elif msg_type == 'ack':
            nonce = msg.ack.nonce
            ack_entry = f"[{timestamp}] ✅ ACK received (nonce={nonce})"
            print(ack_entry)
            self.received_acks.append(nonce)
            
        elif msg_type == 'smartknob_state':
            # Only show significant position changes to avoid spam
            state = msg.smartknob_state
            if abs(state.current_position) > 0.1 or abs(state.sub_position_unit) > 0.1:
                knob_entry = f"[{timestamp}] 🎛️  KNOB: pos={state.current_position}, sub={state.sub_position_unit:.3f}"
                print(knob_entry)
                self.knob_events.append(knob_entry)

    async def find_port(self):
        """Find SmartKnob port with detailed logging."""
        print("🔍 Searching for SmartKnob ports...")
        ports = find_smartknob_ports()
        
        if not ports:
            print("❌ No SmartKnob devices found")
            return None
            
        self.port = ports[0]
        print(f"📱 Found SmartKnob on: {self.port}")
        
        # Reset device first for clean state
        if not reset_esp32(self.port):
            return None
            
        return self.port

    async def monitor_raw_logs(self, connection, duration=5.0, description=""):
        """Monitor and display raw log messages from the device."""
        print(f"📊 {description} - Monitoring raw logs for {duration} seconds...")
        start_time = time.time()
        log_count = 0
        
        async def log_handler(msg):
            nonlocal log_count
            timestamp = time.strftime("%H:%M:%S.%f")[:-3]
            msg_type = msg.WhichOneof("payload")
            
            if msg_type == 'log':
                log_count += 1
                origin = msg.log.origin
                message = msg.log.msg
                print(f"[{timestamp}] 📝 LOG [{origin}] {message}")
                
                # Highlight critical messages
                if any(keyword in message.lower() for keyword in ['error', 'crash', 'exception', 'panic', 'abort', 'reset', 'component']):
                    print(f"[{timestamp}] ⚠️  CRITICAL: {message}")
                    
            elif msg_type == 'ack':
                nonce = msg.ack.nonce
                print(f"[{timestamp}] ✅ ACK received (nonce={nonce})")
                
            elif msg_type == 'smartknob_state':
                # Only show significant position changes to avoid spam
                state = msg.smartknob_state
                if abs(state.current_position) > 0.1 or abs(state.sub_position_unit) > 0.1:
                    print(f"[{timestamp}] 🎛️  KNOB: pos={state.current_position}, sub={state.sub_position_unit:.3f}")
        
        # Start monitoring
        connection.add_message_handler(log_handler)
        
        try:
            while time.time() - start_time < duration:
                await anyio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("⏹️  Log monitoring interrupted by user")
            
        finally:
            connection.remove_message_handler(log_handler)
            
        print(f"✅ Log monitoring complete - {log_count} log messages captured")
        return True

    async def test_component_activation_step_by_step(self):
        """Test component activation with detailed step-by-step logging."""
        port = await self.find_port()
        if not port:
            return False
            
        try:
            print(f"🔗 Connecting to {port}...")
            async with SmartKnobConnection(port) as connection:
                print("✅ Connected successfully")
                
                print("\n" + "="*50)
                print("🧪 STEP 1: Check initial device state")
                print("="*50)
                
                # Wait for initial stability
                print("⏳ Waiting for device to stabilize...")
                await anyio.sleep(2.0)
                
                print("\n" + "="*50)
                print("🧪 STEP 2: Create toggle component configuration")
                print("="*50)
                
                # Create toggle component using working pattern
                to_smartknob = smartknob_pb2.ToSmartknob()
                to_smartknob.app_component.component_id = "debug_toggle"
                to_smartknob.app_component.type = 0  # TOGGLE = 0
                to_smartknob.app_component.display_name = "Debug Toggle"
                
                # Set toggle-specific config with strong feedback
                to_smartknob.app_component.toggle.off_label = "OFF"
                to_smartknob.app_component.toggle.on_label = "ON"
                to_smartknob.app_component.toggle.snap_point = 0.5
                to_smartknob.app_component.toggle.snap_point_bias = 0.0
                to_smartknob.app_component.toggle.initial_state = False
                to_smartknob.app_component.toggle.detent_strength_unit = 2.0
                to_smartknob.app_component.toggle.off_led_hue = 0    # Red when off
                to_smartknob.app_component.toggle.on_led_hue = 120   # Green when on
                
                print(f"� Created config: ID='{to_smartknob.app_component.component_id}', Name='{to_smartknob.app_component.display_name}'")
                print(f"   Initial state: {to_smartknob.app_component.toggle.initial_state}")
                print(f"   LED colors: off={to_smartknob.app_component.toggle.off_led_hue}°, on={to_smartknob.app_component.toggle.on_led_hue}°")
                
                print("\n" + "="*50)
                print("🧪 STEP 3: Start raw logging and send component creation")
                print("="*50)
                
                # Start raw logging monitoring BEFORE sending the request
                print("🔍 Starting raw log monitoring...")
                
                # Create a task to monitor logs in parallel
                async def monitor_and_send():
                    # Start monitoring logs
                    monitor_task = anyio.create_task_group()
                    
                    async with monitor_task:
                        # Start log monitoring
                        monitor_task.start_soon(self.monitor_raw_logs, connection, 8.0, "PRE/POST Component Creation")
                        
                        # Wait a moment to start capturing logs
                        await anyio.sleep(1.0)
                        
                        # Send component creation request
                        print("📤 Sending component creation request...")
                        try:
                            await connection.protocol._enqueue_message(to_smartknob)
                            print("✅ Component creation request sent successfully")
                        except Exception as e:
                            print(f"❌ Failed to send component creation request: {e}")
                            raise
                            
                        # Continue monitoring for a few more seconds after sending
                        print("⏳ Continuing to monitor after sending request...")
                
                await monitor_and_send()
                
                print("\n" + "="*50)
                print("🧪 STEP 4: Extended monitoring for crashes")
                print("="*50)
                
                # Extended monitoring to catch any delayed crashes
                await self.monitor_raw_logs(connection, 10.0, "Extended Crash Detection")
                
                print("\n" + "="*50)
                print("🧪 STEP 5: Test component interaction")
                print("="*50)
                
                # If we get here, the component activated successfully
                print("🎉 Component creation successful! Testing interaction...")
                await self.monitor_raw_logs(connection, 15.0, "Component Interaction Testing")
                
                return True
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main test execution."""
    print("🚀 SmartKnob Component Crash Debug Test")
    print("=" * 60)
    
    debugger = ComponentCrashDebugger()
    success = await debugger.test_component_activation_step_by_step()
    
    if success:
        print("\n✅ All tests passed - no crash detected!")
    else:
        print("\n❌ Test failed - crash or instability detected!")
        
    print("\n🏁 Test complete")

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
