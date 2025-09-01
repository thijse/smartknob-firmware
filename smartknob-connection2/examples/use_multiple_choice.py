#!/usr/bin/env python3
"""
SmartKnob MultipleChoice Component Example

Simple example showing how to use the MultipleChoice component.
Based on the working toggle example pattern.
"""

import sys
import os
import logging
import anyio
from datetime import datetime

# Add smartknob-connection2 directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
smartknob_path = os.path.dirname(current_dir)
sys.path.insert(0, smartknob_path)

from smartknob.protocol import SmartKnobConnection, reset_connection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

# Suppress logging except for errors
logging.basicConfig(level=logging.ERROR)

class MultipleChoiceMonitor:
    """Clean multiple choice monitoring."""
    
    def __init__(self, connection, options=None):
        self.connection = connection
        self.options = options or ["Option 1", "Option 2", "Option 3"]
        self.last_position = None
        self.component_active = False
        self.button_pressed = False
        
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
                
                # Check for button press
                if hasattr(state, 'pressed') and state.pressed:
                    self.button_pressed = True
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    selected_value = self.get_selected_value(current_position)
                    print(f"[{timestamp}] 🔘 SELECTED: {selected_value} (index {current_position})")
                
                # Only print when position actually changes
                #print(f"unfiltered: [{timestamp}] {selected_value} ({current_position})")
                #if self.last_position is not None and current_position != self.last_position:
                timestamp = datetime.now().strftime("%H:%M:%S")
                selected_value = self.get_selected_value(current_position)
                print(f"[{timestamp}] {selected_value} ({current_position})")
                
                self.last_position = current_position

    def get_selected_value(self, position):
        """Get the selected value for a position."""
        if 0 <= position < len(self.options):
            return self.options[position]
        return f"Unknown ({position})"

    def is_button_pressed(self):
        """Check if button was pressed and reset flag."""
        if self.button_pressed:
            self.button_pressed = False
            return True
        return False

    async def create_multiple_choice_component(self, component_id="multi_choice", title="Select Option", options=None):
        """Create a multiple choice component."""
        if options:
            self.options = options
        
        # Create AppComponent message
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = component_id
        to_smartknob.app_component.type = 2  # MULTI_CHOICE = 2
        to_smartknob.app_component.display_name = title
        
        # Configure multiple choice
        multi_choice = to_smartknob.app_component.multi_choice
        
        # Set options
        del multi_choice.options[:]
        for option in self.options:
            multi_choice.options.append(option)
        
        # Configure settings
        multi_choice.initial_index = 0
        multi_choice.wrap_around = True
        multi_choice.detent_strength_unit = 1.5  # Strong feedback
        multi_choice.endstop_strength_unit = 1.5  # Strong endstops
        multi_choice.led_hue = 200  # Blue color
        
        # Send message
        await self.connection.protocol._enqueue_message(to_smartknob)
        
        # Wait for component creation by polling component_active flag
        timeout = 10.0  # Maximum wait time in seconds
        start_time = anyio.current_time()
        
        while not self.component_active:
            if (anyio.current_time() - start_time) > timeout:
                print("⚠️ Warning: Component creation timeout")
                return False
            await anyio.sleep(0.1)  # Check every 100ms
        
        print("✅ Component created successfully!")
        return True

    async def monitor_selection(self, duration_seconds=None):
        """Monitor selection changes."""
        print(f"Multiple Choice Monitor - {len(self.options)} options")
        print("=" * 50)
        print("Options:", ", ".join(self.options))
        print("Rotate the knob to select options.")
        print("Press the knob to confirm selection.")
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
    """Main function for multiple choice monitoring."""
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Connecting to SmartKnob on {port}...")
    
    # Reset for clean state
    reset_connection(port)
    
    try:
        # Connect and start monitoring
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected!")
            
            # Create monitor with drink options
            drinks = ["Coffee", "Tea", "Water", "Juice", "Soda"]
            monitor = MultipleChoiceMonitor(connection, options=drinks)
            
            # Set up message handler
            connection.set_message_callback(monitor.on_message)
            
            # Start protocol read loop
            async with anyio.create_task_group() as tg:
                # Start protocol read loop
                tg.start_soon(connection.protocol.read_loop)
                
                # Wait for initial connection
                await anyio.sleep(1.0)
                
                # Create multiple choice component
                await monitor.create_multiple_choice_component(
                    component_id="drink_selector",
                    title="Drink Selector", 
                    options=drinks
                )
                
                # Monitor selection changes
                await monitor.monitor_selection()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped")
    except Exception as e:
        print(f"\n💥 Error: {e}")
