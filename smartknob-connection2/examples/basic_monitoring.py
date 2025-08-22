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
import anyio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from smartknob.protocol import SmartKnobConnection
from smartknob.connection import find_smartknob_ports

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
    parser.add_argument("--logfile", help="Log file path (auto-generated if not specified)")
    
    args = parser.parse_args()
    
    # Set up log file
    if args.logfile:
        log_file_path = args.logfile
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = f"smartknob_monitor_{timestamp}.log"
    
    # Open log file
    log_file = open(log_file_path, 'w', encoding='utf-8')
    print(f"📝 Logging to file: {log_file_path}")
    
    def dual_print(message):
        """Print to both console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] {message}"
        print(message)  # Console
        log_file.write(log_line + "\n")  # File
        log_file.flush()  # Ensure immediate write
    
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
    should_stop = False
    
    def on_message(msg):
        """Handle incoming messages."""
        nonlocal message_count, message_types, should_stop
        
        # Check if we should stop (duration exceeded)
        elapsed = time.time() - start_time
        if elapsed >= args.duration:
            should_stop = True
            return
        
        message_count += 1
        msg_type = msg.WhichOneof("payload")
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        # Display log messages
        if msg_type == 'log':
            level = msg.log.level
            origin = msg.log.origin
            message = msg.log.msg
            dual_print(f"[{origin}] {message}")
        elif msg_type == 'knob':
            dual_print(f"🎛️  Knob info: mac={msg.knob.mac_address}, ip={msg.knob.ip_address}")
        elif msg_type == 'ack':
            dual_print(f"✅ ACK: nonce={msg.ack.nonce}")
        else:
            dual_print(f"📨 {msg_type}: {msg}")
        
        # Small sleep to allow Ctrl-C handling
        time.sleep(0.001)
    
    # Run async main function
    try:
        return anyio.run(async_main, args, dual_print, port, message_count, message_types, start_time, should_stop, log_file_path)
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user (Ctrl-C)")
        log_file.close()
        print(f"📁 Log saved to: {log_file_path}")
        return 0


async def async_main(args, dual_print, port, message_count, message_types, start_time, should_stop, log_file_path):
    """Async main function using anyio."""
    
    def on_message(msg):
        """Handle incoming messages."""
        nonlocal message_count, message_types, should_stop
        
        # Check if we should stop (duration exceeded) - removed, handled in main loop
        
        message_count += 1
        msg_type = msg.WhichOneof("payload")
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        # Display log messages
        if msg_type == 'log':
            level = msg.log.level
            origin = msg.log.origin
            message = msg.log.msg
            dual_print(f"[{origin}] {message}")
        elif msg_type == 'knob':
            dual_print(f"🎛️  Knob info: mac={msg.knob.mac_address}, ip={msg.knob.ip_address}")
        elif msg_type == 'ack':
            dual_print(f"✅ ACK: nonce={msg.ack.nonce}")
        else:
            dual_print(f"📨 {msg_type}: {msg}")
    
    dual_print(f"Connecting to SmartKnob on {port} at {args.baud} baud...")
    
    start_loop_time = time.time()  # Initialize early for proper scoping
    
    try:
        # Create async connection
        async with SmartKnobConnection(port, args.baud) as knob:
            dual_print("✅ Connected successfully!")
            
            # Set up message callback
            knob.set_message_callback(on_message)
            
            # Send a test command (firmware currently doesn't respond)
            dual_print("🚀 Sending GET_KNOB_INFO command...")
            await knob.send_command(0)  # GET_KNOB_INFO
            
            # Monitor for specified duration
            dual_print(f"📡 Monitoring for {args.duration} seconds...")
            dual_print("=" * 60)
            
            start_loop_time = time.time()  # Reset for actual monitoring
            
            # Start read loop in background with proper exception handling
            try:
                async with anyio.create_task_group() as tg:
                    # Start protocol read loop
                    tg.start_soon(knob.protocol.read_loop)
                    
                    # Main timeout loop - proper timeout handling in main thread
                    while True:
                        current_time = time.time()
                        elapsed = current_time - start_loop_time
                        
                        # Check timeout
                        if elapsed >= args.duration:
                            dual_print(f"\n⏱️  Duration timeout reached ({args.duration}s)")
                            # Cancel the task group cleanly
                            tg.cancel_scope.cancel()
                            break
                        
                        # Responsive sleep - allows clean cancellation
                        await anyio.sleep(0.1)
                        
            except* Exception as eg:
                # Handle all task group exceptions properly
                import serial
                
                for exc in eg.exceptions:
                    # Check for common cancellation exceptions by type name and message
                    exc_type_name = type(exc).__name__
                    exc_message = str(exc).lower()
                    
                    if (exc_type_name in ['CancelledError', 'Cancelled'] or 
                        'cancel' in exc_message or 
                        'cancelled' in exc_message):
                        # Silently absorb expected cancellation from our timeout
                        pass
                    elif isinstance(exc, serial.SerialTimeoutException):
                        # Silently absorb expected serial timeouts (5-second timeout)
                        pass
                    elif "timeout" in exc_message:
                        # Log other timeout errors at info level
                        dual_print(f"ℹ️  Timeout: {exc}")
                    else:
                        # Log unexpected errors but continue gracefully
                        dual_print(f"⚠️  Background task error: {exc}")
        
        # Connection is now properly closed, show final statistics
        dual_print("\n🔌 Connection closed")
        
        # Final statistics
        elapsed = time.time() - start_loop_time
        rate = message_count / elapsed if elapsed > 0 else 0
        
        dual_print(f"\n🏁 Final Results:")
        dual_print(f"   Total time: {elapsed:.1f}s")
        dual_print(f"   Messages received: {message_count} ({rate:.1f}/sec)")
        dual_print(f"   Message types: {message_types}")
        
        # Analysis
        if message_count > 0:
            dual_print(f"\n✅ SUCCESS: Received {message_count} messages")
            if 'log' in message_types:
                dual_print(f"   📝 Log messages: {message_types['log']} (sensor data, system info)")
            if 'knob' in message_types:
                dual_print(f"   🎛️  Knob responses: {message_types['knob']} (command responses)")
            else:
                dual_print(f"   ⚠️  No knob responses (firmware issue - commands not responded to)")
        else:
            dual_print(f"\n❌ No messages received - check connection and firmware")
        
        dual_print(f"\n📁 Log saved to: {log_file_path}")
        return 0
    
    except Exception as e:
        dual_print(f"\n❌ Error: {e}")
        dual_print(f"📁 Log saved to: {log_file_path}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
