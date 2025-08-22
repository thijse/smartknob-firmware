#!/usr/bin/env python3
"""
SmartKnob Two-Way Communication Example

Enhanced version that demonstrates comprehensive communication with SmartKnob:
- Visualizes different message types with icons
- Shows detailed knob information (persistent_config, settings)
- Real-time position tracking via SmartKnobState
- Command-line filtering options
- Interactive command sending

Expected behavior:
- Connects to SmartKnob device
- Sends GET_KNOB_INFO and displays rich device data
- Requests and displays real-time knob position updates
- Provides clean, filtered output options
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
from smartknob.proto_gen import smartknob_pb2

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Message type icons for visualization
MESSAGE_ICONS = {
    'knob': '📦',
    'ack': '✅', 
    'log': '📝',
    'smartknob_state': '🎛️',
    'motor_calib_state': '⚙️',
    'strain_calib_state': '🔧'
}

def format_knob_info(knob_msg):
    """Format detailed knob information for display."""
    lines = []
    lines.append(f"📦 KNOB INFORMATION:")
    lines.append(f"   MAC Address: {knob_msg.mac_address}")
    lines.append(f"   IP Address: {knob_msg.ip_address}")
    
    # Persistent Configuration
    if knob_msg.HasField('persistent_config'):
        pc = knob_msg.persistent_config
        lines.append(f"   📋 Persistent Config (v{pc.version}):")
        
        if pc.HasField('motor'):
            motor = pc.motor
            lines.append(f"      🔧 Motor: {'✅ Calibrated' if motor.calibrated else '❌ Not Calibrated'}")
            if motor.calibrated:
                lines.append(f"         Zero Offset: {motor.zero_electrical_offset:.3f}")
                lines.append(f"         Direction: {'CW' if motor.direction_cw else 'CCW'}")
                lines.append(f"         Pole Pairs: {motor.pole_pairs}")
        
        lines.append(f"      📏 Strain Scale: {pc.strain_scale:.6f}")
    
    # Settings
    if knob_msg.HasField('settings'):
        settings = knob_msg.settings
        lines.append(f"   ⚙️ Settings (protocol v{settings.protocol_version}):")
        
        if settings.HasField('screen'):
            screen = settings.screen
            lines.append(f"      📺 Screen: Dim={screen.dim}, Bright={screen.min_bright}-{screen.max_bright}, Timeout={screen.timeout}s")
        
        if settings.HasField('led_ring'):
            led = settings.led_ring
            lines.append(f"      💡 LED Ring: {'✅ Enabled' if led.enabled else '❌ Disabled'}")
            if led.enabled:
                lines.append(f"         Brightness: {led.min_bright}-{led.max_bright}, Color: {led.color}, Timeout: {led.timeout}s")
                if led.HasField('beacon'):
                    beacon = led.beacon
                    lines.append(f"         🚨 Beacon: {'✅ Enabled' if beacon.enabled else '❌ Disabled'}")
    
    return '\n'.join(lines)

def format_state_info(state_msg):
    """Format SmartKnobState information for display."""
    lines = []
    lines.append(f"🎛️ KNOB STATE:")
    lines.append(f"   Position: {state_msg.current_position}")
    lines.append(f"   Sub-position: {state_msg.sub_position_unit:.3f}")
    lines.append(f"   Press nonce: {state_msg.press_nonce}")
    
    if state_msg.HasField('config'):
        config = state_msg.config
        lines.append(f"   📋 Active Config: '{config.id}'")
        lines.append(f"      Range: [{config.min_position}, {config.max_position}]")
        lines.append(f"      Detent strength: {config.detent_strength_unit:.2f}")
        lines.append(f"      Endstop strength: {config.endstop_strength_unit:.2f}")
        lines.append(f"      LED hue: {config.led_hue}")
    
    return '\n'.join(lines)

def main():
    """Main communication function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartKnob Two-Way Communication")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("--baud", type=int, default=921600, help="Baud rate")
    parser.add_argument("--duration", type=float, default=30.0, help="Monitoring duration (seconds)")
    parser.add_argument("--validate", action="store_true", help="Use protocol validation for detection")
    parser.add_argument("--logfile", help="Log file path (auto-generated if not specified)")
    
    # Filtering options
    parser.add_argument("--hide-logs", action="store_true", help="Hide log messages for cleaner output")
    parser.add_argument("--show-only", help="Show only specific message types (comma-separated: knob,ack,state,log)")
    parser.add_argument("--request-state", action="store_true", help="Continuously request knob state for position tracking")
    parser.add_argument("--state-interval", type=float, default=0.5, help="Interval for state requests (seconds)")
    
    args = parser.parse_args()
    
    # Parse show-only filter
    show_only = None
    if args.show_only:
        show_only = set(args.show_only.split(','))
    
    # Set up log file
    if args.logfile:
        log_file_path = args.logfile
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = f"smartknob_twoway_{timestamp}.log"
    
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
            print("💡 Try: python examples/two_way_communication.py --port <PORT>")
            return 1
        port = ports[0]
        print(f"✅ Auto-detected SmartKnob: {port}")
        
        if len(ports) > 1:
            print(f"ℹ️  Found {len(ports)} devices, using first one: {port}")
    
    # Message statistics
    message_count = 0
    message_types = {}
    start_time = time.time()
    
    def should_show_message(msg_type):
        """Check if message type should be displayed based on filters."""
        if args.hide_logs and msg_type == 'log':
            return False
        if show_only and msg_type not in show_only:
            return False
        return True
    
    def on_message(msg):
        """Handle incoming messages with enhanced display."""
        nonlocal message_count, message_types
        
        message_count += 1
        msg_type = msg.WhichOneof("payload")
        message_types[msg_type] = message_types.get(msg_type, 0) + 1
        
        # Check if we should display this message type
        if not should_show_message(msg_type):
            return
        
        # Get icon for message type
        icon = MESSAGE_ICONS.get(msg_type, '📨')
        
        # Display messages based on type
        if msg_type == 'log':
            level = msg.log.level
            origin = msg.log.origin
            message = msg.log.msg
            dual_print(f"{icon} [LOG] [{origin}] {message}")
            
        elif msg_type == 'knob':
            dual_print(format_knob_info(msg.knob))
            
        elif msg_type == 'ack':
            dual_print(f"{icon} [ACK] Command acknowledged (nonce={msg.ack.nonce})")
            
        elif msg_type == 'smartknob_state':
            dual_print(format_state_info(msg.smartknob_state))
            
        elif msg_type == 'motor_calib_state':
            dual_print(f"{icon} [MOTOR_CALIB] Calibrated: {msg.motor_calib_state.calibrated}")
            
        elif msg_type == 'strain_calib_state':
            dual_print(f"{icon} [STRAIN_CALIB] Step: {msg.strain_calib_state.step}, Scale: {msg.strain_calib_state.strain_scale:.6f}")
            
        else:
            dual_print(f"{icon} [{msg_type.upper()}] {msg}")
    
    # Run async main function
    try:
        return anyio.run(async_main, args, dual_print, port, message_count, message_types, start_time, log_file_path, on_message)
    except KeyboardInterrupt:
        print(f"\n⏹️  Communication stopped by user (Ctrl-C)")
        log_file.close()
        print(f"📁 Log saved to: {log_file_path}")
        return 0


