#!/usr/bin/env python3
"""
SmartKnob Protocol Audit Test

This test validates that the COBS+CRC32+Protobuf protocol stack is working correctly.
It captures data from the SmartKnob device and analyzes the protocol layers.

Expected Results (based on verified working implementation):
- COBS decoding: 100% success
- CRC32 validation: 100% success  
- Protobuf parsing: 100% success
- Message types: Primarily 'log' messages
"""

import sys
import os
import time
import struct
import logging
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serial
from cobs import cobs
import zlib
from smartknob.proto_gen import smartknob_pb2
from smartknob.connection import find_smartknob_ports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROTOBUF_PROTOCOL_VERSION = 1

def crc32_le(data: bytes) -> int:
    """Calculate CRC32 checksum (little-endian)."""
    return zlib.crc32(data) & 0xFFFFFFFF

def audit_protocol(port: str, baud: int = 921600, duration: float = 5.0) -> Dict[str, Any]:
    """
    Audit the SmartKnob protocol by capturing and analyzing data.
    
    Args:
        port: Serial port name
        baud: Baud rate
        duration: Capture duration in seconds
        
    Returns:
        Dictionary with audit results
    """
    logger.info(f"Starting protocol audit on {port} at {baud} baud for {duration}s")
    
    try:
        # Open serial port
        ser = serial.Serial(port=port, baudrate=baud, timeout=0)
        logger.info(f"Opened {port}")
        
        # Send 'q' to switch to protobuf mode
        ser.write(b"q")
        ser.flush()
        time.sleep(0.2)
        logger.info("Sent 'q' command to switch to protobuf mode")
        
        # Capture data
        start_time = time.time()
        buffer = bytearray()
        
        while time.time() - start_time < duration:
            if ser.in_waiting > 0:
                buffer.extend(ser.read(ser.in_waiting))
            else:
                time.sleep(0.001)
        
        ser.close()
        logger.info(f"Captured {len(buffer)} bytes")
        
        # Split into frames by 0x00 delimiter
        frames = []
        start_idx = 0
        for i, byte in enumerate(buffer):
            if byte == 0:
                frame = bytes(buffer[start_idx:i])
                if frame:  # Skip empty frames
                    frames.append(frame)
                start_idx = i + 1
        
        logger.info(f"Found {len(frames)} frames")
        
        # Analyze frames
        results = {
            'total_frames': len(frames),
            'cobs_decoded': 0,
            'crc_valid': 0,
            'protobuf_parsed': 0,
            'message_types': {},
            'protocol_versions': {},
            'errors': []
        }
        
        for i, frame in enumerate(frames):
            try:
                # Try COBS decoding
                decoded = cobs.decode(frame)
                results['cobs_decoded'] += 1
                
                if len(decoded) > 4:
                    # Split payload and CRC32
                    payload = decoded[:-4]
                    received_crc = struct.unpack('<I', decoded[-4:])[0]
                    calculated_crc = crc32_le(payload)
                    
                    if received_crc == calculated_crc:
                        results['crc_valid'] += 1
                        
                        # Try protobuf parsing
                        try:
                            msg = smartknob_pb2.FromSmartKnob()
                            msg.ParseFromString(payload)
                            results['protobuf_parsed'] += 1
                            
                            # Track protocol version
                            version = msg.protocol_version
                            results['protocol_versions'][version] = results['protocol_versions'].get(version, 0) + 1
                            
                            # Track message type
                            msg_type = msg.WhichOneof("payload")
                            results['message_types'][msg_type] = results['message_types'].get(msg_type, 0) + 1
                            
                        except Exception as e:
                            results['errors'].append(f"Frame {i}: Protobuf parse error: {e}")
                    else:
                        results['errors'].append(f"Frame {i}: CRC32 mismatch")
                else:
                    results['errors'].append(f"Frame {i}: Decoded frame too short")
                    
            except Exception as e:
                results['errors'].append(f"Frame {i}: COBS decode error: {e}")
        
        return results
        
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        return {'error': str(e)}

def print_audit_results(results: Dict[str, Any]):
    """Print formatted audit results."""
    if 'error' in results:
        print(f"❌ Audit failed: {results['error']}")
        return
    
    total = results['total_frames']
    
    def pct(count: int) -> str:
        return f"{count} ({100.0 * count / total:.1f}%)" if total > 0 else "0 (0.0%)"
    
    print("=" * 60)
    print("SMARTKNOB PROTOCOL AUDIT RESULTS")
    print("=" * 60)
    print(f"Total frames captured: {total}")
    print(f"COBS decoded:          {pct(results['cobs_decoded'])}")
    print(f"CRC32 valid:           {pct(results['crc_valid'])}")
    print(f"Protobuf parsed:       {pct(results['protobuf_parsed'])}")
    
    if results['message_types']:
        print(f"Message types:         {results['message_types']}")
    
    if results['protocol_versions']:
        print(f"Protocol versions:     {results['protocol_versions']}")
    
    # Determine overall status
    if total == 0:
        print("\n❌ STATUS: No data captured")
    elif (results['cobs_decoded'] == total and 
          results['crc_valid'] == total and 
          results['protobuf_parsed'] == total):
        print("\n✅ STATUS: Protocol stack working perfectly!")
        print("   All layers (COBS + CRC32 + Protobuf) are functioning correctly.")
    else:
        print("\n⚠️  STATUS: Protocol issues detected")
        if results['errors']:
            print("   Errors:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"     - {error}")
            if len(results['errors']) > 5:
                print(f"     ... and {len(results['errors']) - 5} more errors")
    
    print("=" * 60)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartKnob Protocol Audit")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("--baud", type=int, default=921600, help="Baud rate")
    parser.add_argument("--duration", type=float, default=5.0, help="Capture duration (seconds)")
    parser.add_argument("--validate", action="store_true", help="Use protocol validation for detection")
    
    args = parser.parse_args()
    
    # Determine port to test
    if args.port:
        port = args.port
        print(f"Using specified port: {port}")
    else:
        print("🔍 Auto-detecting SmartKnob device...")
        ports = find_smartknob_ports(validate_protocol=args.validate)
        if not ports:
            print("❌ No SmartKnob devices found")
            print("💡 Try: python tests/test_protocol_audit.py --port <PORT>")
            sys.exit(1)
        port = ports[0]
        print(f"✅ Auto-detected SmartKnob: {port}")
        
        if len(ports) > 1:
            print(f"ℹ️  Found {len(ports)} devices, using first one: {port}")
    
    results = audit_protocol(port, args.baud, args.duration)
    print_audit_results(results)
    
    # Exit with appropriate code
    if 'error' in results:
        sys.exit(1)
    elif (results['total_frames'] > 0 and 
          results['cobs_decoded'] == results['total_frames'] and
          results['crc_valid'] == results['total_frames'] and
          results['protobuf_parsed'] == results['total_frames']):
        sys.exit(0)  # Perfect success
    else:
        sys.exit(1)  # Issues detected

if __name__ == "__main__":
    main()
