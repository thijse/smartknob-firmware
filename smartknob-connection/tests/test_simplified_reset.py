#!/usr/bin/env python3
"""
Test the simplified reset functionality with reset_at_close parameter.
Interactive version to confirm when resets actually happen.
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartknob.connection import find_smartknob_ports
from smartknob.protocol import SmartKnobConnection

def ask_user_reset_confirmation(expected_reset: bool, moment: str) -> bool:
    """Ask user if they observed a reset at this moment."""
    expected_text = "EXPECTED" if expected_reset else "NOT expected"
    print(f"\n🔍 RESET CHECK - {moment}")
    print(f"   Expected reset: {expected_text}")
    
    while True:
        response = input("   Did you see the device reset just now? (y/n/skip): ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        elif response in ['s', 'skip']:
            return None  # Skip this check
        else:
            print("   Please enter 'y' (yes), 'n' (no), or 's' (skip)")

def log_reset_result(expected: bool, actual: bool, moment: str):
    """Log the result of a reset check."""
    if actual is None:
        print(f"   ⏭️  SKIPPED: {moment}")
        return
    
    if expected == actual:
        status = "✅ MATCH"
    else:
        status = "❌ MISMATCH"
    
    print(f"   {status}: {moment}")
    print(f"      Expected: {'Reset' if expected else 'No reset'}")
    print(f"      Actual:   {'Reset' if actual else 'No reset'}")

async def test_reset_at_close_functionality():
    """Test the new reset_at_close functionality with user confirmation."""
    
    # Find device
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Testing on {port}")
    print("\n📋 Instructions: Watch your SmartKnob device and answer when asked if you saw it reset.")
    print("   A reset typically shows: boot messages, LED patterns, or brief disconnection.")
    
    results = []
    
    print("\n=== Test 1: Connection without reset_at_close ===")
    try:
        print("🔌 Opening connection with reset_at_close=False...")
        async with SmartKnobConnection(port, reset_at_close=False) as conn:
            # Check #1: After connection open (should NOT reset)
            actual = ask_user_reset_confirmation(False, "after opening connection (reset_at_close=False)")
            log_reset_result(False, actual, "Connection open with reset_at_close=False")
            if actual is not None:
                results.append(("Open reset_at_close=False", False, actual))
            
            print("✅ Connected without reset_at_close")
            print("⏱️ Waiting 5 seconds...")
            await asyncio.sleep(5.0)
            
        # Check #2: After connection close (should NOT reset)
        actual = ask_user_reset_confirmation(False, "after closing connection (reset_at_close=False)")
        log_reset_result(False, actual, "Connection close with reset_at_close=False") 
        if actual is not None:
            results.append(("Close reset_at_close=False", False, actual))
        
        print("⏱️ Waiting 3 seconds...")
        await asyncio.sleep(3.0)
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    print("\n=== Test 2: Connection with reset_at_close=True ===")
    try:
        print("🔌 Opening connection with reset_at_close=True...")
        async with SmartKnobConnection(port, reset_at_close=True) as conn:
            # Check #3: After connection open (SHOULD reset)  
            actual = ask_user_reset_confirmation(True, "after opening connection (reset_at_close=True)")
            log_reset_result(True, actual, "Connection open with reset_at_close=True")
            if actual is not None:
                results.append(("Open reset_at_close=True", True, actual))
            
            print("✅ Connected with reset_at_close=True")
            print("⏱️ Waiting 5 seconds...")
            await asyncio.sleep(5.0)
            
        # Check #4: After connection close (SHOULD reset)
        actual = ask_user_reset_confirmation(True, "after closing connection (reset_at_close=True)")
        log_reset_result(True, actual, "Connection close with reset_at_close=True")
        if actual is not None:
            results.append(("Close reset_at_close=True", True, actual))
        
        print("⏱️ Waiting 3 seconds...")
        await asyncio.sleep(3.0)
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    print("\n=== Test 3: ResetAtClose() method ===")
    try:
        conn = SmartKnobConnection(port, reset_at_close=False)
        print("🔌 Opening connection...")
        await conn.start()
        
        # Check #5: After initial connection (should NOT reset)
        actual = ask_user_reset_confirmation(False, "after initial connection")
        log_reset_result(False, actual, "Initial connection for ResetAtClose test")
        if actual is not None:
            results.append(("ResetAtClose initial", False, actual))
        
        print("✅ Connected with reset_at_close=False initially")
        print("⏱️ Waiting 3 seconds...")
        await asyncio.sleep(3.0)
        
        # Test ResetAtClose method
        print("🔧 Calling conn.ResetAtClose(True)...")
        conn.ResetAtClose(True)
        print("✅ Called ResetAtClose(True)")
        print("⏱️ Waiting 3 seconds...")
        await asyncio.sleep(3.0)
        
        print("🔌 Closing connection (should now reset due to ResetAtClose(True))...")
        await conn.stop()
        
        # Check #6: After close with ResetAtClose(True) (SHOULD reset)
        actual = ask_user_reset_confirmation(True, "after closing with ResetAtClose(True)")
        log_reset_result(True, actual, "Close after ResetAtClose(True)")
        if actual is not None:
            results.append(("ResetAtClose(True) close", True, actual))
        
        print("⏱️ Waiting 3 seconds...")
        await asyncio.sleep(3.0)
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    print("\n=== Test 4: Standalone reset ===")
    try:
        conn = SmartKnobConnection(port)
        print("🔄 Performing standalone reset...")
        success = await conn.reset_device()
        
        # Check #7: After standalone reset (SHOULD reset)
        actual = ask_user_reset_confirmation(True, "after standalone reset_device() call")
        log_reset_result(True, actual, "Standalone reset_device()")
        if actual is not None:
            results.append(("Standalone reset", True, actual))
        
        print(f"✅ Standalone reset: {'SUCCESS' if success else 'FAILED'}")
        print("⏱️ Waiting 3 seconds...")
        await asyncio.sleep(3.0)
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
    
    print("\n=== Test 5: Reset while connected ===")
    try:
        async with SmartKnobConnection(port, reset_at_close=False) as conn:
            print("✅ Connected")
            print("⏱️ Waiting 3 seconds before reset...")
            await asyncio.sleep(3.0)
            
            print("🔄 Performing reset while connected...")
            success = await conn.reset_device()
            
            # Check #8: After reset while connected (SHOULD reset)
            actual = ask_user_reset_confirmation(True, "after reset_device() while connected")
            log_reset_result(True, actual, "Reset while connected")
            if actual is not None:
                results.append(("Reset while connected", True, actual))
            
            print(f"✅ Reset while connected: {'SUCCESS' if success else 'FAILED'}")
            print(f"   Still connected: {conn.connected}")
            print("⏱️ Waiting 3 seconds...")
            await asyncio.sleep(3.0)
    except Exception as e:
        print(f"❌ Test 5 failed: {e}")
    
    # Summary of results
    print("\n" + "="*60)
    print("📊 RESET PATTERN SUMMARY")
    print("="*60)
    
    matches = 0
    total = 0
    
    for test_name, expected, actual in results:
        total += 1
        if expected == actual:
            matches += 1
            status = "✅"
        else:
            status = "❌"
        
        expected_text = "Reset" if expected else "No reset"
        actual_text = "Reset" if actual else "No reset"
        print(f"{status} {test_name}: Expected {expected_text}, Got {actual_text}")
    
    print(f"\n📈 Accuracy: {matches}/{total} ({100*matches/total:.1f}% match)" if total > 0 else "\n📈 No data collected")
    print("\n✅ Interactive reset pattern analysis completed!")

async def main():
    print("🔍 Simplified Reset Functionality Test")
    print("=" * 60)
    await test_reset_at_close_functionality()

if __name__ == "__main__":
    asyncio.run(main())