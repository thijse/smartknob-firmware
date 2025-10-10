#!/usr/bin/env python3
"""
SmartKnob Reset Test

Dedicated test to verify reset functionality works correctly.
"""

import sys
import os
import logging
import anyio
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartknob.protocol import SmartKnobConnection, reset_connection
from smartknob.connection import find_smartknob_ports

# Enable INFO logging to see what happens
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_standalone_reset(port: str):
    """Test the standalone reset_connection function."""
    print("\n=== Testing Standalone Reset ===")
    print(f"Calling reset_connection('{port}')")
    
    success = await anyio.to_thread.run_sync(lambda: reset_connection(port))
    
    if success:
        print("✅ Standalone reset reported success")
    else:
        print("❌ Standalone reset reported failure")
    
    return success

async def test_integrated_reset(port: str):
    """Test the integrated reset via SmartKnobConnection."""
    print("\n=== Testing Integrated Reset ===")
    
    # First establish a connection
    connection = SmartKnobConnection(port)
    
    try:
        print("Establishing connection...")
        success = await connection.start()
        if not success:
            print("❌ Failed to establish connection")
            return False
        
        print("✅ Connection established")
        
        # Now test the integrated reset
        print("Calling connection.reset_device()...")
        reset_success = await connection.reset_device()
        
        if reset_success:
            print("✅ Integrated reset reported success")
        else:
            print("❌ Integrated reset reported failure")
        
        return reset_success
        
    except Exception as e:
        print(f"❌ Exception during integrated reset test: {e}")
        return False
    finally:
        await connection.stop()

async def test_firmware_boot_detection(port: str):
    """Test if we can detect firmware boot messages after reset."""
    print("\n=== Testing Firmware Boot Detection ===")
    
    try:
        connection = SmartKnobConnection(port)
        
        # Set up message monitoring
        boot_messages = []
        def capture_messages(msg):
            boot_messages.append(msg)
            # Look for typical boot messages
            if hasattr(msg, 'log') and msg.log:
                log_msg = msg.log.msg
                if any(keyword in log_msg.lower() for keyword in ['boot', 'start', 'init', 'ready']):
                    print(f"🔍 Boot message: {log_msg}")
        
        connection.set_message_callback(capture_messages)
        
        print("Connecting and resetting...")
        await connection.start()
        
        # Clear any existing messages
        boot_messages.clear()
        
        # Perform reset
        reset_success = await connection.reset_device()
        
        if reset_success:
            print("Reset completed, monitoring for boot messages...")
            
            # Monitor for a few seconds after reset
            await anyio.sleep(3.0)
            
            print(f"Captured {len(boot_messages)} messages after reset")
            
            # Check if we got any messages that suggest the device rebooted
            if boot_messages:
                print("✅ Received messages after reset - device appears to have rebooted")
                return True
            else:
                print("❌ No messages received after reset - reset may not be working")
                return False
        else:
            print("❌ Reset function reported failure")
            return False
            
    except Exception as e:
        print(f"❌ Exception during boot detection test: {e}")
        return False
    finally:
        await connection.stop()

async def main():
    print("🔍 SmartKnob Reset Test")
    print("=" * 50)
    
    # Find device
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Testing reset on {port}")
    
    # Test 1: Standalone reset
    standalone_result = await test_standalone_reset(port)
    
    # Wait between tests
    await anyio.sleep(2.0)
    
    # Test 2: Integrated reset
    integrated_result = await test_integrated_reset(port)
    
    # Wait between tests
    await anyio.sleep(2.0)
    
    # Test 3: Boot detection
    boot_result = await test_firmware_boot_detection(port)
    
    # Results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Standalone reset:  {'✅ PASS' if standalone_result else '❌ FAIL'}")
    print(f"Integrated reset:  {'✅ PASS' if integrated_result else '❌ FAIL'}")
    print(f"Boot detection:    {'✅ PASS' if boot_result else '❌ FAIL'}")
    
    if all([standalone_result, integrated_result, boot_result]):
        print("\n🎉 All reset tests PASSED - reset functionality is working!")
    else:
        print("\n⚠️ Some reset tests FAILED - reset functionality needs investigation")

if __name__ == "__main__":
    anyio.run(main)