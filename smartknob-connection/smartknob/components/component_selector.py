from __future__ import annotations

"""
ComponentSelector helper

High-level selector that switches between existing component sessions:
- ToggleComponent
- MultipleChoiceSession

Features:
- Reuses a single SmartKnobConnection across component switches
- Optionally performs a fast device reset between selections by calling reset_connection while keeping the port open
  (fast path; may fail on Windows if port is already open – errors are caught and logged)
- Wires per-component callbacks
- Ensures only one component session is active at a time

Usage example:

    from smartknob.components import ComponentSelector
    from smartknob.connection import find_smartknob_ports
    import anyio

    async def main():
        port = find_smartknob_ports()[0]
        selector = ComponentSelector(port=port)

        # Select Toggle
        await selector.select_toggle(
            title="AzurionEye",
            off_label="Start",
            on_label="Stop",
            on_connected=lambda: print("Toggle ready"),
            on_state_changed=lambda s: print("state:", s),
            on_button_pressed=lambda s: print("press:", s),
        )

        # Switch to Multiple Choice with reset in between
        await selector.select_multiple_choice(
            title="Drink Selector",
            options=["Coffee", "Tea", "Water"],
            reset_between=True,
            on_connected=lambda: print("MC ready"),
            on_value_selected=lambda i, t: print("selected:", i, t),
            on_button_pressed=lambda i, t: print("press:", i, t),
        )

        await selector.run_forever()

    anyio.run(main)
"""

import anyio
from typing import Any, Callable, List, Optional, Tuple, Union

from ..protocol import SmartKnobConnection, reset_connection
from .toggle import ToggleComponent
from .multiple_choice import MultipleChoiceSession

ToggleCallbacks = Tuple[
    Optional[Callable[[], None]],            # on_connected
    Optional[Callable[[bool], None]],        # on_state_changed
    Optional[Callable[[bool], None]],        # on_button_pressed
]

MultipleChoiceCallbacks = Tuple[
    Optional[Callable[[], None]],            # on_connected
    Optional[Callable[[int, str], None]],    # on_value_selected
    Optional[Callable[[int, str], None]],    # on_button_pressed
]


