from __future__ import annotations

"""
Multiple Choice component for SmartKnob.

Encapsulates:
- Sending the MULTI_CHOICE AppComponent config (component_id, title, options, etc.)
- Switching into multiple choice mode (via protocol helper)
- Emitting simple callbacks: connected, value selected, button pressed
- Fast-producer / slow-consumer pattern using anyio memory channels to avoid blocking the serial reader

Usage:
    from smartknob.highlevel.multiple_choice import MultipleChoiceSession
    from smartknob.connection import find_smartknob_ports
    import anyio

    async def main():
        ports = find_smartknob_ports()
        if not ports:
            print("No SmartKnob devices found")
            return
        port = ports[0]
        async with await MultipleChoiceSession.connect(
            port,
            options=["Coffee", "Tea", "Water"],
            title="Drink Selector",
        ) as mc:
            mc.on_connected(lambda: print("ready"))
            mc.on_value_selected(lambda i, t: print("select", i, t))
            mc.on_button_pressed(lambda i, t: print("press", i, t))
            await mc.run_forever()

    anyio.run(main)
"""

import anyio
import time
from anyio.abc import ObjectReceiveStream, ObjectSendStream
from typing import Callable, List, Optional, Tuple, Any

from ..protocol import SmartKnobConnection


class MultipleChoiceSession:
    """
    High-level session for MULTI_CHOICE component.

    Responsibilities:
    - Prepare and send MULTI_CHOICE config using protocol helper
    - Manage async tasks: protocol.read_loop (producer) and a consumer that processes messages
    - Provide callbacks:
        - on_connected()
        - on_value_selected(index: int, text: str)
        - on_button_pressed(index: int, text: str)
    - Idempotent setup (skips re-sending same config)
    """

    # ----- Lifecycle -----------------------------------------------------

    def __init__(
        self,
        connection: SmartKnobConnection,
        component_id: str = "multi_choice",
        title: str = "Select Option",
        options: Optional[List[str]] = None,
        wrap_around: bool = True,
        initial_index: int = 0,
        detent_strength_unit: float = 1.5,
        endstop_strength_unit: float = 1.5,
        led_hue: int = 200,
    ):
        self.connection = connection
        self.component_id = component_id
        self.title = title
        self.options: List[str] = list(options or ["Option 1", "Option 2", "Option 3"])
        self.wrap_around = wrap_around
        self.initial_index = int(initial_index)
        self.detent_strength_unit = float(detent_strength_unit)
        self.endstop_strength_unit = float(endstop_strength_unit)
        self.led_hue = int(led_hue)

        # Callbacks (user-provided)
        self._cb_connected: Callable[[], None] = lambda: None
        self._cb_value_selected: Callable[[int, str], None] = lambda i, t: None
        self._cb_button_pressed: Callable[[int, str], None] = lambda i, t: None

        # Internal state
        self._send_chan: ObjectSendStream[Any]
        self._recv_chan: ObjectReceiveStream[Any]
        self._send_chan, self._recv_chan = anyio.create_memory_object_stream(max_buffer_size=4000)

        self._tg: Optional[Any] = None
        self._connected_event = anyio.Event()
        self._last_setup_nonce: Optional[int] = None
        self._component_active: bool = False

        self._last_index: Optional[int] = None
        self._last_press_nonce: int = -1

        # Button press deduplication
        self._last_button_press_index: Optional[int] = None
        self._last_button_press_time: float = 0
        self._button_debounce_ms: float = 1000  # 100ms debounce window

        self._owns_connection: bool = False
        self._last_config_key: Optional[Tuple] = None

    async def __aenter__(self) -> "MultipleChoiceSession":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    @classmethod
    async def connect(
        cls,
        port: str,
        options: List[str],
        title: str = "Select Option",
        component_id: str = "multi_choice",
        auto_reset: bool = False,
        wrap_around: bool = True,
        initial_index: int = 0,
        detent_strength_unit: float = 1.5,
        endstop_strength_unit: float = 1.5,
        led_hue: int = 200,
    ) -> "MultipleChoiceSession":
        """
        Convenience: open the connection and return a ready session usable as an async context manager.
        """
        conn = SmartKnobConnection(port, auto_reset=auto_reset)
        ok = await conn.start()
        if not ok:
            raise RuntimeError("Failed to connect to SmartKnob")

        session = cls(
            conn,
            component_id=component_id,
            title=title,
            options=options,
            wrap_around=wrap_around,
            initial_index=initial_index,
            detent_strength_unit=detent_strength_unit,
            endstop_strength_unit=endstop_strength_unit,
            led_hue=led_hue,
        )
        session._owns_connection = True
        await session.start()
        return session

    async def start(self, wait_timeout: float = 10.0):
        """
        Start the session:
        - Wire fast on_message producer
        - Launch protocol.read_loop and consumer in a TaskGroup
        - Send MULTI_CHOICE setup and wait until connected (ACK or activation log)
        """
        # Ensure protocol object exists (supports external connections that must be started first)
        proto = getattr(self.connection, "protocol", None)
        if proto is None:
            raise RuntimeError("SmartKnobConnection.protocol is not initialized. Call SmartKnobConnection.start() first or use MultipleChoiceSession.connect().")

        # Set fast producer callback
        self.connection.set_message_callback(self._on_message_fast)

        # Create task group
        self._tg = await anyio.create_task_group().__aenter__()
        try:
            # Producer: protocol read loop
            self._tg.start_soon(proto.read_loop)
            # Consumer: process messages
            self._tg.start_soon(self._consumer_loop)

            # Send setup (idempotent)
            await self._send_setup()

            # Wait for readiness
            with anyio.move_on_after(wait_timeout):
                await self._connected_event.wait()
            if self._connected_event.is_set():
                # Fire connected only once here (consumer also ensures single-fire guard)
                self._fire_connected_once()
            else:
                # Timed out, keep running but not "connected"
                pass
        except BaseException:
            # If anything fails during startup, ensure we tear down the TG
            await self._cancel_task_group_safely()
            raise

    async def stop(self):
        """
        Stop the session and optionally the underlying connection if owned by this session.
        """
        await self._cancel_task_group_safely()

        # Close channels
        try:
            await self._send_chan.aclose()
        except Exception:
            pass
        try:
            await self._recv_chan.aclose()
        except Exception:
            pass

        if self._owns_connection:
            try:
                await self.connection.stop()
            except Exception:
                pass

    async def _cancel_task_group_safely(self):
        if self._tg is not None:
            try:
                await self._tg.__aexit__(None, None, None)
            finally:
                self._tg = None

    # ----- Public API ----------------------------------------------------

    def on_connected(self, cb: Callable[[], None]) -> "MultipleChoiceSession":
        self._cb_connected = cb or (lambda: None)
        return self

    def on_value_selected(self, cb: Callable[[int, str], None]) -> "MultipleChoiceSession":
        self._cb_value_selected = cb or (lambda i, t: None)
        return self

    def on_button_pressed(self, cb: Callable[[int, str], None]) -> "MultipleChoiceSession":
        self._cb_button_pressed = cb or (lambda i, t: None)
        return self

    async def run_forever(self):
        """
        Simple helper to keep the session alive.
        """
        while True:
            await anyio.sleep(1.0)

    async def update_options(self, options: List[str], initial_index: Optional[int] = None, wait_timeout: float = 5.0):
        """
        Update options and re-send configuration (idempotent).
        """
        if options is not None:
            self.options = list(options)
        if initial_index is not None:
            self.initial_index = int(initial_index)

        await self._send_setup()

        # Wait for readiness signal again (ack/log)
        evt = anyio.Event()
        # Reset the connected event and wait; consumer will set again on ack/log.
        self._connected_event = evt
        with anyio.move_on_after(wait_timeout):
            await evt.wait()

    def get_current(self) -> Tuple[int, str]:
        """
        Return the last known (index, text).
        If no index seen yet, returns (initial_index, text_at_initial_or_unknown).
        """
        idx = self._last_index if self._last_index is not None else self.initial_index
        if 0 <= idx < len(self.options):
            return idx, self.options[idx]
        return idx, f"Unknown ({idx})"

    # ----- Internal helpers ---------------------------------------------

    async def _send_setup(self):
        """
        Compose and send MULTI_CHOICE config using protocol helper, idempotently.
        """
        key = (
            self.component_id,
            self.title,
            tuple(self.options),
            self.initial_index,
            self.wrap_around,
            self.detent_strength_unit,
            self.endstop_strength_unit,
            self.led_hue,
        )
        if key == self._last_config_key:
            return

        self._connected_event = anyio.Event()
        self._component_active = False

        proto = getattr(self.connection, "protocol", None)
        if proto is None:
            raise RuntimeError("SmartKnobConnection.protocol is not initialized. Call SmartKnobConnection.start() first or use MultipleChoiceSession.connect().")

        nonce = await proto.send_multi_choice(  # type: ignore[attr-defined]
            component_id=self.component_id,
            title=self.title,
            options=self.options,
            initial_index=self.initial_index,
            wrap_around=self.wrap_around,
            detent_strength_unit=self.detent_strength_unit,
            endstop_strength_unit=self.endstop_strength_unit,
            led_hue=self.led_hue,
        )
        self._last_setup_nonce = nonce
        self._last_config_key = key

    def _on_message_fast(self, msg):
        """
        Fast producer: push messages to the channel without blocking.
        """
        try:
            # Prefer non-blocking path if available (AnyIO may not expose send_nowait in type stubs)
            send_nowait = getattr(self._send_chan, "send_nowait", None)
            if callable(send_nowait):
                send_nowait(msg)  # type: ignore[misc]
            else:
                # If non-blocking API is not available, drop the message to avoid blocking serial reader.
                pass
        except Exception:
            # Drop to avoid backpressure on serial
            pass

    async def _consumer_loop(self):
        """
        Slow consumer: parse messages and emit events.
        """
        async for msg in self._recv_chan:
            try:
                msg_type = msg.WhichOneof("payload")
            except Exception:
                continue

            # Activation / connected detection
            if msg_type == "ack":
                try:
                    if self._last_setup_nonce is not None and msg.ack.nonce == self._last_setup_nonce:
                        self._mark_connected()
                except Exception:
                    pass
            elif msg_type == "log":
                # Fallback: detect activation via log like the advanced example
                try:
                    text = msg.log.msg
                    if isinstance(text, str) and "Component mode active" in text:
                        self._mark_connected()
                except Exception:
                    pass

            # State updates (support both field names used across versions)
            if msg_type in ("smartknob_state", "knob"):
                state = None
                try:
                    state = getattr(msg, "smartknob_state", None) or getattr(msg, "knob", None)
                except Exception:
                    state = None

                if state is None:
                    continue

                # Current position
                try:
                    current_position = int(getattr(state, "current_position", self.initial_index))
                except Exception:
                    current_position = self.initial_index

                # Button press via press_nonce
                try:
                    press_nonce = int(getattr(state, "press_nonce", -1))
                except Exception:
                    press_nonce = -1

                # Value selected event on position change
                if self._last_index is None or current_position != self._last_index:
                    self._last_index = current_position
                    idx, text = self.get_current()
                    try:
                        self._cb_value_selected(idx, text)
                    except Exception:
                        pass

                # Button pressed event on press_nonce change
                if press_nonce >= 0 and press_nonce != self._last_press_nonce:
                    self._last_press_nonce = press_nonce
                    idx, text = self.get_current()
                    self._handle_button_press_filtered(idx, text)

    def _handle_button_press_filtered(self, idx: int, text: str):
        """
        Handle button press with continuous press filtering.
        Only fires on the first press of a sequence.
        """
        current_time_ms = time.time() * 1000
        
        # Check if this is a continuation of the same press action
        is_continuation = (self._last_button_press_index == idx)
        time_since_last_event = current_time_ms - self._last_button_press_time
        
        # IMPORTANT: Update the time of the last seen press event, regardless of acceptance.
        # This allows us to detect when the stream of press events has stopped.
        self._last_button_press_time = current_time_ms

        # If this is the same button and not enough time has passed, it's a continuous press.
        # We'll treat the debounce value as a "release timeout".
        if is_continuation and time_since_last_event < self._button_debounce_ms:
            # Suppress the event, as it's part of the same physical press.
            # print(f"🔇 Suppressed continuous press [{idx}]: {text} (event interval: {int(time_since_last_event)}ms)")
            return

        # This is a new press event (either a different button or enough time has passed).
        # Record the new index and fire the callback.
        self._last_button_press_index = idx
        
        try:
            # print(f"✅ Accepted new button press [{idx}]: {text}")
            self._cb_button_pressed(idx, text)
        except Exception:
            pass

    def _mark_connected(self):
        if not self._component_active:
            self._component_active = True
            if not self._connected_event.is_set():
                self._connected_event.set()

    def _fire_connected_once(self):
        # Fire only once per activation
        if self._component_active:
            try:
                self._cb_connected()
            except Exception:
                pass
