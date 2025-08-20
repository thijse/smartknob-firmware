#!/usr/bin/env python3
"""
SmartKnob Basic Monitoring Example

This example demonstrates how to connect to a SmartKnob device and monitor
incoming messages using the clean, consolidated library.

Expected behavior:
- Connects to SmartKnob device
- Receives continuous log messages (sensor data, system info)
- Displays message statistics
- Gracefully handles disconnection
"""

import sys
import os
import time
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartknob import SmartKnobConnection

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def main():
    """Main monitoring function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartKnob Basic Monitoring")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("--baud", type=int, default=921600, help="Baud rate")
    parser.add_argument("--duration", type=float, default=30.0, help="Monitoring duration (seconds)")
    parser.add_argument("--validate", action="store_true", help="Use protocol validation for detection")
    
    args = parser.parse_args()
    
    # Determine port to use
    if args.port:
        port = args.port
        print(f"Using specified port: {port}")
    else:
        print("🔍 Auto-detecting SmartKnob device...")
        from smartknob.connection import find_smartknob_ports
        ports = find_smartknob_ports(validate_protocol=args.validate)
        if not ports:
            print("❌ No SmartKnob devices found")
            print("💡 Try: python examples/basic_monitoring.py --port <PORT>")
            return 1
        port = ports[0]
        print(f"✅ Auto-detected SmartKnob: {port}")
        
        if len(ports) > 1:
            print(f"ℹ️  Found {len(ports)} devices, using first one: {port}")
    
    # Message statistics
    message_count = 0
    message_types = {}
    start_time = time.time()
    
    def on_message(msg):
        """Handle incoming messages."""
        nonlocal message_count, message_types
        
        message_count += 1
        msg_type = msg.WhichOneof("payload")
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        # Display log messages
        if msg_type == 'log':
            level = msg.log.level
            origin = msg.log.origin
            message = msg.log.msg
            print(f"[{origin}] {message}")
        elif msg_type == 'knob':
            print(f"🎛️  Knob info: mac={msg.knob.mac_address}, ip={msg.knob.ip_address}")
        elif msg_type == 'ack':
            print(f"✅ ACK: nonce={msg.ack.nonce}")
        else:
            print(f"📨 {msg_type}: {msg}")
    
    print(f"Connecting to SmartKnob on {port} at {args.baud} baud...")
    
    try:
        # Connect to SmartKnob
        with SmartKnobConnection(port, args.baud) as knob:
            print("✅ Connected successfully!")
            
            # Set up message callback
            knob.set_message_callback(on_message)
            
            # Send a test command (firmware currently doesn't respond)
            print("🚀 Sending GET_KNOB_INFO command...")
            knob.send_command(0)  # GET_KNOB_INFO
            
            # Monitor for specified duration
            print(f"📡 Monitoring for {args.duration} seconds...")
            print("=" * 60)
            
            end_time = time.time() + args.duration
            last_stats_time = time.time()
            
            while time.time() < end_time:
                # Display periodic statistics
                if time.time() - last_stats_time >= 5.0:
                    elapsed = time.time() - start_time
                    rate = message_count / elapsed if elapsed > 0 else 0
                    
                    print(f"\n📊 Statistics (after {elapsed:.1f}s):")
                    print(f"   Messages received: {message_count} ({rate:.1f}/sec)")
                    print(f"   Message types: {message_types}")
                    
                    # Get protocol statistics
                    stats = knob.get_stats()
                    print(f"   Protocol stats: {stats}")
                    print("=" * 60)
                    
                    last_stats_time = time.time()
                
                time.sleep(0.1)
            
            # Final statistics
            elapsed = time.time() - start_time
            rate = message_count / elapsed if elapsed > 0 else 0
            
            print(f"\n🏁 Final Results:")
            print(f"   Total time: {elapsed:.1f}s")
            print(f"   Messages received: {message_count} ({rate:.1f}/sec)")
            print(f"   Message types: {message_types}")
            
            # Final protocol statistics
            stats = knob.get_stats()
            print(f"   Protocol stats: {stats}")
            
            # Analysis
            if message_count > 0:
                print(f"\n✅ SUCCESS: Received {message_count} messages")
                if 'log' in message_types:
                    print(f"   📝 Log messages: {message_types['log']} (sensor data, system info)")
                if 'knob' in message_types:
                    print(f"   🎛️  Knob responses: {message_types['knob']} (command responses)")
                else:
                    print(f"   ⚠️  No knob responses (firmware issue - commands not responded to)")
            else:
                print(f"\n❌ No messages received - check connection and firmware")
    
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
