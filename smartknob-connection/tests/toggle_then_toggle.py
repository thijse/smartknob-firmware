#!/usr/bin/env python3
"""
Single-process test: Send Toggle then MultipleChoice in one session.

This avoids serial port re-open timing between separate processes. It:
- Connects once
- Sends a Toggle AppComponent
- Waits for ACK and RX log confirmation
- Sends a MultipleChoice AppComponent
- Waits for ACK and RX log confirmation
- Monitors selection and button presses

Correlates host-side ACKs with firmware "ACK sent" and RX AppComponent logs.
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

from smartknob.protocol import SmartKnobConnection  # noqa: E402
from smartknob.connection import find_smartknob_ports  # noqa: E402

# Suppress logging except for errors
logging.basicConfig(level=logging.ERROR)


class SingleSessionMonitor:
    """
    Message monitor with:
    - Raw inbound capture (size + hex preview)
    - ACK correlation and waiting
    - Log parsing for AppComponent RX lines
    - Simple state/press display
    """

    def __init__(self, connection, log_file=None, drinks=None):
        self.connection = connection
        self.log_file = log_file
        self.drinks = drinks or ["Coffee", "Tea", "Water", "Juice", "Soda"]

        self.send_channel: anyio.abc.ObjectSendStream
        self.receive_channel: anyio.abc.ObjectReceiveStream
        self.send_channel, self.receive_channel = anyio.create_memory_object_stream(max_buffer_size=4000)

        self.received_acks = set()
        self.last_press_nonce = 0
        self.last_position = None

        # Diagnostics parsed from firmware logs
        self.component_mode_active_count = 0
        self.last_rx_app_component_id = None
        self.last_rx_payload_tag = None

        # Raw logging file
        self.raw_log_file = None
        self.setup_raw_logging()

    def _log_to_file(self, line: str):
        try:
            if self.log_file:
                self.log_file.write(line + "\n")
                self.log_file.flush()
        except Exception:
            pass

    def setup_raw_logging(self):
        """Set up raw data logging to a separate binary file under project logs directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(project_root, "logs", "toggle_then_multiple_choice_raw")
        os.makedirs(log_dir, exist_ok=True)
        log_filename = f"smartknob_raw_{timestamp}.log"
        full_path = os.path.join(log_dir, log_filename)
        try:
            self.raw_log_file = open(full_path, "wb")
            print(f"📝 Raw serial data will be logged to: {full_path}")
        except Exception as e:
            print(f"⚠️ Failed to open raw log file: {e}")
            self.raw_log_file = None

    def cleanup_raw_logging(self):
        """Close raw logging file."""
        if self.raw_log_file:
            try:
                self.raw_log_file.close()
            except Exception:
                pass
            self.raw_log_file = None

    def on_raw_data_bytes(self, data: bytes):
        try:
            ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hex_preview = data[:64].hex()
            # Structured preview log to the main text log
            self._log_to_file(f"[{ts}] RAW_RX len={len(data)} bytes preview={hex_preview}")
            # Full raw bytes to dedicated raw binary log
            if self.raw_log_file:
                log_entry = f"[{ts}] ".encode("utf-8") + data + b"\n"
                self.raw_log_file.write(log_entry)
                self.raw_log_file.flush()
        except Exception:
            pass

    def on_message(self, msg):
        try:
            self.send_channel.send_nowait(msg)
        except anyio.WouldBlock:
            print("⚠️  WARNING: Message queue full, dropping message to prevent blocking")

    async def _message_processor_task(self):
        async for msg in self.receive_channel:
            msg_type = msg.WhichOneof("payload")

            if msg_type == "log":
                try:
                    origin = getattr(msg.log, "origin", "")
                    text = getattr(msg.log, "msg", "")
                except Exception:
                    origin, text = "", ""
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self._log_to_file(f"[{timestamp}] 📝 LOG [{origin}] {text}")

                # Parse useful markers
                if "Component mode active" in text:
                    self.component_mode_active_count += 1

                if "SerialProtocolProtobuf: RX nonce=" in text:
                    # Example: SerialProtocolProtobuf: RX nonce=... payload_tag=8 size=...
                    self.last_rx_payload_tag = 1  # marker; not strictly needed, presence is enough

                if "SerialProtocolProtobuf: AppComponent id='" in text:
                    # Extract id between quotes
                    try:
                        start = text.index("AppComponent id='") + len("AppComponent id='")
                        end = text.index("'", start)
                        self.last_rx_app_component_id = text[start:end]
                    except Exception:
                        pass

            elif msg_type == "ack":
                try:
                    nonce = getattr(msg.ack, "nonce", None)
                except Exception:
                    nonce = None
                if nonce is not None:
                    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self.received_acks.add(nonce)
                    self._log_to_file(f"[{ts}] ✅ ACK received for nonce={nonce}")

            elif msg_type == "smartknob_state":
                state = msg.smartknob_state
                current_position = state.current_position
                timestamp = datetime.now().strftime("%H:%M:%S")

                if hasattr(state, "press_nonce") and state.press_nonce != self.last_press_nonce:
                    self.last_press_nonce = state.press_nonce
                    print(f"[{timestamp}] 🔘 PRESS (index {current_position}, nonce={state.press_nonce})")
                    self._log_to_file(f"[{timestamp}] BUTTON PRESS (index {current_position}, nonce={state.press_nonce})")

                elif self.last_position != current_position:
                    selected_value = self.get_selected_value(current_position)
                    print(f"[{timestamp}] {selected_value} ({current_position})")
                    self._log_to_file(f"[{timestamp}] STATE {selected_value} ({current_position})")
                    self.last_position = current_position

    def get_selected_value(self, position):
        if 0 <= position < len(self.drinks):
            return self.drinks[position]
        return f"Unknown ({position})"

    async def wait_for_ack(self, nonce: int, timeout: float = 1.5) -> bool:
        start = anyio.current_time()
        while (anyio.current_time() - start) < timeout:
            if nonce in self.received_acks:
                return True
            await anyio.sleep(0.05)
        return False

    async def wait_for_rx_app_component(self, expected_id: str, timeout: float = 3.0) -> bool:
        start = anyio.current_time()
        while (anyio.current_time() - start) < timeout:
            if self.last_rx_app_component_id == expected_id:
                return True
            await anyio.sleep(0.05)
        return False

    async def wait_for_component_mode_active_increment(self, previous_count: int, timeout: float = 5.0) -> bool:
        start = anyio.current_time()
        while (anyio.current_time() - start) < timeout:
            if self.component_mode_active_count > previous_count:
                return True
            await anyio.sleep(0.05)
        return False


