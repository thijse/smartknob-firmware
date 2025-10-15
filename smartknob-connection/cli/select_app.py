#!/usr/bin/env python3
"""
Minimal CLI to select a SmartKnob app from the host.  

Usage examples:
  python -m smartknob_connection.cli.select_app --id 1
  python -m smartknob_connection.cli.select_app --app-id climate
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
    parser = argparse.ArgumentParser(description="Select an app on the SmartKnob device and await one confirmation state, or run a mixed exercise while streaming logs")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--id", type=int, help="Select app by numeric id")
    group.add_argument("--app-id", type=str, help="Select app by string app_id")
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds to wait for confirmation state")
    parser.add_argument("--immediate", action="store_true", help="Send app_select via immediate path (bypass queue)")
    parser.add_argument("--also-request-state", action="store_true", help="Also send request_state immediately after app_select")
    # Mixed exercise flags (continuous alternating remote selections, with logs streaming)
    parser.add_argument("--mixed-exercise", action="store_true", help="Run continuous mixed selection loop and stream firmware logs")
    parser.add_argument("--exercise-seconds", type=float, default=75.0, help="Duration for mixed exercise in seconds (default: 75)")
    parser.add_argument("--dwell-seconds", type=float, default=1.0, help="Seconds to dwell between selections during mixed exercise (default: 1.0)")
    return parser.parse_args()


async def main():
    args = parse_args()

    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return

    port = ports[0]
    print(f"📡 Using SmartKnob on: {port}")

    conn = SmartKnobConnection(port=port)

    received_state = {"value": None}

    def on_message(msg):
        which = msg.WhichOneof("payload")
        if which == "log":
            try:
                lvl = msg.log.level
                origin = msg.log.origin
                m = msg.log.msg
                print(f"[FW:{lvl}] {origin}: {m}")
            except Exception:
                pass
        elif which == "smartknob_state":
            received_state["value"] = msg.smartknob_state

    async with anyio.create_task_group() as tg:
        started = await conn.start(switch_to_protobuf=True)
        if not started:
            print("❌ Failed to connect")
            return

        # Attach message callback and start read loop
        conn.set_message_callback(on_message)
        tg.start_soon(conn.start_read_loop)

        # Mixed exercise mode: continuously alternate selections and stream logs
        if args.mixed_exercise:
            try:
                dwell = max(0.1, float(getattr(args, "dwell_seconds", 1.0)))
                total = max(1.0, float(getattr(args, "exercise_seconds", 75.0)))
                iterations = int(total / (2.0 * dwell))
                if iterations < 1:
                    iterations = 1
                print(f"▶ Starting mixed exercise for ~{total:.1f}s (iterations={iterations}, dwell={dwell:.1f}s)")
                for i in range(iterations):
                    # by_id phase (use a fixed id=1 for exercise)
                    try:
                        await conn.send_app_select_immediate(by_id=1)
                        print("➡️ Sent app_select (by_id=1)")
                        if args.also_request_state:
                            await conn.send_request_state_immediate()
                    except Exception as e:
                        print(f"⚠️ by_id send failed: {e}")
                    await anyio.sleep(dwell)
                    # by_app_id phase (use a fixed app_id='climate' for exercise)
                    try:
                        await conn.send_app_select_immediate(by_app_id="climate")
                        print("➡️ Sent app_select (by_app_id=climate)")
                        if args.also_request_state:
                            await conn.send_request_state_immediate()
                    except Exception as e:
                        print(f"⚠️ by_app_id send failed: {e}")
                    await anyio.sleep(dwell)
                print("ℹ️ Mixed exercise complete")
            except Exception as e:
                print(f"💥 Mixed exercise failed: {e}")
            finally:
                tg.cancel_scope.cancel()
                await conn.stop()
            return

        # Single-shot selection: send once and await one confirmation
        try:
            if args.immediate:
                if args.id is not None:
                    await conn.send_app_select_immediate(by_id=args.id)
                else:
                    await conn.send_app_select_immediate(by_id=None, by_app_id=args.app_id)
            else:
                if args.id is not None:
                    await conn.send_app_select(by_id=args.id)
                else:
                    await conn.send_app_select(by_id=None, by_app_id=args.app_id)
            print(f"➡️ Sent app_select ({'by_id='+str(args.id) if args.id is not None else 'by_app_id='+args.app_id})")
        except Exception as e:
            print(f"💥 Failed to send app_select: {e}")
            tg.cancel_scope.cancel()
            await conn.stop()
            return

        # Optionally request state explicitly
        if args.also_request_state:
            try:
                await conn.send_request_state_immediate()
            except Exception:
                pass

        # Wait for one confirmation state
        try:
            with anyio.fail_after(max(0.1, float(args.timeout))):
                while received_state["value"] is None:
                    await anyio.sleep(0.01)
        except TimeoutError:
            print(f"⏱️ No confirmation state received within {args.timeout:.1f}s")
        else:
            st = received_state["value"]
            app_id = getattr(st.config, "id", "")
            print(f"✅ Confirmation: app_id='{app_id}' position={st.current_position} sub={st.sub_position_unit:.3f}")

        # Shutdown
        tg.cancel_scope.cancel()
        await conn.stop()


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")