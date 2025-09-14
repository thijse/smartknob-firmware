#!/usr/bin/env python3
"""
Test the enhanced SmartKnob library with optional reset functionality.

This script demonstrates the new auto_reset parameter in both SmartKnobConnection
and SmartKnobProtocol classes.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add the SmartKnob library to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "smartknob-connection2"))

from smartknob import SmartKnobConnection
from smartknob.connection import find_smartknob_ports

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_connection_without_reset():
    """Test connection without auto-reset (default behavior)."""
    logger.info("=== Testing connection WITHOUT auto-reset ===")
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        logger.error("No SmartKnob devices found")
        return False
    
    port = ports[0]
    logger.info(f"Using port: {port}")
    
    # Test connection without reset (default)
    connection = SmartKnobConnection(port)
    
    try:
        success = await connection.start()
        if success:
            logger.info("✅ Connection without reset successful")
            await asyncio.sleep(1)
            await connection.stop()
            return True
        else:
            logger.error("❌ Connection without reset failed")
            return False
    except Exception as e:
        logger.error(f"❌ Exception during connection without reset: {e}")
        await connection.stop()
        return False

async def test_connection_with_reset():
    """Test connection with auto-reset enabled."""
    logger.info("=== Testing connection WITH auto-reset ===")
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        logger.error("No SmartKnob devices found")
        return False
    
    port = ports[0]
    logger.info(f"Using port: {port}")
    
    # Test connection with reset enabled
    connection = SmartKnobConnection(port, auto_reset=True)
    
    try:
        success = await connection.start()
        if success:
            logger.info("✅ Connection with reset successful")
            await asyncio.sleep(1)
            await connection.stop()
            return True
        else:
            logger.error("❌ Connection with reset failed")
            return False
    except Exception as e:
        logger.error(f"❌ Exception during connection with reset: {e}")
        await connection.stop()
        return False

async def main():
    """Main test function."""
    logger.info("Testing enhanced SmartKnob library with reset functionality")
    
    # Test both connection modes
    test1_success = await test_connection_without_reset()
    await asyncio.sleep(2)  # Wait between tests
    
    test2_success = await test_connection_with_reset()
    
    # Summary
    logger.info("=== Test Results ===")
    logger.info(f"Connection without reset: {'✅ PASS' if test1_success else '❌ FAIL'}")
    logger.info(f"Connection with reset: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        logger.info("🎉 All tests passed! Library enhancement successful.")
        return True
    else:
        logger.error("❌ Some tests failed. Library may need debugging.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        sys.exit(1)
