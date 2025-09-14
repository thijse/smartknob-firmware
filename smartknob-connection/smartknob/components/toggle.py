from __future__ import annotations

import anyio
import time
from anyio.abc import ObjectReceiveStream, ObjectSendStream
from typing import Callable, Optional, Tuple, Any

from ..protocol import SmartKnobConnection


class ToggleComponent:
    """
    High-level session for TOGGLE component.

    Responsibilities:
    - Prepare and send TOGGLE config using protocol helper
    - Manage async tasks: protocol.read_loop (producer) and a consumer that processes messages
    - Provide callbacks:
        - on_connected()
        - on_state_changed(state: bool)
        - on_button_pressed(state: bool)
    - Idempotent setup (skips re-sending same config)
    """

    # ----- Lifecycle -----------------------------------------------------

    def __init__(
        self,
        connection: SmartKnobConnection,
        component_id: str = "toggle",
        title: str = "Toggle",
        off_label: str = "Off",
        on_label: str = "On",
        initial_state: bool = False,
        snap_point: float = 0.7,
        snap_point_bias: float = 0.4,
        detent_strength_unit: float = 4.0,
        off_led_hue: int = 0,
        on_led_hue: int = 120,
    ):
        self.connection = connection
        self.component_id = component_id
        self.title = title
        self.off_label = off_label
        self.on_label = on_label
        self.initial_state = bool(initial_state)
        self.snap_point = float(snap_point)
        self.snap_point_bias = float(snap_point_bias)
        self.detent_strength_unit = float(detent_strength_unit)
        self.off_led_hue = int(off_led_hue)
        self.on_led_hue = int(on_led_hue)

        # Callbacks (user-provided)
        self._cb_connected: Callable[[], None] = lambda: None
        self._cb_state_changed: Callable[[bool], None] = lambda s: None
        self._cb_button_pressed: Callable[[bool], None] = lambda s: None

        # Internal state
        self._send_chan: ObjectSendStream[Any]
        self._recv_chan: ObjectReceiveStream[Any]
        self._send_chan, self._recv_chan = anyio.create_memory_object_stream(max_buffer_size=4000)

        self._tg: Optional[Any] = None
        self._connected_event = anyio.Event()
        self._last_setup_nonce: Optional[int] = None
        self._component_active: bool = False

        self._last_state: Optional[bool] = None
        self._last_press_nonce: int = -1

        # Button press deduplication
        self._last_button_press_time: float = 0
        self._button_debounce_ms: float = 1000  # 1s debounce window

        self._owns_connection: bool = False
        self._last_config_key: Optional[Tuple] = None

    async def __aenter__(self) -> "ToggleComponent":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    @classmethod
    async def connect(
        cls,
        port: str,
        auto_reset: bool = False,
        **kwargs,
    ) -> "ToggleComponent":
        """
        Convenience: open the connection and return a ready session usable as an async context manager.
        """
        conn = SmartKnobConnection(port, auto_reset=auto_reset)
        ok = await conn.start()
        if not ok:
            raise RuntimeError("Failed to connect to SmartKnob")

        session = cls(conn, **kwargs)
        session._owns_connection = True
        await session.start()
        return session

    async def start(self, wait_timeout: float = 10.0):
        """
        Start the session:
        - Wire fast on_message producer
        - Launch protocol.read_loop and consumer in a TaskGroup
        - Send TOGGLE setup and wait until connected (ACK or activation log)
        """
        proto = getattr(self.connection, "protocol", None)
        if proto is None:
            raise RuntimeError("SmartKnobConnection.protocol is not initialized. Call SmartKnobConnection.start() first or use ToggleComponent.connect().")

        self.connection.set_message_callback(self._on_message_fast)

        self._tg = await anyio.create_task_group().__aenter__()
        try:
            self._tg.start_soon(proto.read_loop)
            self._tg.start_soon(self._consumer_loop)
            await self._send_setup()

            with anyio.move_on_after(wait_timeout):
                await self._connected_event.wait()
            if self._connected_event.is_set():
                self._fire_connected_once()
        except BaseException:
            await self._cancel_task_group_safely()
            raise

    async def stop(self):
        """
        Stop the session and optionally the underlying connection if owned by this session.
        """
        await self._cancel_task_group_safely()
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

    def on_connected(self, cb: Callable[[], None]) -> "ToggleComponent":
        self._cb_connected = cb or (lambda: None)
        return self

    def on_state_changed(self, cb: Callable[[bool], None]) -> "ToggleComponent":
        self._cb_state_changed = cb or (lambda s: None)
        return self

    def on_button_pressed(self, cb: Callable[[bool], None]) -> "ToggleComponent":
        self._cb_button_pressed = cb or (lambda s: None)
        return self

    async def run_forever(self):
        """Simple helper to keep the session alive."""
        while True:
            await anyio.sleep(1.0)

    def get_current_state(self) -> bool:
        """Return the last known state."""
        return self._last_state if self._last_state is not None else self.initial_state

    # ----- Internal helpers ---------------------------------------------

    async def _send_setup(self):
        """Compose and send TOGGLE config using protocol helper, idempotently."""
        key = (
            self.component_id, self.title, self.off_label, self.on_label,
            self.initial_state, self.snap_point, self.snap_point_bias,
            self.detent_strength_unit, self.off_led_hue, self.on_led_hue,
        )
        if key == self._last_config_key:
            return

        self._connected_event = anyio.Event()
        self._component_active = False

        proto = getattr(self.connection, "protocol", None)
        if proto is None:
            raise RuntimeError("SmartKnobConnection.protocol is not initialized.")

        nonce = await proto.send_toggle(
            component_id=self.component_id,
            title=self.title,
            off_label=self.off_label,
            on_label=self.on_label,
            initial_state=self.initial_state,
            snap_point=self.snap_point,
            snap_point_bias=self.snap_point_bias,
            detent_strength_unit=self.detent_strength_unit,
            off_led_hue=self.off_led_hue,
            on_led_hue=self.on_led_hue,
        )
        self._last_setup_nonce = nonce
        self._last_config_key = key

    def _on_message_fast(self, msg):
        """Fast producer: push messages to the channel without blocking."""
        try:
            send_nowait = getattr(self._send_chan, "send_nowait", None)
            if callable(send_nowait):
                send_nowait(msg)
            else:
                pass
        except Exception:
            pass

    async def _consumer_loop(self):
        """Slow consumer: parse messages and emit events."""
        async for msg in self._recv_chan:
            try:
                msg_type = msg.WhichOneof("payload")
            except Exception:
                continue

            if msg_type == "ack":
                if self._last_setup_nonce is not None and msg.ack.nonce == self._last_setup_nonce:
                    self._mark_connected()
            elif msg_type == "log":
                if "Component mode active" in msg.log.msg:
                    self._mark_connected()

            if msg_type in ("smartknob_state", "knob"):
                state_msg = getattr(msg, "smartknob_state", None) or getattr(msg, "knob", None)
                if state_msg is None:
                    continue

                current_state = bool(getattr(state_msg, "current_position", self.initial_state))
                press_nonce = int(getattr(state_msg, "press_nonce", -1))

                if self._last_state is None or current_state != self._last_state:
                    self._last_state = current_state
                    try:
                        self._cb_state_changed(current_state)
                    except Exception:
                        pass

                if press_nonce >= 0 and press_nonce != self._last_press_nonce:
                    self._last_press_nonce = press_nonce
                    self._handle_button_press_filtered(self.get_current_state())

    def _handle_button_press_filtered(self, state: bool):
        """Handle button press with continuous press filtering."""
        current_time_ms = time.time() * 1000
        time_since_last_event = current_time_ms - self._last_button_press_time
        
        self._last_button_press_time = current_time_ms

        if time_since_last_event < self._button_debounce_ms:
            return

        try:
            self._cb_button_pressed(state)
        except Exception:
            pass

    def _mark_connected(self):
        if not self._component_active:
            self._component_active = True
            if not self._connected_event.is_set():
                self._connected_event.set()

    def _fire_connected_once(self):
        if self._component_active:
            try:
                self._cb_connected()
            except Exception:
                pass
