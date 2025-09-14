#!/usr/bin/env python3
"""
SmartKnob MultipleChoice Component Example

Simple example showing how to use the MultipleChoice component.
Based on the working toggle example pattern.
"""

import sys
import os
import logging
import anyio
import anyio.abc
from datetime import datetime

# Add smartknob-connection directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
smartknob_path = os.path.dirname(current_dir)
sys.path.insert(0, smartknob_path)

from smartknob.protocol import SmartKnobConnection, reset_connection
from smartknob.connection import find_smartknob_ports
from smartknob.proto_gen import smartknob_pb2

# Suppress logging except for errors
logging.basicConfig(level=logging.ERROR)

class MultipleChoiceMonitor:
    """Clean multiple choice monitoring."""
    
    def __init__(self, connection, options=None, log_file=None):
        self.connection = connection
        self.options = options or ["Option 1", "Option 2", "Option 3"]
        self.last_position = None
        self.component_active = False
        self.button_pressed = False
        self.last_press_nonce = 0  # Track press nonce to detect new presses
        self.log_file = log_file  # File handle for logging firmware messages and events
        # This is our message queue (an anyio channel) to decouple the fast
        # message receiving from the slow message processing/printing.
        self.send_channel: anyio.abc.ObjectSendStream
        self.receive_channel: anyio.abc.ObjectReceiveStream
        self.send_channel, self.receive_channel = anyio.create_memory_object_stream(max_buffer_size=4000)
        # Track ACKs received from firmware (nonce set)
        self.received_acks = set()

    def _log_to_file(self, line: str):
        try:
            if self.log_file:
                self.log_file.write(line + "\n")
                self.log_file.flush()
        except Exception:
            pass

    def on_raw_data_bytes(self, data: bytes):
        """
        Optional raw-data callback: captures raw inbound serial bytes to file for diagnostics.
        Note: This logs bytes as length and hex (truncated) to avoid huge files.
        """
        try:
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_preview = data[:64].hex()
            self._log_to_file(f"[{ts}] RAW_RX len={len(data)} bytes preview={hex_preview}")
        except Exception:
            pass
        
    def on_message(self, msg):
        """
        FAST callback. Do not block here.
        Immediately sends the message to a processing task via the channel.
        """
        try:
            # This is a non-blocking send.
            self.send_channel.send_nowait(msg)
        except anyio.WouldBlock:
            # Safety valve: If the consumer is too slow, we drop intermediate
            # messages instead of letting them pile up and crash the serial buffer.
            # For UI updates, this is the correct behavior.
            print("⚠️  WARNING: Message queue full, dropping message to prevent blocking")
            pass

    async def _message_processor_task(self):
        """
        SLOW consumer. Reads messages from the channel and performs slow
        I/O operations like printing to the console.
        """
        async for msg in self.receive_channel:
            msg_type = msg.WhichOneof("payload")
        
            if msg_type == 'log':
                # Always capture firmware log messages to file
                try:
                    origin = getattr(msg.log, 'origin', '')
                    text = getattr(msg.log, 'msg', '')
                except Exception:
                    origin, text = '', ''
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self._log_to_file(f"[{timestamp}] 📝 LOG [{origin}] {text}")
                # Check for component activation (console behavior unchanged)
                if 'Component mode active' in str(text):
                    if (not self.component_active):
                        self.component_active = True
                        print("✅ Component created successfully!")

            elif msg_type == 'ack':
                # Track ACKs so we can correlate with sent nonces
                try:
                    nonce = getattr(msg.ack, 'nonce', None)
                except Exception:
                    nonce = None
                if nonce is not None:
                    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self.received_acks.add(nonce)
                    self._log_to_file(f"[{ts}] ✅ ACK received for nonce={nonce}")

            elif msg_type == 'smartknob_state':
                if self.component_active:
                    state = msg.smartknob_state
                    current_position = state.current_position
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # Check for button press using press_nonce - IMMEDIATE FEEDBACK
                    if hasattr(state, 'press_nonce') and state.press_nonce != self.last_press_nonce:
                        self.button_pressed = True
                        self.last_press_nonce = state.press_nonce
                        selected_value = self.get_selected_value(current_position)
                        print(f"[{timestamp}] 🔘 SELECTED: {selected_value} (index {current_position}, nonce={state.press_nonce})")
                        # Also record to file
                        self._log_to_file(f"[{timestamp}] BUTTON SELECTED: {selected_value} (index {current_position}, nonce={state.press_nonce})")
                    
                    # Show position changes only when position actually changes
                    elif self.last_position != current_position:
                        selected_value = self.get_selected_value(current_position)
                        print(f"[{timestamp}] {selected_value} ({current_position})")
                        # Also record to file
                        self._log_to_file(f"[{timestamp}] STATE {selected_value} ({current_position})")
                        self.last_position = current_position

    def get_selected_value(self, position):
        """Get the selected value for a position."""
        if 0 <= position < len(self.options):
            return self.options[position]
        return f"Unknown ({position})"

    def is_button_pressed(self):
        """Check if button was pressed and reset flag."""
        if self.button_pressed:
            self.button_pressed = False
            return True
        return False

    async def wait_for_ack(self, nonce: int, timeout: float = 1.5) -> bool:
        """Wait until an ACK with the given nonce is observed or timeout."""
        start = anyio.current_time()
        while (anyio.current_time() - start) < timeout:
            if nonce in self.received_acks:
                return True
            await anyio.sleep(0.05)
        return False

    async def create_multiple_choice_component(self, component_id="multi_choice", title="Select Option", options=None):
        """Create a multiple choice component."""
        if options:
            self.options = options

        # Small stabilization delay to avoid initial empty COBS frames interfering
        await anyio.sleep(0.3)

        # Use protocol helper to compose and send MULTI_CHOICE AppComponent
        self.component_active = False
        try:
            nonce = await self.connection.protocol.send_multi_choice(  # type: ignore[attr-defined]
                component_id=component_id,
                title=title,
                options=self.options,
                initial_index=0,
                wrap_around=True,
                detent_strength_unit=1.5,   # Strong feedback
                endstop_strength_unit=1.5,  # Strong endstops
                led_hue=200                 # Blue color
            )
            # Record enqueue info to file for correlation
            ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            self._log_to_file(f"[{ts}] ENQUEUED AppComponent nonce={nonce} id='{component_id}' type=MULTI_CHOICE options={len(self.options)}")

            # Wait for ACK of the exact nonce to confirm delivery to firmware
            ack_ok = await self.wait_for_ack(nonce, timeout=1.5)
            if not ack_ok:
                print(f"⚠️ Warning: ACK timeout for AppComponent nonce={nonce}")
                self._log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ⚠️ ACK timeout for AppComponent nonce={nonce}")

        except Exception as e:
            self._log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ERROR enqueue AppComponent: {e}")
            print(f"❌ Failed to send MULTI_CHOICE: {e}")
            return False

        # Wait for component creation by polling component_active flag
        timeout = 10.0  # Maximum wait time in seconds
        start_time = anyio.current_time()

        while not self.component_active:
            if (anyio.current_time() - start_time) > timeout:
                print("⚠️ Warning: Component creation timeout")
                return False
            await anyio.sleep(0.1)  # Check every 100ms

        # Component will be created successfully and logged in on_message
        return True

    async def monitor_selection(self, duration_seconds=None):
        """Simplified monitoring - all logging happens in on_message for immediate feedback."""
        print(f"Multiple Choice Monitor - {len(self.options)} options")
        print("=" * 50)
        print("Options:", ", ".join(self.options))
        print("Rotate the knob to select options.")
        print("Press the knob to confirm selection.")
        print("Press Ctrl+C to stop monitoring.")
        print("")
        
        # Just wait - all the real work happens in on_message now
        try:
            if duration_seconds:
                await anyio.sleep(duration_seconds)
            else:
                # Run indefinitely with longer sleep since we're not doing work here
                while True:
                    await anyio.sleep(1.0)
                    
        except KeyboardInterrupt:
            print("\nStopped by user")

