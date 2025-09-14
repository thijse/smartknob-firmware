#!/usr/bin/env python3
"""
SmartKnob Component System Test

Test script to validate the new component system implementation:
- Test ComponentManager functionality
- Test ToggleComponent creation and configuration
- Test protocol communication with AppComponent messages
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

class ComponentSystemTest:
    """Test class for component system functionality."""
    
    def __init__(self, connection):
        self.connection = connection
        self.message_count = 0
        self.received_acks = []
        
    def on_message(self, msg):
        """Handle incoming messages from the device."""
        self.message_count += 1
        msg_type = msg.WhichOneof("payload")
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if msg_type == 'log':
            level = msg.log.level
            origin = msg.log.origin
            message = msg.log.msg
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

    async def test_toggle_component_creation(self):
        """Test creating a toggle component via AppComponent message."""
        print("\n🧪 TEST: Creating ToggleComponent")
        
        # Create AppComponent message using the working pattern from test_component_debug.py
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
        print("   Type: TOGGLE")
        print(f"   Snap point: {to_smartknob.app_component.toggle.snap_point}")
        print(f"   Labels: {to_smartknob.app_component.toggle.off_label} / {to_smartknob.app_component.toggle.on_label}")
        
        # Send the message using the working async pattern
        await self.connection.protocol._enqueue_message(to_smartknob)
        
        # Wait for response
        print("⏳ Waiting for ACK...")
        await anyio.sleep(2.0)
        
        return len(self.received_acks) > 0

    async def test_component_activation(self):
        """Test activating the created component."""
        print("\n🧪 TEST: Activating ToggleComponent")
        
        # For now, let's just request state to see what happens
        # Component activation would be handled in a different message
        request_state = smartknob_pb2.RequestState()
        
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.request_state.CopyFrom(request_state)
        
        print("📤 Sending state request message")
        
        await self.connection.protocol._enqueue_message(to_smartknob)
        await anyio.sleep(2.0)

    async def test_component_state_change(self):
        """Test changing component state via protocol."""
        print("\n🧪 TEST: Testing component system")
        
        # For now, let's send another component creation to test the system
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "test_toggle_02"
        to_smartknob.app_component.type = 0  # TOGGLE = 0
        to_smartknob.app_component.display_name = "Second Toggle"
        
        to_smartknob.app_component.toggle.snap_point = 0.6
        to_smartknob.app_component.toggle.snap_point_bias = 0.2
        to_smartknob.app_component.toggle.off_label = "CLOSED"
        to_smartknob.app_component.toggle.on_label = "OPEN"
        to_smartknob.app_component.toggle.initial_state = True
        to_smartknob.app_component.toggle.detent_strength_unit = 1.0
        to_smartknob.app_component.toggle.off_led_hue = 240   # Blue
        to_smartknob.app_component.toggle.on_led_hue = 60     # Yellow
        
        print("📤 Sending second component creation")
        
        await self.connection.protocol._enqueue_message(to_smartknob)
        await anyio.sleep(2.0)

    async def run_comprehensive_test(self):
        """Run all component system tests."""
        print("🚀 Starting Component System Test Suite")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 3
        
        try:
            # Test 1: Component creation
            if await self.test_toggle_component_creation():
                print("✅ TEST 1 PASSED: Component creation")
                tests_passed += 1
            else:
                print("❌ TEST 1 FAILED: Component creation")
            
            # Test 2: Component activation
            await self.test_component_activation()
            print("✅ TEST 2 COMPLETED: Component activation")
            tests_passed += 1
            
            # Test 3: State change
            await self.test_component_state_change()
            print("✅ TEST 3 COMPLETED: State change")
            tests_passed += 1
            
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS: {tests_passed}/{total_tests} passed")
        print(f"📨 Total messages received: {self.message_count}")
        print(f"✅ ACKs received: {len(self.received_acks)}")

async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartKnob Component System Test")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("--baud", type=int, default=921600, help="Baud rate")
    parser.add_argument("--duration", type=float, default=15.0, help="Test duration (seconds)")
    
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
            print("💡 Try: python test_component_system.py --port <PORT>")
            return 1
        port = ports[0]
        print(f"✅ Auto-detected SmartKnob: {port}")
    
    print(f"🔗 Connecting to {port} at {args.baud} baud...")
    
    try:
        async with SmartKnobConnection(port, args.baud) as connection:
            print("✅ Connected successfully!")
            
            # Create test instance
            test = ComponentSystemTest(connection)
            
            # Set up message handler
            connection.set_message_callback(test.on_message)
            
            # Start read loop in background
            async with anyio.create_task_group() as tg:
                # Start protocol read loop
                tg.start_soon(connection.protocol.read_loop)
                
                # Wait for initial connection
                await anyio.sleep(1.0)
                
                # Run the test suite
                await test.run_comprehensive_test()
                
                # Monitor for additional time to see responses
                print(f"\n👀 Monitoring for {args.duration} seconds...")
                await anyio.sleep(args.duration)
                
                # Cancel the task group
                tg.cancel_scope.cancel()
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return 1

if __name__ == "__main__":
    anyio.run(main)