async def async_main(args, dual_print, port, message_count, message_types, start_time, log_file_path, on_message):
    """Async main function with enhanced two-way communication."""
    
    dual_print(f"🔗 Connecting to SmartKnob on {port} at {args.baud} baud...")
    
    start_loop_time = time.time()
    
    try:
        # Create async connection
        async with SmartKnobConnection(port, args.baud) as knob:
            dual_print("✅ Connected successfully!")
            
            # Set up message callback
            knob.set_message_callback(on_message)
            
            # Send initial commands
            dual_print("🚀 Sending GET_KNOB_INFO command...")
            await knob.send_command(0)  # GET_KNOB_INFO
            
            # Wait a moment for knob info response
            await anyio.sleep(0.5)
            
            if args.request_state:
                dual_print(f"🎛️ Starting position tracking (every {args.state_interval}s)...")
            
            # Monitor for specified duration
            dual_print(f"📡 Monitoring for {args.duration} seconds...")
            dual_print("=" * 80)
            
            start_loop_time = time.time()
            last_state_request = 0
            
            # Start read loop in background with proper exception handling
            try:
                async with anyio.create_task_group() as tg:
                    # Start protocol read loop
                    tg.start_soon(knob.protocol.read_loop)
                    
                    # Main monitoring loop
                    while True:
                        current_time = time.time()
                        elapsed = current_time - start_loop_time
                        
                        # Check timeout
                        if elapsed >= args.duration:
                            dual_print(f"\n⏱️  Duration timeout reached ({args.duration}s)")
                            tg.cancel_scope.cancel()
                            break
                        
                        # Send state requests if enabled
                        if args.request_state and (current_time - last_state_request) >= args.state_interval:
                            # Create RequestState message using the protocol's send method
                            try:
                                # Use a more direct approach - create the message manually
                                request_msg = smartknob_pb2.ToSmartknob()
                                request_msg.request_state.CopyFrom(smartknob_pb2.RequestState())
                                await knob.protocol._enqueue_message(request_msg)
                                dual_print(f"🔄 Requested knob state (attempt {int((current_time - start_loop_time) / args.state_interval)})")
                                last_state_request = current_time
                            except Exception as e:
                                dual_print(f"⚠️  Failed to send RequestState: {e}")
                        
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
                        # Silently absorb expected serial timeouts
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
            for msg_type, count in message_types.items():
                icon = MESSAGE_ICONS.get(msg_type, '📨')
                dual_print(f"   {icon} {msg_type}: {count}")
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
