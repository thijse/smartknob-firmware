#!/usr/bin/env python3
"""
SmartKnob Component Double-Send Test

This script sends component creation messages twice using proper connection
framework to see if we can trigger the reset/crash behavior.
"""

import sys
import os
import time
import logging
import anyio
import serial
import threading
import queue
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
        time.sleep(3.0)
        print("✅ Reset complete")
        return True
    except Exception as e:
        print(f"❌ Reset failed: {e}")
        return False

class RawSerialMonitor:
    """Monitor raw serial output in parallel with proper connection."""
    
    def __init__(self, port, baud=921600):
        self.port = port
        self.baud = baud
        self.serial_conn = None
        self.running = False
        self.raw_output = []
        self.output_queue = queue.Queue()
        
    def start_monitoring(self):
        """Start raw serial monitoring in a separate thread."""
        try:
            # Use a separate serial connection for raw monitoring
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=0.1)
            self.running = True
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_thread, daemon=True)
            monitor_thread.start()
            
            print(f"📡 Started parallel raw serial monitoring on {self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start parallel serial monitoring: {e}")
            return False
    
    def _monitor_thread(self):
        """Thread function to monitor raw serial output."""
        buffer = ""
        
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    # Read raw bytes
                    data = self.serial_conn.read(self.serial_conn.in_waiting)
                    
                    try:
                        # Try to decode as text
                        text = data.decode('utf-8', errors='replace')
                        buffer += text
                        
                        # Process complete lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if line.strip():  # Only process non-empty lines
                                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                log_entry = f"[{timestamp}] RAW: {line.strip()}"
                                print(log_entry)
                                self.raw_output.append(log_entry)
                                
                                # Look for specific patterns
                                if any(keyword in line.lower() for keyword in ['reset', 'crash', 'panic', 'abort', 'component', 'small packet']):
                                    critical_entry = f"[{timestamp}] ⚠️  CRITICAL: {line.strip()}"
                                    print(critical_entry)
                                    self.raw_output.append(critical_entry)
                                
                    except UnicodeDecodeError:
                        # Handle binary data
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        log_entry = f"[{timestamp}] BINARY: {data.hex()}"
                        print(log_entry)
                        self.raw_output.append(log_entry)
                        
                time.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                if self.running:  # Only print if we're supposed to be running
                    print(f"⚠️  Serial monitoring error: {e}")
                time.sleep(0.1)
    
    def stop_monitoring(self):
        """Stop serial monitoring."""
        self.running = False
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
        print("⏹️  Raw serial monitoring stopped")

