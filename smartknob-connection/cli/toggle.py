#!/usr/bin/env python3
"""
 High-level Toggle example using the component library.
"""

import os
import sys
import anyio

# Ensure we can import the local package when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(CURRENT_DIR)
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from smartknob.components import ToggleComponent
from smartknob.connection import find_smartknob_ports
from smartknob.protocol import reset_connection


async def main():
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return

    port = ports[0]
    print(f"📡 Found SmartKnob on: {port}")

    # Reset device to ensure clean protobuf mode and component state
    print("Resetting device... ")
    await anyio.to_thread.run_sync(lambda: reset_connection(port))

    async with await ToggleComponent.connect(
        port,
        auto_reset=True,
        title="AzurionEye",
        off_label="Start",
        on_label="Stop",
        detent_strength_unit=4.0,
        off_led_hue=0,
        on_led_hue=120,
    ) as ts:
        ts.on_connected(lambda: print("✅ Toggle ready"))
        ts.on_state_changed(lambda state: print(f"State changed -> {'ON' if state else 'OFF'}"))
        ts.on_button_pressed(lambda state: print(f"Button pressed! (state was {'ON' if state else 'OFF'})"))

        print("Rotate to change state; press the knob. Ctrl+C to exit.")
        await ts.run_forever()


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")
