#!/usr/bin/env python3
"""
SmartKnob Physical Component Test using Working Protocol

This script uses the proven communication pattern from test_component_system_reset.py
but adds physical interaction monitoring.
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

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
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
        time.sleep(2.0)  # ESP32 boot time
        print("✅ Reset complete")
        return True
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False

class PhysicalComponentTester:
    """Physical component testing using proven communication patterns with raw data logging."""
    
    def __init__(self, connection):
        self.connection = connection
        self.message_count = 0
        self.received_acks = []
        self.physical_interactions = []
        self.raw_log_file = None
        self.setup_raw_logging()
        
    def setup_raw_logging(self):
        """Set up raw data logging to file under project logs directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Write logs to smartknob-connection2/logs/test_physical_working_with_raw_logging_toggle/<timestamped>.log
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, 'logs', 'test_physical_working_with_raw_logging_toggle')
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f"smartknob_raw_{timestamp}.log"
        full_path = os.path.join(log_dir, log_filename)
        self.raw_log_file = open(full_path, 'wb')  # Binary mode for raw data
        print(f"📝 Raw serial data will be logged to: {full_path}")
        
    def on_raw_data(self, data: bytes):
        """Handle raw serial data for logging."""
        if self.raw_log_file:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Log to file (binary data)
            log_entry = f"[{timestamp}] ".encode('utf-8') + data + b'\n'
            self.raw_log_file.write(log_entry)
            self.raw_log_file.flush()
            
            # Also try to decode and print to console if it's text
            try:
                decoded = data.decode('utf-8', errors='replace')
                lines = decoded.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"[{timestamp}] RAW: {line.strip()}")
                        
                        # Highlight critical messages
                        if any(keyword in line.lower() for keyword in ['reset', 'crash', 'panic', 'abort', 'component', 'error']):
                            print(f"[{timestamp}] ⚠️  RAW CRITICAL: {line.strip()}")
                            
            except Exception:
                # If decode fails, show as hex
                print(f"[{timestamp}] RAW HEX: {data.hex()}")
    
    def cleanup_raw_logging(self):
        """Close raw logging file."""
        if self.raw_log_file:
            self.raw_log_file.close()
            self.raw_log_file = None
        
    def on_message(self, msg):
        """Handle incoming messages from the device."""
        self.message_count += 1
        msg_type = msg.WhichOneof("payload")
        
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if msg_type == 'log':
            origin = msg.log.origin
            message = msg.log.msg
            print(f"[{timestamp}] 📝 LOG [{origin}] {message}")
            
            # Look for component-related activity
            if any(keyword in message.lower() for keyword in ['component', 'toggle', 'knob', 'state', 'rotation', 'button', 'snap', 'position']):
                self.physical_interactions.append(f"[{timestamp}] {message}")
                print(f"[{timestamp}] 🎮 PHYSICAL: {message}")
            
        elif msg_type == 'ack':
            nonce = msg.ack.nonce
            self.received_acks.append(nonce)
            print(f"[{timestamp}] ✅ ACK received (nonce={nonce})")
            
        elif msg_type == 'smartknob_state':
            state = msg.smartknob_state
            # Only log position changes that might indicate physical interaction
            pos_change = abs(state.current_position) > 0.01 or abs(state.sub_position_unit) > 0.01
            if pos_change:
                print(f"[{timestamp}] 🎛️ KNOB STATE: pos={state.current_position}, sub={state.sub_position_unit:.3f}")
                self.physical_interactions.append(f"[{timestamp}] Knob moved: pos={state.current_position}, sub={state.sub_position_unit:.3f}")
            
        elif msg_type == 'knob':
            print(f"[{timestamp}] 📦 KNOB INFO received")

    async def create_physical_toggle_component(self):
        """Create a toggle component optimized for physical testing."""
        print("\\n🧪 TEST: Creating Physical Toggle Component")
        
        # Create AppComponent message (using proven working pattern)
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "physical_test_toggle"
        to_smartknob.app_component.type = 0  # TOGGLE = 0
        to_smartknob.app_component.display_name = "Physical Test"
        
        # Configure toggle with strong physical feedback
        to_smartknob.app_component.toggle.off_label = "OFF"
        to_smartknob.app_component.toggle.on_label = "ON"
        to_smartknob.app_component.toggle.snap_point = 0.5  # Clear 50% snap point
        to_smartknob.app_component.toggle.snap_point_bias = 0.0  # No bias
        to_smartknob.app_component.toggle.initial_state = False  # Start OFF
        to_smartknob.app_component.toggle.detent_strength_unit = 2.0  # Strong haptic feedback
        to_smartknob.app_component.toggle.off_led_hue = 0    # Red when OFF
        to_smartknob.app_component.toggle.on_led_hue = 120   # Green when ON
        
        print("📤 Sending Physical Toggle Component:")
        print(f"   Component ID: {to_smartknob.app_component.component_id}")
        print("   Type: TOGGLE")
        print(f"   Snap point: {to_smartknob.app_component.toggle.snap_point}")
        print(f"   Detent strength: {to_smartknob.app_component.toggle.detent_strength_unit}")
        print(f"   Labels: {to_smartknob.app_component.toggle.off_label} / {to_smartknob.app_component.toggle.on_label}")
        
        # Send using proven working async pattern
        await self.connection.protocol._enqueue_message(to_smartknob)
        
        # Wait for ACK
        print("⏳ Waiting for component creation ACK...")
        await anyio.sleep(3.0)
        
        return len(self.received_acks) > 0

    async def monitor_physical_interaction(self, duration_seconds=60):
        """Monitor for physical interactions with the component."""
        print(f"\\n🎮 PHYSICAL INTERACTION MONITORING ({duration_seconds}s)")
        print("=" * 60)
        print("🖥️  DISPLAY CHECK:")
        print("   ❓ Do you see a toggle component on the SmartKnob display?")
        print("   ❓ Does it show 'Physical Test' and 'OFF' state?")
        print("   ❓ Is the menu blocked/unresponsive (indicating component mode)?")
        print("")
        print("🎮 PHYSICAL TESTING INSTRUCTIONS:")
        print("   1. 🔄 Try rotating the knob slowly")
        print("   2. 🔄 Try rotating past the 50% snap point") 
        print("   3. 🔘 Try pressing the button")
        print("   4. 👀 Watch for LED color changes (Red ↔ Green)")
        print("   5. ⚡ Feel for strong haptic feedback")
        print("   6. 🖥️  Look for display state changes")
        print("")
        print("💬 Physical interactions will be logged below...")
        print("Press Ctrl+C to stop monitoring")
        print("")
        
        start_time = anyio.current_time()
        last_summary = start_time
        
        try:
            while (anyio.current_time() - start_time) < duration_seconds:
                await anyio.sleep(0.1)
                
                # Print summary every 10 seconds
                current_time = anyio.current_time()
                if current_time - last_summary >= 10:
                    elapsed = int(current_time - start_time)
                    print(f"\\n⏱️  Monitoring for {elapsed}s - Messages: {self.message_count}, ACKs: {len(self.received_acks)}, Physical events: {len(self.physical_interactions)}")
                    if len(self.physical_interactions) > 0:
                        print(f"   📊 Recent physical activity detected!")
                    last_summary = current_time
                    
        except KeyboardInterrupt:
            print("\\n🛑 Physical testing stopped by user")
        
        # Final summary
        elapsed = int(anyio.current_time() - start_time)
        print(f"\\n📊 PHYSICAL TEST RESULTS ({elapsed}s):")
        print(f"   📨 Total messages: {self.message_count}")
        print(f"   ✅ ACKs received: {len(self.received_acks)}")
        print(f"   🎮 Physical interactions: {len(self.physical_interactions)}")
        
        if len(self.physical_interactions) > 0:
            print(f"\\n🎮 Physical interaction summary:")
            for interaction in self.physical_interactions[-10:]:  # Last 10 events
                print(f"   • {interaction}")
        else:
            print(f"\\n❌ No physical interactions detected")
            print(f"   Possible issues:")
            print(f"   • Component not displayed")
            print(f"   • Component not receiving input")
            print(f"   • Device still in menu mode")

