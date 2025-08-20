#!/usr/bin/env python3
"""
SmartKnob Device Discovery Test

This test demonstrates the enhanced device discovery capabilities,
including USB VID/PID matching and protocol validation.
"""

import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartknob.connection import find_smartknob_ports, get_port_info, connect_smartknob

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def test_device_discovery():
    """Test the device discovery functionality."""
    print("=" * 60)
    print("SMARTKNOB DEVICE DISCOVERY TEST")
    print("=" * 60)
    
    # Test 1: Basic discovery (USB VID/PID + description matching)
    print("\n🔍 Test 1: Basic Device Discovery")
    print("-" * 40)
    
    basic_ports = find_smartknob_ports(validate_protocol=False)
    print(f"Found {len(basic_ports)} candidate ports: {basic_ports}")
    
    # Show detailed info for each candidate
    for port in basic_ports:
        info = get_port_info(port)
        print(f"\n📋 Port Details: {port}")
        for key, value in info.items():
            if value:
                print(f"   {key}: {value}")
    
    # Test 2: Protocol validation (slower but more reliable)
    print(f"\n🧪 Test 2: Protocol Validation")
    print("-" * 40)
    
    if basic_ports:
        print("Testing protocol validation on candidates...")
        validated_ports = find_smartknob_ports(validate_protocol=True)
        print(f"Protocol-validated ports: {validated_ports}")
        
        if validated_ports:
            print("✅ Protocol validation successful!")
        else:
            print("⚠️  No ports passed protocol validation")
    else:
        print("No candidates found for protocol validation")
    
    # Test 3: Auto-connection
    print(f"\n🔌 Test 3: Auto-Connection")
    print("-" * 40)
    
    print("Attempting auto-connection...")
    connection = connect_smartknob()
    
    if connection:
        print("✅ Auto-connection successful!")
        print(f"Connected to: {connection.port}")
        
        # Get some stats
        stats = connection.get_stats()
        print(f"Connection stats: {stats}")
        
        # Clean disconnect
        connection.disconnect()
        print("Connection closed")
    else:
        print("❌ Auto-connection failed")
    
    print("\n" + "=" * 60)
    print("DISCOVERY TEST COMPLETE")
    print("=" * 60)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartKnob Device Discovery Test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        test_device_discovery()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
