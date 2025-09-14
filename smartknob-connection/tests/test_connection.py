#!/usr/bin/env python3
"""
SmartKnob Basic Connection Test

Simple test to verify basic connectivity to SmartKnob device.
"""

import sys
import os
import time
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serial
from smartknob.connection import find_smartknob_ports, get_port_info

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def test_basic_connection(port: str = "COM9", baud: int = 921600) -> bool:
    """
    Test basic serial connection to SmartKnob.
    
    Args:
        port: Serial port name
        baud: Baud rate
        
    Returns:
        True if connection successful
    """
    logger.info(f"Testing connection to {port} at {baud} baud")
    
    try:
        # Open serial port
        ser = serial.Serial(port=port, baudrate=baud, timeout=1)
        logger.info(f"✅ Successfully opened {port}")
        
        # Send 'q' command
        ser.write(b"q")
        ser.flush()
        logger.info("Sent 'q' command")
        
        # Read some data
        time.sleep(0.5)
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            logger.info(f"✅ Received {len(data)} bytes of data")
        else:
            logger.warning("⚠️  No data received")
        
        ser.close()
        logger.info("Connection test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartKnob Basic Connection Test")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("--baud", type=int, default=921600, help="Baud rate")
    parser.add_argument("--list-ports", action="store_true", help="List available SmartKnob ports")
    parser.add_argument("--validate", action="store_true", help="Use protocol validation for detection")
    
    args = parser.parse_args()
    
    if args.list_ports:
        ports = find_smartknob_ports(validate_protocol=args.validate)
        print("SmartKnob ports found:")
        for port in ports:
            info = get_port_info(port)
            print(f"  📍 {port}")
            if info.get('description'):
                print(f"     Description: {info['description']}")
            if info.get('vid') and info.get('pid'):
                print(f"     USB ID: {info['vid']}:{info['pid']}")
        return
    
    # Determine port to test
    if args.port:
        port = args.port
        print(f"Using specified port: {port}")
    else:
        print("🔍 Auto-detecting SmartKnob device...")
        ports = find_smartknob_ports(validate_protocol=args.validate)
        if not ports:
            print("❌ No SmartKnob devices found")
            print("💡 Try: python tests/test_connection.py --list-ports")
            sys.exit(1)
        port = ports[0]
        print(f"✅ Auto-detected SmartKnob: {port}")
        
        if len(ports) > 1:
            print(f"ℹ️  Found {len(ports)} devices, using first one: {port}")
    
    # Run test
    success = test_basic_connection(port, args.baud)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
