#!/usr/bin/env python3
"""
Select app and monitor value changes and button presses.

Simple CLI tool demonstrating remote app selection and event monitoring.
Shows how to use the SmartKnob library's callback-based event system.

Usage:
  python .\\cli\\select_app_and_monitor.py --id 1
  python .\\cli\\select_app_and_monitor.py --app-id climate
  python .\\cli\\select_app_and_monitor.py --id 1 --duration 60
"""

import os
import sys
import argparse
import anyio

# Ensure we can import the local package when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(CURRENT_DIR)
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from smartknob.connection import find_smartknob_ports
from smartknob.protocol import SmartKnobConnection


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Select app and monitor knob interactions")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", type=int, help="Select app by numeric id (0-255)")
    group.add_argument("--app-id", type=str, help="Select app by string app_id (max 32 chars)")
    parser.add_argument("--duration", type=float, default=30.0, 
                       help="Monitor duration in seconds (default: 30)")
    parser.add_argument("--timeout", type=float, default=3.0,
                       help="Timeout in seconds to wait for confirmation (default: 3.0)")
    
    return parser.parse_args()


async def main():
    args = parse_args()

    # Discover device
    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return

    port = ports[0]
    print(f"📡 Using SmartKnob on: {port}")

    # Create connection
    conn = SmartKnobConnection(port=port)

    # Register event callbacks
    conn.on_value_selected(
        lambda pos, sub: print(f"🔄 Value changed: position={pos}, sub={sub:.3f}")
    )
    conn.on_button_pressed(
        lambda pos: print(f"🔘 Button pressed at position={pos}")
    )

    # Track confirmation
    received_state = {"value": None}

    def on_message(msg):
        which = msg.WhichOneof("payload")
        if which == "smartknob_state":
            received_state["value"] = msg.smartknob_state

    try:
        async with anyio.create_task_group() as tg:
            # Start connection
            started = await conn.start(switch_to_protobuf=True)
            if not started:
                print("❌ Failed to connect")
                return

            # Set message callback and start read loop
            conn.set_message_callback(on_message)
            tg.start_soon(conn.start_read_loop)

            # Send app selection
            if args.id is not None:
                await conn.send_app_select(by_id=args.id)
                print(f"➡️ Sent app selection: by_id={args.id}")
            else:
                await conn.send_app_select(by_app_id=args.app_id)
                print(f"➡️ Sent app selection: by_app_id='{args.app_id}'")

            # Wait for confirmation
            try:
                with anyio.fail_after(args.timeout):
                    while received_state["value"] is None:
                        await anyio.sleep(0.01)
            except TimeoutError:
                print(f"⏱️ No confirmation within {args.timeout:.1f}s")
                return
            
            st = received_state["value"]
            app_id = getattr(st.config, "id", "")
            position = getattr(st, "current_position", 0)
            print(f"✅ App selected: '{app_id}' at position={position}")
            
            # Monitor for interactions
            print(f"\n👂 Monitoring for {args.duration:.1f}s...")
            print("   Turn the knob or press the button")
            print("   Press Ctrl+C to stop early\n")

            await anyio.sleep(args.duration)
            
            print(f"\n⏱️ Monitoring complete")
            tg.cancel_scope.cancel()
            
    except BaseException:
        pass
    finally:
        await conn.stop()


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")