class ComponentSelector:
    """
    Manage switching between ToggleComponent and MultipleChoiceSession on a single SmartKnobConnection.

    Notes on reset_between:
    - When reset_between=True, this helper will call reset_connection(self.port) while keeping the current
      serial port open. On Windows this may fail if the port is locked; failures are caught and logged.
    - After a reset attempt, we sleep briefly, and try to re-send 'q' to re-enter protobuf mode if the serial
      object is still available. This is a best-effort fast path, not guaranteed across all host setups.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        connection: Optional[SmartKnobConnection] = None,
        auto_reset: bool = False,
        on_raw_data: Optional[Callable[[bytes], None]] = None,
    ):
        if not port and not connection:
            raise ValueError("Provide either 'port' or an existing 'connection'.")

        self.port: Optional[str] = port or getattr(connection, "port", None)
        if self.port is None:
            raise ValueError("Unable to determine serial port for reset functionality.")

        self._owns_connection = connection is None
        self.connection: SmartKnobConnection = connection or SmartKnobConnection(self.port, auto_reset=auto_reset, on_raw_data=on_raw_data)

        self._active_session: Optional[Union[ToggleComponent, MultipleChoiceSession]] = None

    # ----- Lifecycle ---------------------------------------------------------

    async def ensure_connection_started(self):
        if not getattr(self.connection, "connected", False):
            await self.connection.start(switch_to_protobuf=True)

    async def stop(self):
        await self._stop_current_session()
        if self._owns_connection:
            try:
                await self.connection.stop()
            except Exception:
                pass

    async def run_forever(self):
        while True:
            await anyio.sleep(1.0)

    # ----- Public API: Select Components ------------------------------------

    async def select_toggle(
        self,
        *,
        component_id: str = "toggle",
        title: str = "Toggle",
        off_label: str = "Off",
        on_label: str = "On",
        initial_state: bool = False,
        snap_point: float = 0.5,
        snap_point_bias: float = 0.0,
        detent_strength_unit: float = 4.0,
        off_led_hue: int = 0,
        on_led_hue: int = 120,
        reset_between: bool = False,
        on_connected: Optional[Callable[[], None]] = None,
        on_state_changed: Optional[Callable[[bool], None]] = None,
        on_button_pressed: Optional[Callable[[bool], None]] = None,
        wait_timeout: float = 10.0,
    ) -> ToggleComponent:
        """
        Create and activate a ToggleComponent session, replacing any active session.
        """
        await self.ensure_connection_started()
        await self._stop_current_session()

        if reset_between:
            await self._fast_reset_device_best_effort()

        session = ToggleComponent(
            self.connection,
            component_id=component_id,
            title=title,
            off_label=off_label,
            on_label=on_label,
            initial_state=initial_state,
            snap_point=snap_point,
            snap_point_bias=snap_point_bias,
            detent_strength_unit=detent_strength_unit,
            off_led_hue=off_led_hue,
            on_led_hue=on_led_hue,
        )
        if on_connected:
            session.on_connected(on_connected)
        if on_state_changed:
            session.on_state_changed(on_state_changed)
        if on_button_pressed:
            session.on_button_pressed(on_button_pressed)

        await session.start(wait_timeout=wait_timeout)
        self._active_session = session
        return session

    async def select_multiple_choice(
        self,
        *,
        component_id: str = "multi_choice",
        title: str = "Select Option",
        options: Optional[List[str]] = None,
        wrap_around: bool = True,
        initial_index: int = 0,
        detent_strength_unit: float = 1.5,
        endstop_strength_unit: float = 1.5,
        led_hue: int = 200,
        reset_between: bool = False,
        on_connected: Optional[Callable[[], None]] = None,
        on_value_selected: Optional[Callable[[int, str], None]] = None,
        on_button_pressed: Optional[Callable[[int, str], None]] = None,
        wait_timeout: float = 10.0,
    ) -> MultipleChoiceSession:
        """
        Create and activate a MultipleChoiceSession, replacing any active session.
        """
        await self.ensure_connection_started()
        await self._stop_current_session()

        if reset_between:
            await self._fast_reset_device_best_effort()

        session = MultipleChoiceSession(
            self.connection,
            component_id=component_id,
            title=title,
            options=options or ["Option 1", "Option 2", "Option 3"],
            wrap_around=wrap_around,
            initial_index=initial_index,
            detent_strength_unit=detent_strength_unit,
            endstop_strength_unit=endstop_strength_unit,
            led_hue=led_hue,
        )
        if on_connected:
            session.on_connected(on_connected)
        if on_value_selected:
            session.on_value_selected(on_value_selected)
        if on_button_pressed:
            session.on_button_pressed(on_button_pressed)

        await session.start(wait_timeout=wait_timeout)
        self._active_session = session
        return session

    async def reset_device(self) -> bool:
        """
        Reset the device. Strategy:
        1) Try fast in-handle reset (keep port open, toggle RTS/DTR).
        2) If that fails (common on Windows), gracefully stop the connection,
           perform a hardware reset via reset_connection(port), then restart
           the same connection in protobuf mode.

        Returns:
            True if either fast or fallback reset likely succeeded, False otherwise.
        """
        # Stop any active session so we can safely restart the connection if needed.
        await self._stop_current_session()

        # Attempt fast reset first
        ok = await self._fast_reset_device_best_effort(verbose=True)
        if ok:
            return True

        # Fallback: fully stop the connection, perform reset, and restart
        port = self.port
        if not port:
            return False

        try:
            await self.connection.stop()
        except Exception:
            pass

        ok2 = False
        try:
            ok2 = await anyio.to_thread.run_sync(lambda: reset_connection(port))
        except Exception:
            ok2 = False

        # Give device time to boot and then restart connection into protobuf mode
        try:
            await anyio.sleep(1.5)
        except Exception:
            pass

        try:
            await self.connection.start(switch_to_protobuf=True)
        except Exception:
            # If restart fails, report fallback failure
            return False

        return ok2

    # ----- Internal helpers --------------------------------------------------

    async def _stop_current_session(self):
        if self._active_session is not None:
            try:
                await self._active_session.stop()
            except Exception:
                pass
            finally:
                self._active_session = None

    async def _fast_reset_device_best_effort(self, verbose: bool = False) -> bool:
        """
        Best-effort device reset without closing the port.

        Strategy:
        1) Prefer toggling RTS (and DTR low) on the current open serial handle if available.
           This avoids re-opening the port and works even when Windows locks the device.
        2) If no open handle is available, fall back to reset_connection(port) in a worker thread.
        3) After reset, attempt to re-enter protobuf mode by sending 'q' on the existing handle.

        Returns:
            True if a reset action likely succeeded, False otherwise.
        """
        ok = False

        # 1) Try in-handle reset via current serial handle (if available)
        proto = getattr(self.connection, "protocol", None)
        ser = getattr(proto, "serial", None) if proto is not None else None
        if ser is not None and getattr(ser, "is_open", False):
            try:
                # Ensure DTR low then pulse RTS high -> low
                try:
                    ser.dtr = False
                except Exception:
                    # Some drivers may not allow DTR; ignore
                    pass
                ser.rts = True
                await anyio.sleep(0.1)
                ser.rts = False
                # Allow ESP32 to boot
                await anyio.sleep(1.0)
                ok = True
            except Exception as e:
                if verbose:
                    print(f"⚠️ In-handle reset failed: {e}")

        # 2) If that didn't work, fallback to reset_connection(port)
        if not ok:
            port = self.port
            if not port:
                return False
            try:
                ok = await anyio.to_thread.run_sync(lambda: reset_connection(port))
            except Exception as e:
                if verbose:
                    print(f"⚠️ Fast reset failed: {e}")

        # 3) Best-effort: re-send 'q' to re-enter protobuf mode (if serial is still present)
        try:
            if ser is not None and getattr(ser, "is_open", False):
                ser.write(b"q")
                ser.flush()
        except Exception:
            # Non-fatal
            pass

        return ok