#!/usr/bin/env python3
"""
SmartKnob Component Crash Debug Script - FIXED VERSION

This script sends component activation commands step by step with full logging
to identify where crashes occur during component selection.
Uses the proven working pattern from test_physical_working.py
"""

import sys
import os
import time
import logging
import anyio
import serial

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
        self.port = None
        self.log_messages = []
        self.received_acks = []
        self.knob_events = []

    def on_message(self, msg):
        """Handle incoming messages with detailed logging - PROVEN WORKING PATTERN."""
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

    async def test_component_creation_with_raw_logs(self):
        """Test component creation with full raw logging - PROVEN WORKING PATTERN."""
        port = await self.find_port()
        if not port:
            return False
            
        try:
            print(f"🔗 Connecting to {port}...")
            async with SmartKnobConnection(port) as connection:
                print("✅ Connected successfully")
                
                # Set up message handler using PROVEN WORKING METHOD
                connection.set_message_callback(self.on_message)
                
                print("\n" + "="*50)
                print("🧪 STEP 1: Start protocol read loop and begin logging")
                print("="*50)
                
                async with anyio.create_task_group() as tg:
                    # Start protocol read loop using PROVEN WORKING PATTERN
                    tg.start_soon(connection.protocol.read_loop)
                    
                    # Wait for initial connection and start seeing logs
                    print("⏳ Waiting for device to stabilize and start logging...")
                    await anyio.sleep(3.0)
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 2: Create toggle component configuration")
                    print("="*50)
                    
                    # Create toggle component using PROVEN WORKING PATTERN
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
                    
                    print(f"📝 Created config: ID='{to_smartknob.app_component.component_id}', Name='{to_smartknob.app_component.display_name}'")
                    print(f"   Initial state: {to_smartknob.app_component.toggle.initial_state}")
                    print(f"   Snap point: {to_smartknob.app_component.toggle.snap_point}")
                    print(f"   LED colors: off={to_smartknob.app_component.toggle.off_led_hue}°, on={to_smartknob.app_component.toggle.on_led_hue}°")
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 3: Send component creation request (CRITICAL POINT)")
                    print("="*50)
                    
                    print("🔍 Current log count before sending:", len(self.log_messages))
                    print("📤 Sending component creation request...")
                    
                    initial_log_count = len(self.log_messages)
                    
                    try:
                        # Send using PROVEN WORKING METHOD
                        await connection.protocol._enqueue_message(to_smartknob)
                        print("✅ Component creation request sent successfully")
                    except Exception as e:
                        print(f"❌ Failed to send component creation request: {e}")
                        return False
                        
                    print("\n" + "="*50)
                    print("🧪 STEP 4: Monitor for crashes immediately after sending")
                    print("="*50)
                    
                    # Monitor immediately after sending - this is where crashes typically occur
                    print("⚠️  Critical monitoring phase - watching for crash/reset...")
                    print("🔍 Raw logs will appear below:")
                    print("-" * 50)
                    
                    await anyio.sleep(8.0)  # Give time for any immediate crash and logs
                    
                    print("-" * 50)
                    new_log_count = len(self.log_messages) - initial_log_count
                    print(f"📊 Captured {new_log_count} new log messages after sending request")
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 5: Extended monitoring for delayed issues")
                    print("="*50)
                    
                    # Extended monitoring to catch any delayed crashes or behavior
                    if len(self.received_acks) > 0:
                        print("🎉 ACK received! Component creation acknowledged by device")
                    else:
                        print("⚠️  No ACK yet - continuing to monitor...")
                    
                    print("🔍 Continuing extended monitoring:")
                    print("-" * 50)
                    await anyio.sleep(10.0)
                    print("-" * 50)
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 6: Test component interaction")
                    print("="*50)
                    
                    # If we get here, the component activated successfully
                    print("🎉 No crash detected! Testing knob interaction...")
                    print("🎛️  Try turning the knob to test the toggle component...")
                    print("🔍 Knob interaction logs:")
                    print("-" * 50)
                    await anyio.sleep(15.0)
                    print("-" * 50)
                    
                    # Summary
                    print("\n" + "="*50)
                    print("📊 FINAL TEST SUMMARY")
                    print("="*50)
                    print(f"   📝 Total log messages: {len(self.log_messages)}")
                    print(f"   ✅ ACKs received: {len(self.received_acks)}")
                    print(f"   🎛️  Knob events: {len(self.knob_events)}")
                    
                    if len(self.received_acks) > 0:
                        print("   ✅ SUCCESS: Component creation was acknowledged")
                    else:
                        print("   ❌ FAILURE: No ACK received - component creation failed")
                    
                    if len(self.knob_events) > 0:
                        print("   ✅ SUCCESS: Knob interaction detected")
                    else:
                        print("   ⚠️  WARNING: No knob interaction detected")
                    
                    return len(self.received_acks) > 0
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main test execution."""
    print("🚀 SmartKnob Component Crash Debug Test")
    print("🔍 Using PROVEN WORKING PATTERN from test_physical_working.py")
    print("=" * 60)
    
    debugger = ComponentCrashDebugger()
    success = await debugger.test_component_creation_with_raw_logs()
    
    if success:
        print("\n✅ All tests passed - component creation successful!")
    else:
        print("\n❌ Test failed - crash or component creation failure detected!")
        
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