async def main():
    """Main function for multiple choice monitoring."""
    
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return
    
    port = ports[0]
    print(f"📡 Connecting to SmartKnob on {port}...")
    
    # Prepare log file path under project logs/use_multiple_choice
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs', 'use_multiple_choice')
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"multiple_choice_{ts}.log")
    log_file = open(log_path, 'w', encoding='utf-8')
    print(f"📝 Logging to file: {log_path}")
    
    # Reset for clean state
    # reset_connection(port)
    
    try:
        # Connect and start monitoring
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected!")
            
            # Create monitor with drink options
            drinks = ["Coffee", "Tea", "Water", "Juice", "Soda"]
            monitor = MultipleChoiceMonitor(connection, options=drinks, log_file=log_file)
            
            # Set up message handler
            connection.set_message_callback(monitor.on_message)
            # Set up raw data capture (inbound only)
            connection.set_raw_data_callback(monitor.on_raw_data_bytes)
            
            # Start protocol read loop
            async with anyio.create_task_group() as tg:
                # Start protocol read loop (the "fast producer")
                tg.start_soon(connection.protocol.read_loop)
                # Start our new, decoupled message processor (the "slow consumer")
                tg.start_soon(monitor._message_processor_task)
                
                # Wait for initial connection
                await anyio.sleep(1.0)
                
                # Create multiple choice component
                await monitor.create_multiple_choice_component(
                    component_id="drink_selector",
                    title="Drink Selector",
                    options=drinks
                )
                
                # Monitor selection changes
                await monitor.monitor_selection()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            log_file.close()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped")
    except Exception as e:
        print(f"\n💥 Error: {e}")
