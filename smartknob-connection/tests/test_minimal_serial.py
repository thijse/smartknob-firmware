#!/usr/bin/env python3
"""
Minimal Serial Test - No DTR/RTS manipulation

Test what happens with basic serial open/close without touching DTR/RTS.
"""

import serial
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from smartknob.connection import find_smartknob_ports

def test_minimal_serial_cycle(port: str, baud: int = 921600):
    """Test minimal serial open/close cycle."""
    print(f"=== Testing Minimal Serial Cycle on {port} ===")
    
    try:
        print("1. Opening serial port (no DTR/RTS changes)...")
        # Open serial port with minimal settings
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            timeout=1,
            # Don't touch DTR/RTS at all - let them be whatever default is
        )
        print(f"   ✅ Port opened: DTR={ser.dtr}, RTS={ser.rts}")
        
        print("2. Sending 'q' command...")
        ser.write(b"q")
        ser.flush()
        
        print("3. Reading initial response...")
        time.sleep(0.5)
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"   📥 Received {len(data)} bytes")
        else:
            print("   📭 No data received")
        
        print("4. Closing connection...")
        ser.close()
        print("   ✅ Connection closed")
        
        print("5. Waiting 2 seconds...")
        time.sleep(2.0)
        
        print("6. Reopening connection...")
        ser = serial.Serial(
            port=port,
            baudrate=baud,
            timeout=1,
        )
        print(f"   ✅ Port reopened: DTR={ser.dtr}, RTS={ser.rts}")
        
        print("7. Sending 'q' command again...")
        ser.write(b"q")
        ser.flush()
        
        print("8. Reading response after reopen...")
        time.sleep(0.5)
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"   📥 Received {len(data)} bytes")
        else:
            print("   📭 No data received")
        
        print("9. Final close...")
        ser.close()
        print("   ✅ Test completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_explicit_dtr_rts_control(port: str, baud: int = 921600):
    """Test with explicit DTR/RTS control."""
    print(f"\n=== Testing Explicit DTR/RTS Control on {port} ===")
    
    try:
        print("1. Opening serial port...")
        ser = serial.Serial()
        ser.port = port
        ser.baudrate = baud
        ser.timeout = 1
        
        print("2. Setting DTR/RTS before open...")
        ser.dtr = False  # Explicitly set DTR low
        ser.rts = False  # Explicitly set RTS low
        
        print("3. Opening port with explicit settings...")
        ser.open()
        print(f"   ✅ Port opened: DTR={ser.dtr}, RTS={ser.rts}")
        
        print("4. Sending 'q' command...")
        ser.write(b"q")
        ser.flush()
        
        print("5. Reading response...")
        time.sleep(0.5)
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"   📥 Received {len(data)} bytes")
        else:
            print("   📭 No data received")
        
        print("6. Closing with DTR/RTS maintained...")
        ser.close()
        print("   ✅ Test completed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_dtr_rts_changes_on_close(port: str, baud: int = 921600):
    """Test what happens when DTR/RTS change during close."""
    print(f"\n=== Testing DTR/RTS Changes on Close on {port} ===")
    
    try:
        print("1. Opening serial port...")
        ser = serial.Serial(port, baud, timeout=1)
        original_dtr = ser.dtr
        original_rts = ser.rts
        print(f"   ✅ Port opened: DTR={original_dtr}, RTS={original_rts}")
        
        print("2. Sending 'q' command...")
        ser.write(b"q")
        ser.flush()
        
        print("3. Changing DTR/RTS before close...")
        ser.dtr = not original_dtr  # Toggle DTR
        ser.rts = not original_rts  # Toggle RTS  
        print(f"   🔄 Changed to: DTR={ser.dtr}, RTS={ser.rts}")
        
        print("4. Closing connection...")
        ser.close()
        print("   ✅ Connection closed")
        
        print("5. Waiting to see if device resets...")
        time.sleep(3.0)
        
        print("6. Reopening to check if device reset...")
        ser = serial.Serial(port, baud, timeout=1)
        ser.write(b"q")
        ser.flush()
        
        time.sleep(0.5)
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(f"   📥 Received {len(data)} bytes after potential reset")
        else:
            print("   📭 No data received after potential reset")
            
        ser.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🔍 Minimal Serial Reset Test")
    print("=" * 60)
    
    # Find device
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Testing on {port}")
    
    # Test 1: Minimal serial cycle
    result1 = test_minimal_serial_cycle(port)
    
    # Test 2: Explicit DTR/RTS control
    result2 = test_explicit_dtr_rts_control(port)
    
    # Test 3: DTR/RTS changes on close
    result3 = test_dtr_rts_changes_on_close(port)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"Minimal cycle:     {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Explicit control:  {'✅ PASS' if result2 else '❌ FAIL'}")  
    print(f"DTR/RTS on close:  {'✅ PASS' if result3 else '❌ FAIL'}")

if __name__ == "__main__":
    main()