async def main():
    """Main test function using proven working patterns."""
    
    print("🎯 Physical Component Test (Using Working Protocol)")
    print("=" * 60)
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Found SmartKnob on: {port}")
    
    # Reset for clean state
    if not reset_esp32(port):
        print("❌ Reset failed, continuing anyway...")
    
    print(f"🔗 Connecting to {port}...")
    
    try:
        # Use proven working connection pattern with context manager
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected successfully!")
            
            # Create tester with proven message handling and raw logging
            tester = PhysicalComponentTester(connection)
            
            # Set up message handler using proven working method
            connection.set_message_callback(tester.on_message)
            
            # Set up raw data callback for logging (NEW!)
            connection.set_raw_data_callback(tester.on_raw_data)
            print("📡 Raw data logging enabled")
            
            # Start protocol read loop using proven working pattern
            async with anyio.create_task_group() as tg:
                # Start protocol read loop
                tg.start_soon(connection.protocol.read_loop)
                
                # Wait for initial connection
                await anyio.sleep(2.0)
                
                print("\n" + "="*60)
                print("🧪 COMPONENT CREATION - MONITORING FOR CRASH")
                print("="*60)
                print("⚠️  Watch raw output below for any reset/crash messages...")
                print()
                
                # Create component using proven working pattern
                success = await tester.create_physical_toggle_component()
                
                if success:
                    print("✅ Component created successfully - ACK received")
                    
                    # Monitor for physical interactions
                    await tester.monitor_physical_interaction(duration_seconds=120)  # 2 minutes
                    
                else:
                    print("❌ Component creation failed - no ACK received")
                    print("Cannot proceed with physical testing")
                    
            # Cleanup raw logging
            tester.cleanup_raw_logging()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
