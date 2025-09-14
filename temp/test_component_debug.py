#!/usr/bin/env python3
"""
SmartKnob Component System Test with Log Monitoring

Enhanced test that focuses on seeing firmware log messages to debug 
why our AppComponent messages aren't being processed.
"""

import sys
import os
import time
import logging
import anyio
from datetime import datetime

# Add smartknob-connection2 directory to path for imports
connection_path = os.path.join(os.path.dirname(__file__), '..', 'smartknob-connection2')
sys.path.insert(0, connection_path)

from smartknob.protocol import SmartKnobConnection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

class ComponentSystemDebugTest:
    """Debug test class focusing on firmware communication."""
    
    def __init__(self, connection):
        self.connection = connection
        self.message_count = 0
        self.received_acks = []
        self.log_messages = []
        
    def on_message(self, msg):
        """Handle incoming messages from the device."""
        self.message_count += 1
        msg_type = msg.WhichOneof("payload")
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if msg_type == 'log':
            origin = msg.log.origin
            message = msg.log.msg
            self.log_messages.append(f"[{origin}] {message}")
            print(f"[{timestamp}] 📝 LOG [{origin}] {message}")
            
        elif msg_type == 'ack':
            nonce = msg.ack.nonce
            self.received_acks.append(nonce)
            print(f"[{timestamp}] ✅ ACK received (nonce={nonce})")
            
        elif msg_type == 'smartknob_state':
            state = msg.smartknob_state
            print(f"[{timestamp}] 🎛️ STATE: pos={state.current_position}, sub={state.sub_position_unit:.3f}")
            
        elif msg_type == 'knob':
            print(f"[{timestamp}] 📦 KNOB INFO received")
            
        else:
            print(f"[{timestamp}] 📨 {msg_type.upper()}")

    async def test_knob_info_first(self):
        """First send a known working command to verify communication."""
        print("\n🧪 TEST: Sending GET_KNOB_INFO (working command)")
        
        # Send GET_KNOB_INFO command that we know works
        await self.connection.send_command(0)  # GET_KNOB_INFO
        
        print("⏳ Waiting for knob info response...")
        await anyio.sleep(3.0)
        
        return True

    async def test_request_state(self):
        """Test RequestState message that we know works."""
        print("\n🧪 TEST: Sending RequestState message")
        
        # Create RequestState message using the working pattern from App_communication.py
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.request_state.CopyFrom(smartknob_pb2.RequestState())
        await self.connection.protocol._enqueue_message(to_smartknob)
        
        print("⏳ Waiting for state response...")
        await anyio.sleep(2.0)
        
        return True

    async def test_toggle_component_creation(self):
        """Test creating a toggle component via AppComponent message."""
        print("\n🧪 TEST: Creating ToggleComponent")
        print("📝 Looking for ComponentManager logs...")
        
        # Create AppComponent message for toggle creation using the working pattern
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "test_toggle_01"
        to_smartknob.app_component.type = 0  # TOGGLE = 0
        to_smartknob.app_component.display_name = "Test Toggle"
        
        # Configure toggle-specific settings
        to_smartknob.app_component.toggle.snap_point = 0.55
        to_smartknob.app_component.toggle.snap_point_bias = 0.0
        to_smartknob.app_component.toggle.off_label = "OFF"
        to_smartknob.app_component.toggle.on_label = "ON"
        to_smartknob.app_component.toggle.initial_state = False
        to_smartknob.app_component.toggle.detent_strength_unit = 1.0
        to_smartknob.app_component.toggle.off_led_hue = 0    # Red
        to_smartknob.app_component.toggle.on_led_hue = 120   # Green
        
        print("📤 Sending AppComponent message:")
        print(f"   Component ID: {to_smartknob.app_component.component_id}")
        print("   Type: TOGGLE (0)")
        print(f"   Protocol tag: 8 (PB_ToSmartknob_app_component_tag)")
        
        # Send the message using the working async pattern
        await self.connection.protocol._enqueue_message(to_smartknob)
        
        # Wait longer for response and logs
        print("⏳ Waiting for firmware logs and ACK...")
        await anyio.sleep(5.0)
        
        # Check if we got any relevant log messages
        component_logs = [log for log in self.log_messages if 'component' in log.lower() or 'rootTask' in log]
        if component_logs:
            print("📝 Found component-related logs:")
            for log in component_logs:
                print(f"   {log}")
        else:
            print("❌ No component-related logs found")
        
        return len(self.received_acks) > 0

    async def run_debug_test_suite(self):
        """Run all tests focusing on debugging communication."""
        print("🚀 Starting Component System Debug Test Suite")
        print("=" * 60)
        
        try:
            # Test 1: Known working command
            print("\n📡 Testing basic communication...")
            await self.test_knob_info_first()
            
            # Test 2: Known working protobuf message
            print("\n📡 Testing protobuf communication...")
            await self.test_request_state()
            
            # Test 3: Our AppComponent message
            print("\n📡 Testing AppComponent message...")
            await self.test_toggle_component_creation()
            
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("📊 DEBUG RESULTS:")
        print(f"📨 Total messages received: {self.message_count}")
        print(f"✅ ACKs received: {len(self.received_acks)}")
        print(f"📝 Log messages: {len(self.log_messages)}")
        
        if self.log_messages:
            print("\n📝 All log messages received:")
            for i, log in enumerate(self.log_messages[-10:], 1):  # Show last 10
                print(f"   {i}. {log}")

async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartKnob Component System Debug Test")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("--baud", type=int, default=921600, help="Baud rate")
    parser.add_argument("--duration", type=float, default=20.0, help="Test duration (seconds)")
    
    args = parser.parse_args()
    
    # Determine port to use
    if args.port:
        port = args.port
        print(f"Using specified port: {port}")
    else:
        print("🔍 Auto-detecting SmartKnob device...")
        ports = find_smartknob_ports(validate_protocol=False)
        if not ports:
            print("❌ No SmartKnob devices found")
            print("💡 Try: python test_component_debug.py --port <PORT>")
            return 1
        port = ports[0]
        print(f"✅ Auto-detected SmartKnob: {port}")
    
    print(f"🔗 Connecting to {port} at {args.baud} baud...")
    
    try:
        async with SmartKnobConnection(port, args.baud) as connection:
            print("✅ Connected successfully!")
            
            # Create test instance
            test = ComponentSystemDebugTest(connection)
            
            # Set up message handler
            connection.set_message_callback(test.on_message)
            
            # Start read loop in background
            async with anyio.create_task_group() as tg:
                # Start protocol read loop
                tg.start_soon(connection.protocol.read_loop)
                
                # Wait for initial connection
                await anyio.sleep(1.0)
                
                # Run the debug test suite
                await test.run_debug_test_suite()
                
                # Monitor for additional time to see responses
                print(f"\n👀 Monitoring for additional {args.duration} seconds...")
                await anyio.sleep(args.duration)
                
                # Cancel the task group
                tg.cancel_scope.cancel()
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    anyio.run(main)
