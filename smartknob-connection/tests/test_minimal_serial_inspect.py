#!/usr/bin/env python3
"""
Minimal Serial Test with Data Inspection

Test what happens with basic serial open/close and examine the actual data received.
"""

import serial
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smartknob.connection import find_smartknob_ports

def inspect_received_data(data: bytes, label: str):
    """Inspect and display received data."""
    print(f"   📊 {label}: {len(data)} bytes")
    if len(data) > 0:
        # Look for boot messages
        try:
            text = data.decode('utf-8', errors='replace')
            if 'rst:' in text or 'boot' in text.lower() or 'esp32' in text.lower():
                print("   🔄 BOOT MESSAGE DETECTED!")
                print(f"   📝 Text preview: {text[:200]}...")
            else:
                print(f"   📝 Text preview: {text[:100]}...")
        except:
            pass
        
        # Show hex preview
        hex_preview = ' '.join([f'{b:02x}' for b in data[:20]])
        print(f"   🔢 Hex preview: {hex_preview}...")

def test_close_reopen_cycle(port: str, baud: int = 921600):
    """Test close/reopen cycle with data inspection."""
    print(f"=== Testing Close/Reopen Cycle on {port} ===")
    
    try:
        print("1. Initial connection...")
        ser = serial.Serial(port, baud, timeout=1)
        print(f"   ✅ Connected: DTR={ser.dtr}, RTS={ser.rts}")
        
        # Clear any existing data
        time.sleep(0.1)
        if ser.in_waiting > 0:
            existing = ser.read(ser.in_waiting)
            print(f"   🧹 Cleared {len(existing)} existing bytes")
        
        print("2. Sending 'q' command...")
        ser.write(b"q")
        ser.flush()
        
        print("3. Reading initial response...")
        time.sleep(0.5)
        if ser.in_waiting > 0:
            data1 = ser.read(ser.in_waiting)
            inspect_received_data(data1, "Initial response")
        else:
            print("   📭 No initial response")
        
        print("4. Closing connection...")
        ser.close()
        print("   ✅ Connection closed")
        
        print("5. Waiting 5 seconds for potential reset...")
        time.sleep(5.0)
        
        print("6. Reopening connection...")
        ser = serial.Serial(port, baud, timeout=1)
        print(f"   ✅ Reconnected: DTR={ser.dtr}, RTS={ser.rts}")
        
        print("7. Checking for data immediately after reopen...")
        time.sleep(2.0)  # Give more time for any boot messages
        if ser.in_waiting > 0:
            data2 = ser.read(ser.in_waiting)
            inspect_received_data(data2, "Data after reopen")
        else:
            print("   📭 No data after reopen")
        
        print("8. Sending 'q' command after reopen...")
        ser.write(b"q")
        ser.flush()
        
        print("9. Reading response to post-reopen command...")
        time.sleep(2.0)
        if ser.in_waiting > 0:
            data3 = ser.read(ser.in_waiting)
            inspect_received_data(data3, "Response after reopen")
        else:
            print("   📭 No response after reopen")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_multiple_close_reopen_cycles(port: str, baud: int = 921600, cycles: int = 5):
    """Test multiple close/reopen cycles with clear markers."""
    print(f"\n=== Testing {cycles} Close/Reopen Cycles on {port} ===")
    
    for cycle in range(1, cycles + 1):
        print(f"\n##### RESET {cycle} ##### - Opening connection...")
        try:
            # Open
            ser = serial.Serial(port, baud, timeout=1)
            print(f"   ✅ Connected: DTR={ser.dtr}, RTS={ser.rts}")
            
            # Clear any existing data first
            time.sleep(0.1)
            if ser.in_waiting > 0:
                existing = ser.read(ser.in_waiting)
                print(f"   🧹 Cleared {len(existing)} existing bytes")
            
            # Wait and check for data (boot messages)
            print(f"   ⏱️ Waiting 6 seconds for boot messages...")
            time.sleep(6.0)
            
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"   🔄 RESET {cycle} - BOOT DATA RECEIVED!")
                inspect_received_data(data, f"Reset {cycle} boot data")
            else:
                print(f"   📭 RESET {cycle} - No boot data received")
            
            # Send a test command to verify device is responsive
            print(f"   📤 Sending test command...")
            ser.write(b"q")
            ser.flush()
            time.sleep(2.0)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"   📥 Device responsive: {len(response)} bytes")
            else:
                print(f"   📭 No response to test command")
            
            # Close
            print(f"##### RESET {cycle} ##### - Closing connection...")
            ser.close()
            print(f"   ✅ Connection closed")
            
            print(f"   ⏱️ Waiting 8 seconds before next cycle...")
            time.sleep(8.0)
            
        except Exception as e:
            print(f"   ❌ RESET {cycle} error: {e}")

def test_multiple_close_reopen_cycles_no_reset(port: str, baud: int = 921600, cycles: int = 3):
    """Test multiple close/reopen cycles with DTR/RTS disabled to prevent resets."""
    print(f"\n=== Testing {cycles} Close/Reopen Cycles with NO-RESET (DTR/RTS=False) ===")
    
    for cycle in range(1, cycles + 1):
        print(f"\n##### NO-RESET CYCLE {cycle} ##### - Opening connection...")
        try:
            # Open with explicit DTR/RTS control
            ser = serial.Serial()
            ser.port = port
            ser.baudrate = baud
            ser.timeout = 1
            
            # Set DTR/RTS to False BEFORE opening to prevent reset
            ser.dtr = False  # Don't touch GPIO0
            ser.rts = False  # Don't touch EN/RESET
            
            # Now open the port
            ser.open()
            print(f"   ✅ Connected with NO-RESET: DTR={ser.dtr}, RTS={ser.rts}")
            
            # Clear any existing data first
            time.sleep(0.1)
            if ser.in_waiting > 0:
                existing = ser.read(ser.in_waiting)
                print(f"   🧹 Cleared {len(existing)} existing bytes")
            
            # Wait and check for data (should be no boot messages if reset prevented)
            print(f"   ⏱️ Waiting 6 seconds to check for boot messages...")
            time.sleep(6.0)
            
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                print(f"   ❌ UNEXPECTED: Boot data received despite DTR/RTS=False!")
                inspect_received_data(data, f"Cycle {cycle} unexpected data")
            else:
                print(f"   ✅ NO-RESET CYCLE {cycle} - No boot data (reset prevented!)")
            
            # Send a test command to verify device is responsive
            print(f"   📤 Sending test command...")
            ser.write(b"q")
            ser.flush()
            time.sleep(2.0)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"   📥 Device responsive: {len(response)} bytes")
            else:
                print(f"   📭 No response to test command")
            
            # Close
            print(f"##### NO-RESET CYCLE {cycle} ##### - Closing connection...")
            ser.close()
            print(f"   ✅ Connection closed")
            
            print(f"   ⏱️ Waiting 8 seconds before next cycle...")
            time.sleep(8.0)
            
        except Exception as e:
            print(f"   ❌ NO-RESET CYCLE {cycle} error: {e}")

def main():
    print("🔍 Minimal Serial Reset Test - Data Inspector")
    print("=" * 60)
    
    # Find device
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Testing on {port}")
    
    # Test 1 cycle with NO-RESET (DTR/RTS=False)
    test_multiple_close_reopen_cycles_no_reset(port, cycles=1)
    
    # Test 3 cycles with RESET (DTR/RTS=True, default behavior)
    test_multiple_close_reopen_cycles(port, cycles=3)

if __name__ == "__main__":
    main()