#!/usr/bin/env python3
"""
Test both Toggle and MultipleChoice components to identify the issue.
"""

import sys
import os
import time
import logging
import anyio
import serial
from datetime import datetime

# Add smartknob-connection2 directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
smartknob_path = os.path.dirname(current_dir)
sys.path.insert(0, smartknob_path)

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

class ComponentTester:
    """Test different component types."""
    
    def __init__(self, connection):
        self.connection = connection
        self.component_active = False
        self.last_position = None
        
    def on_message(self, msg):
        """Handle incoming messages from the device."""
        msg_type = msg.WhichOneof("payload")
        
        if msg_type == 'log':
            message = msg.log.msg
            # Check for component activation
            if 'Component mode active' in message:
                self.component_active = True
                print("✅ Component activated!")
            elif 'crash' in message.lower() or 'exception' in message.lower():
                print(f"💥 CRASH: {message}")
                
        elif msg_type == 'smartknob_state':
            if self.component_active:
                state = msg.smartknob_state
                current_position = state.current_position
                
                # Check for button press
                if hasattr(state, 'pressed') and state.pressed:
                    print(f"🔘 Button pressed at position {current_position}")
                
                # Only print when position actually changes
                if self.last_position is not None and current_position != self.last_position:
                    print(f"📍 Position: {current_position}")
                
                self.last_position = current_position

    async def test_toggle_component(self):
        """Test toggle component (known to work)."""
        print("🔄 Testing Toggle Component...")
        
        # Create AppComponent message
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "test_toggle"
        to_smartknob.app_component.type = 0  # TOGGLE = 0
        to_smartknob.app_component.display_name = "Test Toggle"
        
        # Configure toggle
        to_smartknob.app_component.toggle.off_label = "OFF"
        to_smartknob.app_component.toggle.on_label = "ON"
        to_smartknob.app_component.toggle.snap_point = 0.5
        to_smartknob.app_component.toggle.snap_point_bias = 0.0
        to_smartknob.app_component.toggle.initial_state = False
        to_smartknob.app_component.toggle.detent_strength_unit = 2.0
        to_smartknob.app_component.toggle.off_led_hue = 0
        to_smartknob.app_component.toggle.on_led_hue = 120
        
        # Send message
        await self.connection.protocol._enqueue_message(to_smartknob)
        await anyio.sleep(3.0)
        
        return self.component_active

    async def test_multiple_choice_component(self):
        """Test multiple choice component."""
        print("🔢 Testing MultipleChoice Component...")
        self.component_active = False  # Reset flag
        
        # Create AppComponent message
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "test_multi"
        to_smartknob.app_component.type = 2  # MULTI_CHOICE = 2
        to_smartknob.app_component.display_name = "Test Multi"
        
        # Configure multiple choice - use simple options
        multi_choice = to_smartknob.app_component.multi_choice
        
        # Set simple options
        del multi_choice.options[:]
        simple_options = ["A", "B", "C"]
        for option in simple_options:
            multi_choice.options.append(option)
        
        # Use conservative settings
        multi_choice.initial_index = 0
        multi_choice.wrap_around = True
        multi_choice.detent_strength_unit = 1.0  # Conservative
        multi_choice.endstop_strength_unit = 1.0  # Conservative
        multi_choice.led_hue = 120  # Green
        
        # Send message
        await self.connection.protocol._enqueue_message(to_smartknob)
        await anyio.sleep(3.0)
        
        return self.component_active

async def main():
    """Main test function."""
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Connecting to SmartKnob on {port}...")
    
    try:
        # Test Toggle first (should work)
        print("\n=== TESTING TOGGLE COMPONENT ===")
        reset_esp32(port)
        
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected!")
            
            tester = ComponentTester(connection)
            connection.set_message_callback(tester.on_message)
            
            async with anyio.create_task_group() as tg:
                tg.start_soon(connection.protocol.read_loop)
                await anyio.sleep(1.0)
                
                toggle_success = await tester.test_toggle_component()
                print(f"Toggle result: {'✅ SUCCESS' if toggle_success else '❌ FAILED'}")
                
                if toggle_success:
                    print("Toggle component working - test for 5 seconds...")
                    await anyio.sleep(5.0)
        
        # Test MultipleChoice next
        print("\n=== TESTING MULTIPLECHOICE COMPONENT ===")
        reset_esp32(port)
        
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected!")
            
            tester = ComponentTester(connection)
            connection.set_message_callback(tester.on_message)
            
            async with anyio.create_task_group() as tg:
                tg.start_soon(connection.protocol.read_loop)
                await anyio.sleep(1.0)
                
                multi_success = await tester.test_multiple_choice_component()
                print(f"MultipleChoice result: {'✅ SUCCESS' if multi_success else '❌ FAILED'}")
                
                if multi_success:
                    print("MultipleChoice component working - test for 10 seconds...")
                    await anyio.sleep(10.0)
                else:
                    print("MultipleChoice component failed to activate")
        
        print("\n=== TEST SUMMARY ===")
        print(f"Toggle Component: {'✅ WORKING' if toggle_success else '❌ BROKEN'}")
        print(f"MultipleChoice Component: {'✅ WORKING' if multi_success else '❌ BROKEN'}")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Test stopped")
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
