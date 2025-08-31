#!/usr/bin/env python3
"""
SmartKnob Physical MultipleChoice Component Test using Working Protocol

This script uses the proven communication pattern from test_component_system_reset.py
but tests the MultipleChoice component and monitors for crashes.
"""

import sys
import os
import time
import logging
import anyio
import serial
import traceback
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

class PhysicalMultipleChoiceTester:
    """Physical MultipleChoice component testing with crash detection."""
    
    def __init__(self, connection):
        self.connection = connection
        self.message_count = 0
        self.received_acks = []
        self.physical_interactions = []
        self.raw_log_file = None
        self.crash_detected = False
        self.component_created = False
        self.setup_raw_logging()
        
    def setup_raw_logging(self):
        """Set up raw data logging to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"smartknob_multiple_choice_{timestamp}.log"
        self.raw_log_file = open(log_filename, 'wb')  # Binary mode for raw data
        print(f"📝 Raw serial data will be logged to: {log_filename}")
        
    def on_raw_data(self, data: bytes):
        """Handle raw serial data for logging and crash detection."""
        if self.raw_log_file:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Log to file (binary data)
            log_entry = f"[{timestamp}] ".encode('utf-8') + data + b'\n'
            self.raw_log_file.write(log_entry)
            self.raw_log_file.flush()
            
            # Try to decode and analyze for crashes
            try:
                decoded = data.decode('utf-8', errors='replace')
                lines = decoded.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"[{timestamp}] RAW: {line.strip()}")
                        
                        # Detect crashes/resets
                        crash_keywords = ['reset', 'crash', 'panic', 'abort', 'exception', 'guru meditation', 
                                        'fatal', 'stack canary', 'loadprohibited', 'storeprohibited',
                                        'illegelinstruction', 'instr_fetchprohibited', 'double_exception']
                        
                        if any(keyword in line.lower() for keyword in crash_keywords):
                            self.crash_detected = True
                            print(f"[{timestamp}] 💥 CRASH DETECTED: {line.strip()}")
                            
                        # Detect component-related activity
                        component_keywords = ['component', 'multiplechoice', 'multi_choice', 'selector', 'option']
                        if any(keyword in line.lower() for keyword in component_keywords):
                            print(f"[{timestamp}] 🧩 COMPONENT: {line.strip()}")
                            
                        # Detect successful component creation
                        if 'component created' in line.lower() or 'multiplechoice' in line.lower():
                            self.component_created = True
                            print(f"[{timestamp}] ✅ COMPONENT SUCCESS: {line.strip()}")
                            
            except Exception:
                # If decode fails, show as hex and check for reset patterns
                hex_data = data.hex()
                print(f"[{timestamp}] RAW HEX: {hex_data}")
                
                # Look for common reset patterns in hex
                if 'ets' in hex_data.lower() or 'rst:' in hex_data.lower():
                    self.crash_detected = True
                    print(f"[{timestamp}] 💥 BINARY RESET DETECTED")
    
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
            
            # Look for MultipleChoice-related activity
            choice_keywords = ['choice', 'selector', 'option', 'index', 'text', 'knob', 'rotation', 'position']
            if any(keyword in message.lower() for keyword in choice_keywords):
                self.physical_interactions.append(f"[{timestamp}] {message}")
                print(f"[{timestamp}] 🎮 CHOICE INTERACTION: {message}")
            
        elif msg_type == 'ack':
            nonce = msg.ack.nonce
            self.received_acks.append(nonce)
            print(f"[{timestamp}] ✅ ACK received (nonce={nonce})")
            
        elif msg_type == 'smartknob_state':
            state = msg.smartknob_state
            # Log all position changes for MultipleChoice testing
            pos_change = abs(state.current_position) > 0.01 or abs(state.sub_position_unit) > 0.01
            if pos_change:
                print(f"[{timestamp}] 🎛️ KNOB STATE: pos={state.current_position}, sub={state.sub_position_unit:.3f}")
                self.physical_interactions.append(f"[{timestamp}] Knob moved: pos={state.current_position}, sub={state.sub_position_unit:.3f}")
            
        elif msg_type == 'knob':
            print(f"[{timestamp}] 📦 KNOB INFO received")

    async def create_multiple_choice_component(self):
        """Create a MultipleChoice component for testing."""
        print("\\n🧪 TEST: Creating MultipleChoice Component")
        
        # Create AppComponent message
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "test_multiple_choice"
        to_smartknob.app_component.type = 2  # MULTI_CHOICE = 2
        to_smartknob.app_component.display_name = "Drink Selector"
        
        # Configure MultipleChoice with drink options
        multi_choice = to_smartknob.app_component.multi_choice
        
        # Set options (plain text, no unicode)
        options = [
            "Coffee",
            "Tea", 
            "Water",
            "Juice",
            "Soda"
        ]
        
        # Clear existing options and add new ones
        del multi_choice.options[:]
        for option in options:
            multi_choice.options.append(option)
        
        # Configure settings
        multi_choice.initial_index = 0
        multi_choice.wrap_around = True
        multi_choice.detent_strength_unit = 1.5  # Strong feedback for testing
        multi_choice.endstop_strength_unit = 1.5  # Strong endstops for boundary feedback
        multi_choice.led_hue = 200  # Blue color
        
        print("📤 Sending MultipleChoice Component:")
        print(f"   Component ID: {to_smartknob.app_component.component_id}")
        print("   Type: MULTI_CHOICE (2)")
        print(f"   Display Name: {to_smartknob.app_component.display_name}")
        print(f"   Options: {list(multi_choice.options)}")
        print(f"   Initial Index: {multi_choice.initial_index}")
        print(f"   Wrap Around: {multi_choice.wrap_around}")
        print(f"   Detent Strength: {multi_choice.detent_strength_unit}")
        print(f"   Endstop Strength: {multi_choice.endstop_strength_unit}")
        print(f"   LED Hue: {multi_choice.led_hue}")
        
        # Send message
        print("📡 Sending message...")
        await self.connection.protocol._enqueue_message(to_smartknob)
        
        # Wait and monitor for response/crash
        print("⏳ Waiting for response (monitoring for crashes)...")
        start_time = anyio.current_time()
        
        while (anyio.current_time() - start_time) < 5.0:  # Wait 5 seconds
            await anyio.sleep(0.1)
            
            if self.crash_detected:
                print("💥 CRASH DETECTED during component creation!")
                return False
                
            if len(self.received_acks) > 0:
                print("✅ ACK received - component likely created successfully")
                return True
        
        print("⚠️ No ACK received within timeout")
        return False

    async def monitor_multiple_choice_interaction(self, duration_seconds=60):
        """Monitor for MultipleChoice interactions."""
        print(f"\\n🎮 MULTIPLE CHOICE INTERACTION MONITORING ({duration_seconds}s)")
        print("=" * 60)
        print("🖥️  DISPLAY CHECK:")
        print("   ❓ Do you see 'Drink Selector' on the SmartKnob display?")
        print("   ❓ Does it show 'Coffee ☕' as the initial selection?")
        print("   ❓ Is there a position indicator (1/5) at the bottom?")
        print("")
        print("🎮 MULTIPLE CHOICE TESTING INSTRUCTIONS:")
        print("   1. 🔄 Rotate knob clockwise - should cycle through:")
        print("      Coffee ☕ → Tea 🍵 → Water 💧 → Juice 🧃 → Soda 🥤")
        print("   2. 🔄 Rotate past 'Soda 🥤' - should wrap to 'Coffee ☕'")
        print("   3. � Rotate counter-clockwise to go backwards")
        print("   4. 🔘 Press button to select current option")
        print("   5. 👀 Watch for text changes on display")
        print("   6. ⚡ Feel for detent feedback at each option")
        print("   7. � LED should be blue (hue=200)")
        print("")
        print("💬 Physical interactions will be logged below...")
        print("Press Ctrl+C to stop monitoring")
        print("")
        
        start_time = anyio.current_time()
        last_summary = start_time
        
        try:
            while (anyio.current_time() - start_time) < duration_seconds:
                await anyio.sleep(0.1)
                
                # Check for crashes during interaction
                if self.crash_detected:
                    print("💥 CRASH DETECTED during interaction testing!")
                    break
                
                # Print summary every 15 seconds
                current_time = anyio.current_time()
                if current_time - last_summary >= 15:
                    elapsed = int(current_time - start_time)
                    print(f"\\n⏱️  Monitoring for {elapsed}s - Messages: {self.message_count}, ACKs: {len(self.received_acks)}, Physical events: {len(self.physical_interactions)}")
                    if len(self.physical_interactions) > 0:
                        print("   📊 Recent choice interactions detected!")
                    last_summary = current_time
                    
        except KeyboardInterrupt:
            print("\\n🛑 Testing stopped by user")
        
        # Final summary
        elapsed = int(anyio.current_time() - start_time)
        print(f"\\n📊 MULTIPLE CHOICE TEST RESULTS ({elapsed}s):")
        print(f"   📨 Total messages: {self.message_count}")
        print(f"   ✅ ACKs received: {len(self.received_acks)}")
        print(f"   🎮 Choice interactions: {len(self.physical_interactions)}")
        print(f"   💥 Crash detected: {self.crash_detected}")
        print(f"   🧩 Component created: {self.component_created}")
        
        if len(self.physical_interactions) > 0:
            print("\\n🎮 Choice interaction summary:")
            for interaction in self.physical_interactions[-10:]:  # Last 10 events
                print(f"   • {interaction}")
        else:
            print("\\n❌ No choice interactions detected")
            if self.crash_detected:
                print("   Likely cause: Component crashed during creation")
            else:
                print("   Possible issues:")
                print("   • Component not displayed properly")
                print("   • MultipleChoice component has bugs")
                print("   • Device reverted to menu mode")

async def main():
    """Main test function for MultipleChoice component."""
    
    print("🎯 MultipleChoice Component Test (Crash Detection)")
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
        # Use proven working connection pattern
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected successfully!")
            
            # Create tester with crash detection
            tester = PhysicalMultipleChoiceTester(connection)
            
            # Set up message handler
            connection.set_message_callback(tester.on_message)
            
            # Set up raw data callback for crash detection
            connection.set_raw_data_callback(tester.on_raw_data)
            print("📡 Raw data logging enabled (crash detection active)")
            
            # Start protocol read loop
            async with anyio.create_task_group() as tg:
                # Start protocol read loop
                tg.start_soon(connection.protocol.read_loop)
                
                # Wait for initial connection
                await anyio.sleep(2.0)
                
                print("\n" + "="*60)
                print("🧪 MULTIPLE CHOICE COMPONENT CREATION")
                print("="*60)
                print("⚠️  Monitoring for crashes during component creation...")
                print()
                
                # Create MultipleChoice component
                success = await tester.create_multiple_choice_component()
                
                if success and not tester.crash_detected:
                    print("✅ MultipleChoice component created successfully!")
                    
                    # Monitor for physical interactions
                    await tester.monitor_multiple_choice_interaction(duration_seconds=120)  # 2 minutes
                    
                elif tester.crash_detected:
                    print("💥 Component creation caused a crash!")
                    print("❌ Cannot proceed with interaction testing")
                    print("")
                    print("🔍 DEBUGGING SUGGESTIONS:")
                    print("   • Check MultipleChoice component constructor")
                    print("   • Verify protobuf message structure")
                    print("   • Check memory allocation in component")
                    print("   • Review component_manager.cpp integration")
                    
                else:
                    print("❌ Component creation failed - no ACK received")
                    print("Cannot proceed with interaction testing")
                    
            # Cleanup
            tester.cleanup_raw_logging()
            
            # Final crash report
            if tester.crash_detected:
                print("\n" + "="*60)
                print("💥 CRASH ANALYSIS")
                print("="*60)
                print("The MultipleChoice component appears to cause crashes.")
                print("Check the raw log file for detailed crash information.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\\n💥 Test crashed: {e}")
        traceback.print_exc()
