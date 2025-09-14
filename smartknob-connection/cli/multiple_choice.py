#!/usr/bin/env python3
"""
 MultipleChoice example

"""

import os
import sys
import anyio

# Ensure we can import the local package when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(CURRENT_DIR)
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from smartknob.components import MultipleChoiceSession
from smartknob.connection import find_smartknob_ports
from smartknob.protocol import reset_connection


async def main():
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return

    port = ports[0]
    options = ["collimate", "follow", "Auto EPX" ]
    # Reset the device
    # print("Resetting device... ")    
    # await anyio.to_thread.run_sync(lambda: reset_connection(port))


    async with await MultipleChoiceSession.connect(port, options=options, title="AzurionEye", auto_reset=True) as mc:

        mc.on_connected(lambda: print("✅ Multiple choice ready"))
        mc.on_value_selected(lambda i, t: print(f"Item   Selected [{i}]: {t}"))
        mc.on_button_pressed(lambda i, t: print(f"Button Pressed  [{i}]: {t}"))

        print("Rotate to change selection; press the knob to confirm. Ctrl+C to exit.")
        await mc.run_forever()


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")