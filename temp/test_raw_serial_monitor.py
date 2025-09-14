#!/usr/bin/env python3
"""
SmartKnob Raw Serial Monitor with Component Test

This script captures RAW serial output from the ESP32 and sends component
commands to identify exactly where crashes occur.
"""

import sys
import os
import time
import serial
import threading
import queue
from datetime import datetime

# Add smartknob-connection2 directory to path for imports
connection_path = os.path.join(os.path.dirname(__file__), '..', 'smartknob-connection2')
sys.path.insert(0, connection_path)

from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

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
    """Monitor raw serial output and send component commands."""
    
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
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=0.1)
            self.running = True
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_thread, daemon=True)
            monitor_thread.start()
            
            print(f"📡 Started raw serial monitoring on {self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start serial monitoring: {e}")
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
                                self.output_queue.put(log_entry)
                                
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
    
    def send_raw_data(self, data):
        """Send raw data to the serial port."""
        try:
            if self.serial_conn:
                self.serial_conn.write(data)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] SENT: {data}")
                return True
        except Exception as e:
            print(f"❌ Failed to send data: {e}")
        return False
    
    def send_protobuf_mode_command(self):
        """Send the command to switch to protobuf mode."""
        print("📤 Sending 'q' command to switch to protobuf mode...")
        return self.send_raw_data(b'q')
    
    def stop_monitoring(self):
        """Stop serial monitoring."""
        self.running = False
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
        print("⏹️  Serial monitoring stopped")

def test_component_creation_with_raw_serial():
    """Test component creation while monitoring raw serial output."""
    
    print("🚀 SmartKnob Raw Serial Component Test")
    print("=" * 60)
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return False
        
    port = ports[0]
    print(f"📱 Found SmartKnob on: {port}")
    
    # Reset device for clean state
    if not reset_esp32(port):
        print("❌ Reset failed, continuing anyway...")
    
    # Create raw serial monitor
    monitor = RawSerialMonitor(port)
    
    try:
        print("\n" + "="*50)
        print("🧪 STEP 1: Start raw serial monitoring")
        print("="*50)
        
        if not monitor.start_monitoring():
            return False
            
        # Wait to see initial boot messages
        print("⏳ Monitoring initial boot sequence...")
        time.sleep(5.0)
        
        print("\n" + "="*50)
        print("🧪 STEP 2: Switch to protobuf mode")
        print("="*50)
        
        # Send protobuf mode command
        monitor.send_protobuf_mode_command()
        print("⏳ Waiting for protobuf mode switch...")
        time.sleep(2.0)
        
        print("\n" + "="*50)
        print("🧪 STEP 3: Create and send component (CRITICAL POINT)")
        print("="*50)
        
        print("🔍 Current raw output count:", len(monitor.raw_output))
        print("📤 Now creating and sending component creation message...")
        print("⚠️  WATCH FOR CRASH/RESET MESSAGES BELOW:")
        print("-" * 50)
        
        # Create the component message using the proper protobuf format
        try:
            # Import here to avoid issues if not available
            import sys
            import os
            connection_path = os.path.join(os.path.dirname(__file__), '..', 'smartknob-connection2')
            sys.path.insert(0, connection_path)
            from smartknob.proto_gen import smartknob_pb2
            
            # Create toggle component message
            to_smartknob = smartknob_pb2.ToSmartknob()
            to_smartknob.app_component.component_id = "raw_debug_toggle"
            to_smartknob.app_component.type = 0  # TOGGLE = 0
            to_smartknob.app_component.display_name = "Raw Debug"
            
            # Set toggle-specific config
            to_smartknob.app_component.toggle.off_label = "OFF"
            to_smartknob.app_component.toggle.on_label = "ON"
            to_smartknob.app_component.toggle.snap_point = 0.5
            to_smartknob.app_component.toggle.snap_point_bias = 0.0
            to_smartknob.app_component.toggle.initial_state = False
            to_smartknob.app_component.toggle.detent_strength_unit = 2.0
            to_smartknob.app_component.toggle.off_led_hue = 0    # Red when off
            to_smartknob.app_component.toggle.on_led_hue = 120   # Green when on
            
            print(f"📝 Created component: {to_smartknob.app_component.component_id}")
            
            # Serialize the protobuf message
            message_bytes = to_smartknob.SerializeToString()
            print(f"📦 Serialized message: {len(message_bytes)} bytes")
            
            # Now we need to frame it properly for the ESP32
            # The ESP32 expects messages in a specific format
            
            # For now, let's just send the raw bytes and see what happens
            print("📤 Sending raw protobuf bytes...")
            if monitor.send_raw_data(message_bytes):
                print("✅ Raw protobuf message sent")
            else:
                print("❌ Failed to send raw protobuf message")
                
        except Exception as e:
            print(f"❌ Failed to create/send component message: {e}")
            import traceback
            traceback.print_exc()
        
        print("📡 Monitoring for 10 seconds after sending component...")
        time.sleep(10.0)
        
        print("-" * 50)
        print(f"📊 Captured {len(monitor.raw_output)} raw serial messages")
        
        print("\n" + "="*50)
        print("🧪 STEP 4: Extended monitoring")
        print("="*50)
        
        print("📡 Extended monitoring for any delayed effects...")
        time.sleep(10.0)
        
        print("\n" + "="*50)
        print("📊 RAW SERIAL SUMMARY")
        print("="*50)
        print(f"Total raw messages captured: {len(monitor.raw_output)}")
        
        # Look for specific patterns in the raw output
        error_messages = [msg for msg in monitor.raw_output if any(keyword in msg.lower() for keyword in ['error', 'crash', 'panic', 'abort', 'exception', 'reset'])]
        if error_messages:
            print(f"⚠️  Found {len(error_messages)} error/crash messages:")
            for msg in error_messages[-5:]:  # Show last 5
                print(f"   {msg}")
        else:
            print("✅ No obvious error/crash messages detected")
            
        component_messages = [msg for msg in monitor.raw_output if 'component' in msg.lower()]
        if component_messages:
            print(f"🧩 Found {len(component_messages)} component-related messages:")
            for msg in component_messages[-5:]:  # Show last 5
                print(f"   {msg}")
                
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    try:
        success = test_component_creation_with_raw_serial()
        if success:
            print("\n✅ Raw serial test completed")
        else:
            print("\n❌ Raw serial test failed")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
