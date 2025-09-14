#!/usr/bin/env python3
"""
Physical Component Testing

This script creates a toggle component and then monitors the device
while you physically interact with the knob to test if the component
is actually running and responding to input.
"""

import sys
import asyncio
import anyio
import logging
from pathlib import Path

# Add the SmartKnob library to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "smartknob-connection2"))

from smartknob import SmartKnobConnection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_physical_component_interaction():
    """Test actual physical interaction with a toggle component."""
    
    logger.info("🎯 Physical Component Interaction Test")
    logger.info("=" * 50)
    
    # Find SmartKnob device
    ports = find_smartknob_ports()
    if not ports:
        logger.error("❌ No SmartKnob devices found")
        return False
    
    port = ports[0]
    logger.info(f"📡 Using SmartKnob on: {port}")
    
    # Message counters
    message_count = 0
    component_logs = []
    acks_received = 0
    
    def on_message(msg):
        nonlocal message_count, component_logs, acks_received
        message_count += 1
        
        if hasattr(msg, 'ack'):
            acks_received += 1
            logger.info(f"✅ ACK received (nonce={msg.ack.nonce})")
        
        if hasattr(msg, 'log') and msg.log:
            log_msg = msg.log.msg
            if any(keyword in log_msg.lower() for keyword in ['component', 'toggle', 'knob', 'state', 'rotation', 'button', 'snap', 'position']):
                component_logs.append(log_msg)
                logger.info(f"📝 COMPONENT LOG: {log_msg}")
    
    # Connect with auto-reset for clean state
    logger.info("🔄 Connecting with auto-reset for clean device state...")
    
    connection = SmartKnobConnection(port, auto_reset=True)
    try:
        success = await connection.start()
        if not success:
            logger.error("❌ Failed to connect")
            return False
            
        connection.protocol.on_message = on_message
        
        # Wait for device to stabilize after reset
        await asyncio.sleep(2)
        logger.info("⏳ Device stabilized, creating toggle component...")
        
        # Create a physical toggle component with clear feedback
        to_smartknob = smartknob_pb2.ToSmartknob()
        to_smartknob.app_component.component_id = "physical_test_toggle"
        to_smartknob.app_component.type = 0  # TOGGLE = 0
        to_smartknob.app_component.display_name = "Aan uit knop"
        
        # Configure toggle with strong haptic feedback for testing
        toggle_config = to_smartknob.app_component.toggle
        toggle_config.off_label = "Aan"
        toggle_config.on_label = "Uit" 
        toggle_config.snap_point = 0.7  # Clear 50% snap point
        toggle_config.snap_point_bias = 0.0  # No bias for testing
        toggle_config.off_led_hue = 0    # Red when OFF  
        toggle_config.on_led_hue = 120   # Green when ON 
        toggle_config.initial_state = False  # Start in OFF state
        
        logger.info("📤 Sending toggle component configuration...")
        await connection.protocol._enqueue_message(to_smartknob)
        
        # Wait for component creation
        await asyncio.sleep(3)
        
        logger.info("\n🖥️  DISPLAY CHECK:")
        logger.info("=" * 30)
        logger.info("❓ Do you see a toggle app on the SmartKnob display?")
        logger.info("❓ Does it show 'Physical Test' or 'OFF' state?")
        logger.info("❓ Is there any visual indication the component is active?")
        
        logger.info("\n🎮 PHYSICAL TESTING INSTRUCTIONS:")
        logger.info("=" * 50)
        logger.info("1. 🔄 Try rotating the knob slowly")
        logger.info("2. 🔄 Try rotating past the 50% snap point")
        logger.info("3. 🔘 Try pressing the button")
        logger.info("4. 👀 Watch for LED color changes (Red ↔ Green)")
        logger.info("5. 🖥️  Look at the display for state changes")
        logger.info("6. ⚡ Feel for haptic feedback at the snap point")
        logger.info("\n💬 All component activity will be logged here...")
        logger.info("Press Ctrl+C when done testing\n")
        
        # Monitor for physical interactions
        try:
            start_time = asyncio.get_event_loop().time()
            last_status = start_time
            
            while True:
                await asyncio.sleep(0.1)
                current_time = asyncio.get_event_loop().time()
                
                # Print status every 10 seconds
                if current_time - last_status >= 10:
                    elapsed = int(current_time - start_time)
                    logger.info(f"⏱️  Monitoring for {elapsed}s - Messages: {message_count}, ACKs: {acks_received}, Component logs: {len(component_logs)}")
                    if len(component_logs) > 0:
                        logger.info(f"📊 Recent component activity: {len(component_logs)} relevant logs")
                    last_status = current_time
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 Testing stopped by user")
            
        # Final summary
        logger.info(f"\n📊 FINAL TEST RESULTS:")
        logger.info(f"   📨 Total messages received: {message_count}")
        logger.info(f"   ✅ ACKs received: {acks_received}")
        logger.info(f"   📝 Component-related logs: {len(component_logs)}")
        
        if len(component_logs) > 0:
            logger.info(f"\n📝 Component activity summary:")
            for log in component_logs[-10:]:  # Show last 10 relevant logs
                logger.info(f"   • {log}")
                
        # User feedback questions
        logger.info(f"\n❓ USER FEEDBACK NEEDED:")
        logger.info(f"   1. Did you see the toggle app on the display?")
        logger.info(f"   2. Did the knob respond to rotation with haptic feedback?")
        logger.info(f"   3. Did the LED ring change colors?")
        logger.info(f"   4. Did button presses trigger any response?")
        logger.info(f"   5. Did the display show state changes?")
        
    finally:
        await connection.stop()
        
    return True

async def main():
    """Main test function."""
    try:
        success = await test_physical_component_interaction()
        if success:
            logger.info("\n🎯 Physical component testing complete!")
            return True
        else:
            logger.error("\n❌ Physical testing failed")
            return False
    except Exception as e:
        logger.error(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