async def main():
    # Find SmartKnob port
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return

    port = ports[0]
    print(f"📡 Connecting to SmartKnob on {port}...")

    # Prepare log file path under project logs/toggle_then_multiple_choice
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, "logs", "toggle_then_multiple_choice")
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"toggle_then_multiple_choice_{ts}.log")
    log_file = open(log_path, "w", encoding="utf-8")
    print(f"📝 Logging to file: {log_path}")
    monitor = None

    try:
        async with SmartKnobConnection(port) as connection:
            print("✅ Connected!")

            monitor = SingleSessionMonitor(connection, log_file=log_file)
            connection.set_message_callback(monitor.on_message)
            connection.set_raw_data_callback(monitor.on_raw_data_bytes)

            async with anyio.create_task_group() as tg:
                tg.start_soon(connection.protocol.read_loop)  # fast producer
                tg.start_soon(monitor._message_processor_task)  # slow consumer

                # Stabilize
                await anyio.sleep(1.0)


                # Alternate between components until stopped
                print("Alternating between Toggle and MultipleChoice. Ctrl+C to stop.")
                try:
                    while True:
                        # Step A: Send Toggle again
                        toggle_id = "toggle_1"
                        prev_active_count = monitor.component_mode_active_count
                        try:
                            # Explicit symmetric feel on each iteration as well
                            nonce_t = await connection.protocol.send_toggle(  # type: ignore[attr-defined]
                                component_id=toggle_id,
                                title="AzurionEye",
                                off_label="OFF",
                                on_label="ON",
                                initial_state=False,
                                snap_point=0.5,
                                snap_point_bias=0.0,
                                detent_strength_unit=0.5,
                                off_led_hue=0,
                                on_led_hue=120,
                            )
                            tsx = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            monitor._log_to_file(f"[{tsx}] ENQUEUED AppComponent nonce={nonce_t} id='{toggle_id}' type=TOGGLE")

                            ack_ok = await monitor.wait_for_ack(nonce_t, timeout=1.5)
                            if not ack_ok:
                                print(f"⚠️ Warning: ACK timeout for Toggle AppComponent nonce={nonce_t}")
                                monitor._log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ⚠️ ACK timeout for Toggle nonce={nonce_t}")

                            # Wait for firmware RX log to confirm delivery and decode
                            rx_ok = await monitor.wait_for_rx_app_component(toggle_id, timeout=3.0)
                            if not rx_ok:
                                print("⚠️ Warning: No firmware RX AppComponent log observed for Toggle")

                            # Wait until we see component mode active increment
                            act_ok = await monitor.wait_for_component_mode_active_increment(prev_active_count, timeout=5.0)
                            if act_ok:
                                print("✅ Toggle component activated")
                            else:
                                print("⚠️ Warning: Did not observe 'Component mode active' increment after Toggle")

                        except Exception as e:
                            print(f"❌ Failed to send TOGGLE: {e}")
                            break

                        # Short dwell on Toggle
                        await anyio.sleep(3.0)

                        # Step B: Transport handshake before MultipleChoice
                        toggle_id = "toggle_2"
                        prev_active_count = monitor.component_mode_active_count
                        try:
                            # Explicit symmetric feel on each iteration as well
                            nonce_t = await connection.protocol.send_toggle(  # type: ignore[attr-defined]
                                component_id=toggle_id,
                                title="Philips",
                                off_label="-aan-",
                                on_label="-uit-",
                                initial_state=False,
                                snap_point=0.5,
                                snap_point_bias=0.8,
                                detent_strength_unit=1.0,
                                off_led_hue=0,
                                on_led_hue=120,
                            )
                            tsx = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            monitor._log_to_file(f"[{tsx}] ENQUEUED AppComponent nonce={nonce_t} id='{toggle_id}' type=TOGGLE")

                            ack_ok = await monitor.wait_for_ack(nonce_t, timeout=1.5)
                            if not ack_ok:
                                print(f"⚠️ Warning: ACK timeout for Toggle AppComponent nonce={nonce_t}")
                                monitor._log_to_file(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] ⚠️ ACK timeout for Toggle nonce={nonce_t}")

                            # Wait for firmware RX log to confirm delivery and decode
                            rx_ok = await monitor.wait_for_rx_app_component(toggle_id, timeout=3.0)
                            if not rx_ok:
                                print("⚠️ Warning: No firmware RX AppComponent log observed for Toggle")

                            # Wait until we see component mode active increment
                            act_ok = await monitor.wait_for_component_mode_active_increment(prev_active_count, timeout=5.0)
                            if act_ok:
                                print("✅ Toggle component activated")
                            else:
                                print("⚠️ Warning: Did not observe 'Component mode active' increment after Toggle")

                        except Exception as e:
                            print(f"❌ Failed to send TOGGLE: {e}")
                            break

 
                        # Dwell on MultipleChoice before switching back
                        await anyio.sleep(3.0)

                except KeyboardInterrupt:
                    print("\n⏹️ Stopped")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            if monitor is not None:
                monitor.cleanup_raw_logging()
        except Exception:
            pass
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