class ComponentDoubleSendTester:
    """Test component creation with double-send and proper connection."""
    
    def __init__(self):
        self.port = None
        self.log_messages = []
        self.received_acks = []
        self.knob_events = []
        self.raw_monitor = None

    def on_message(self, msg):
        """Handle incoming messages with detailed logging."""
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
        msg_type = msg.WhichOneof("payload")
        
        if msg_type == 'log':
            origin = msg.log.origin
            message = msg.log.msg
            log_entry = f"[{timestamp}] 📝 PROTO LOG [{origin}] {message}"
            print(log_entry)
            self.log_messages.append(log_entry)
            
            # Highlight critical messages
            if any(keyword in message.lower() for keyword in ['error', 'crash', 'exception', 'panic', 'abort', 'reset', 'component']):
                critical_entry = f"[{timestamp}] ⚠️  PROTO CRITICAL: {message}"
                print(critical_entry)
                self.log_messages.append(critical_entry)
                
        elif msg_type == 'ack':
            nonce = msg.ack.nonce
            ack_entry = f"[{timestamp}] ✅ PROTO ACK received (nonce={nonce})"
            print(ack_entry)
            self.received_acks.append(nonce)
            
        elif msg_type == 'smartknob_state':
            # Only show significant position changes to avoid spam
            state = msg.smartknob_state
            if abs(state.current_position) > 0.1 or abs(state.sub_position_unit) > 0.1:
                knob_entry = f"[{timestamp}] 🎛️  PROTO KNOB: pos={state.current_position}, sub={state.sub_position_unit:.3f}"
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

    async def test_double_component_creation(self):
        """Test component creation with double-send using proper connection AND raw monitoring."""
        port = await self.find_port()
        if not port:
            return False
            
        # Start raw serial monitoring in parallel
        self.raw_monitor = RawSerialMonitor(port)
        # Note: We can't monitor the same port twice, so we'll rely on protobuf logs
        
        try:
            print(f"🔗 Connecting with proper SmartKnobConnection to {port}...")
            async with SmartKnobConnection(port) as connection:
                print("✅ Connected successfully with proper connection")
                
                # Set up message handler
                connection.set_message_callback(self.on_message)
                
                print("\n" + "="*50)
                print("🧪 STEP 1: Start protocol read loop and stabilize")
                print("="*50)
                
                async with anyio.create_task_group() as tg:
                    # Start protocol read loop
                    tg.start_soon(connection.protocol.read_loop)
                    
                    # Wait for initial connection and stabilization
                    print("⏳ Waiting for device to stabilize...")
                    await anyio.sleep(3.0)
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 2: Create component configuration")
                    print("="*50)
                    
                    # Create toggle component using proper format
                    to_smartknob = smartknob_pb2.ToSmartknob()
                    to_smartknob.app_component.component_id = "double_test_toggle"
                    to_smartknob.app_component.type = 0  # TOGGLE = 0
                    to_smartknob.app_component.display_name = "Double Test"
                    
                    # Set toggle-specific config
                    to_smartknob.app_component.toggle.off_label = "OFF"
                    to_smartknob.app_component.toggle.on_label = "ON"
                    to_smartknob.app_component.toggle.snap_point = 0.5
                    to_smartknob.app_component.toggle.snap_point_bias = 0.0
                    to_smartknob.app_component.toggle.initial_state = False
                    to_smartknob.app_component.toggle.detent_strength_unit = 2.0
                    to_smartknob.app_component.toggle.off_led_hue = 0    # Red when off
                    to_smartknob.app_component.toggle.on_led_hue = 120   # Green when on
                    
                    print(f"📝 Created config: ID='{to_smartknob.app_component.component_id}'")
                    print(f"   Display name: '{to_smartknob.app_component.display_name}'")
                    print(f"   Snap point: {to_smartknob.app_component.toggle.snap_point}")
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 3: FIRST component creation send (CRITICAL POINT)")
                    print("="*50)
                    
                    print("🔍 Initial state - Log count:", len(self.log_messages))
                    print("📤 Sending FIRST component creation request...")
                    
                    initial_log_count = len(self.log_messages)
                    
                    try:
                        await connection.protocol._enqueue_message(to_smartknob)
                        print("✅ FIRST component creation request sent successfully")
                    except Exception as e:
                        print(f"❌ Failed to send FIRST component creation request: {e}")
                        return False
                        
                    # Monitor immediately after first send
                    print("⚠️  Monitoring after FIRST send - watching for crash...")
                    await anyio.sleep(3.0)
                    
                    new_logs = len(self.log_messages) - initial_log_count
                    print(f"📊 Captured {new_logs} new log messages after FIRST send")
                    print(f"📊 ACKs received so far: {len(self.received_acks)}")
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 4: SECOND component creation send (DOUBLE-SEND TEST)")
                    print("="*50)
                    
                    print("📤 Sending SECOND component creation request...")
                    
                    second_initial_log_count = len(self.log_messages)
                    
                    try:
                        await connection.protocol._enqueue_message(to_smartknob)
                        print("✅ SECOND component creation request sent successfully")
                    except Exception as e:
                        print(f"❌ Failed to send SECOND component creation request: {e}")
                        return False
                        
                    # Monitor immediately after second send - this might trigger the crash
                    print("⚠️  Monitoring after SECOND send - this might trigger crash...")
                    await anyio.sleep(5.0)
                    
                    new_logs_second = len(self.log_messages) - second_initial_log_count
                    print(f"📊 Captured {new_logs_second} new log messages after SECOND send")
                    print(f"📊 Total ACKs received: {len(self.received_acks)}")
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 5: Extended monitoring for delayed effects")
                    print("="*50)
                    
                    print("📡 Extended monitoring to catch any delayed crashes...")
                    await anyio.sleep(10.0)
                    
                    print("\n" + "="*50)
                    print("🧪 STEP 6: Test knob interaction")
                    print("="*50)
                    
                    print("🎛️  Try turning the knob to test component interaction...")
                    await anyio.sleep(15.0)
                    
                    # Summary
                    print("\n" + "="*50)
                    print("📊 DOUBLE-SEND TEST SUMMARY")
                    print("="*50)
                    print(f"   📝 Total protobuf log messages: {len(self.log_messages)}")
                    print(f"   ✅ ACKs received: {len(self.received_acks)}")
                    print(f"   🎛️  Knob events: {len(self.knob_events)}")
                    
                    if len(self.received_acks) >= 2:
                        print("   ✅ SUCCESS: Both component creation requests acknowledged")
                    elif len(self.received_acks) == 1:
                        print("   ⚠️  PARTIAL: Only one component creation acknowledged")
                    else:
                        print("   ❌ FAILURE: No component creation acknowledged")
                    
                    return len(self.received_acks) > 0
                
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            if self.raw_monitor:
                self.raw_monitor.stop_monitoring()

async def main():
    """Main test execution."""
    print("🚀 SmartKnob Component Double-Send Test")
    print("🔍 Testing if double-sending component creation triggers reset")
    print("=" * 60)
    
    tester = ComponentDoubleSendTester()
    success = await tester.test_double_component_creation()
    
    if success:
        print("\n✅ Double-send test completed - component creation successful!")
    else:
        print("\n❌ Double-send test failed - crash or component creation failure detected!")
        
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
