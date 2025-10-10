#!/usr/bin/env python3
"""
Interactive component selector demo using ComponentSelector.

Design (simple and reliable in Windows/VSCode terminals):
- Show available keys immediately
- Main loop waits for a key (line) using blocking input() moved to a worker thread (so async tasks keep running)
- On selection:
  - Send the component selection via the ComponentSelector (which stops the active session and starts the new one)
  - Callbacks are attached per session; no manual (dis)connection of message callbacks needed
- Optional fast reset using selector.reset_device() (best effort)

Keys:
  1 - Toggle Variant A
  2 - Toggle Variant B
  3 - Multiple Choice Variant A
  4 - Multiple Choice Variant B
  r - Reset device (fast path, best-effort)
  q - Quit
"""

import os
import sys
import argparse
import anyio
from typing import List

# Ensure we can import the local package when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(CURRENT_DIR)
if PKG_ROOT not in sys.path:
    sys.path.insert(0, PKG_ROOT)

from smartknob.connection import find_smartknob_ports
from smartknob.components import ComponentSelector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive SmartKnob component selector (input() loop)")

    parser.add_argument(
        "--component",
        choices=["toggle", "multiple_choice"],
        default="toggle",
        help="Initial component to start",
    )

    # Generic options
    parser.add_argument("--reset-between", action="store_true", help="Reset device between selections (fast path)")
    parser.add_argument("--switch-to-other", action="store_true", help="Automatically switch to the other component after a short dwell")
    parser.add_argument("--dwell-seconds", type=float, default=2.0, help="Dwell seconds before auto-switch")

    # Toggle-specific options
    parser.add_argument("--toggle-title", type=str, default="AzurionEye")
    parser.add_argument("--off-label", type=str, default="Start")
    parser.add_argument("--on-label", type=str, default="Stop")
    parser.add_argument("--initial-state", action="store_true", help="Start toggle ON (default OFF)")
    parser.add_argument("--snap-point", type=float, default=0.5)
    parser.add_argument("--snap-point-bias", type=float, default=0.0)
    parser.add_argument("--toggle-detent-strength-unit", type=float, default=4.0)
    parser.add_argument("--off-led-hue", type=int, default=0)
    parser.add_argument("--on-led-hue", type=int, default=120)

    # Multiple-choice-specific options
    parser.add_argument("--mc-title", type=str, default="Drink Selector")
    parser.add_argument(
        "--options",
        type=str,
        default="Coffee,Tea,Water",
        help="Comma-separated list of options for multiple choice",
    )
    parser.add_argument("--initial-index", type=int, default=0)
    parser.add_argument("--wrap-around", action="store_true", help="Enable wrap-around in multiple choice")
    parser.add_argument("--mc-detent-strength-unit", type=float, default=1.5)
    parser.add_argument("--endstop-strength-unit", type=float, default=1.5)
    parser.add_argument("--led-hue", type=int, default=200)

    return parser.parse_args()


def make_toggle_variant_A_kwargs(args: argparse.Namespace) -> dict:
    return dict(
        component_id="toggle_1",
        title=args.toggle_title,
        off_label=args.off_label,
        on_label=args.on_label,
        initial_state=bool(args.initial_state),
        snap_point=float(args.snap_point),
        snap_point_bias=float(args.snap_point_bias),
        detent_strength_unit=float(args.toggle_detent_strength_unit),
        off_led_hue=int(args.off_led_hue),
        on_led_hue=int(args.on_led_hue),
    )


def make_toggle_variant_B_kwargs() -> dict:
    # A second variant with different feel and labels
    return dict(
        component_id="toggle_2",
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


def make_mc_variant_A_kwargs(args: argparse.Namespace) -> dict:
    opts: List[str] = [o.strip() for o in (args.options or "").split(",") if o.strip()]
    if not opts:
        opts = ["Coffee", "Tea", "Water"]
    return dict(
        component_id="mc_1",
        title=args.mc_title,
        options=opts,
        wrap_around=bool(args.wrap_around),
        initial_index=int(args.initial_index),
        detent_strength_unit=float(args.mc_detent_strength_unit),
        endstop_strength_unit=float(args.endstop_strength_unit),
        led_hue=int(args.led_hue),
    )


def make_mc_variant_B_kwargs() -> dict:
    # A second variant with different title/options/haptics
    return dict(
        component_id="mc_2",
        title="Procedures",
        options=["Collimate", "Follow", "Auto EPX"],
        wrap_around=True,
        initial_index=0,
        detent_strength_unit=0.8,
        endstop_strength_unit=0.8,
        led_hue=220,
    )


def print_banner():
    print("")
    print("Interactive keys:")
    print("  1 - Toggle Variant A")
    print("  2 - Toggle Variant B")
    print("  3 - Multiple Choice Variant A")
    print("  4 - Multiple Choice Variant B")
    print("  r - Reset device (fast path)")
    print("  q - Quit")
    print("")


async def auto_switch_once(selector: ComponentSelector, args: argparse.Namespace,
                           on_connected, on_toggle_state_changed, on_toggle_pressed,
                           on_mc_value_selected, on_mc_pressed):
    # Optional auto-switch in background; does not block input loop
    await anyio.sleep(max(0.0, args.dwell_seconds))
    try:
        if args.component == "toggle":
            # Switch to MC Variant A
            kwargs = make_mc_variant_A_kwargs(args)
            await selector.select_multiple_choice(
                **kwargs,
                reset_between=bool(args.reset_between),
                on_connected=on_connected,
                on_value_selected=on_mc_value_selected,
                on_button_pressed=on_mc_pressed,
            )
            print(f"🔁 Switched to Multiple Choice (Variant A) {'with' if args.reset_between else 'without'} reset")
        else:
            # Switch to Toggle Variant A
            kwargs = make_toggle_variant_A_kwargs(args)
            await selector.select_toggle(
                **kwargs,
                reset_between=bool(args.reset_between),
                on_connected=on_connected,
                on_state_changed=on_toggle_state_changed,
                on_button_pressed=on_toggle_pressed,
            )
            print(f"🔁 Switched to Toggle (Variant A) {'with' if args.reset_between else 'without'} reset")
    except Exception as e:
        print(f"⚠️ Auto-switch failed: {e}")


async def main():
    args = parse_args()

    ports = find_smartknob_ports()
    if not ports:
        print("❌ No SmartKnob devices found")
        return

    port = ports[0]
    print(f"📡 Using SmartKnob on: {port}")

    selector = ComponentSelector(port=port)

    # Define callbacks
    def on_connected():
        print("✅ Component ready")

    def on_toggle_state_changed(state: bool):
        print(f"State -> {'ON' if state else 'OFF'}")

    def on_toggle_pressed(state: bool):
        print(f"🔘 Toggle press (state was {'ON' if state else 'OFF'})")

    def on_mc_value_selected(i: int, t: str):
        print(f"Select [{i}]: {t}")

    def on_mc_pressed(i: int, t: str):
        print(f"🔘 Press [{i}]: {t}")

    # Track current selection and provide a single helper to (re)apply it
    current_kind = None  # one of: "toggleA", "toggleB", "mcA", "mcB"

    async def apply_selection(kind: str, use_reset_between: bool = True):
        nonlocal current_kind
        try:
            if kind == "toggleA":
                kwargs = make_toggle_variant_A_kwargs(args)
                await selector.select_toggle(
                    **kwargs,
                    reset_between=bool(use_reset_between),
                    on_connected=on_connected,
                    on_state_changed=on_toggle_state_changed,
                    on_button_pressed=on_toggle_pressed,
                )
                print(f"➡  Toggle Variant A{' (reset)' if use_reset_between else ''}")
            elif kind == "toggleB":
                kwargs = make_toggle_variant_B_kwargs()
                await selector.select_toggle(
                    **kwargs,
                    reset_between=bool(use_reset_between),
                    on_connected=on_connected,
                    on_state_changed=on_toggle_state_changed,
                    on_button_pressed=on_toggle_pressed,
                )
                print(f"➡  Toggle Variant B{' (reset)' if use_reset_between else ''}")
            elif kind == "mcA":
                kwargs = make_mc_variant_A_kwargs(args)
                await selector.select_multiple_choice(
                    **kwargs,
                    reset_between=bool(use_reset_between),
                    on_connected=on_connected,
                    on_value_selected=on_mc_value_selected,
                    on_button_pressed=on_mc_pressed,
                )
                print(f"➡  Multiple Choice Variant A{' (reset)' if use_reset_between else ''}")
            elif kind == "mcB":
                kwargs = make_mc_variant_B_kwargs()
                await selector.select_multiple_choice(
                    **kwargs,
                    reset_between=bool(use_reset_between),
                    on_connected=on_connected,
                    on_value_selected=on_mc_value_selected,
                    on_button_pressed=on_mc_pressed,
                )
                print(f"➡  Multiple Choice Variant B{' (reset)' if use_reset_between else ''}")
            else:
                print("Unknown kind; ignoring selection.")
                return
            current_kind = kind
        except Exception as e:
            print(f"💥 Selection failed: {e}")

    # Start initial component using the helper (no reset_between for first selection)
    if args.component == "toggle":
        await apply_selection("toggleA", use_reset_between=False)
        print("▶ Started with Toggle (Variant A)")
    else:
        await apply_selection("mcA", use_reset_between=False)
        print("▶ Started with Multiple Choice (Variant A)")

    print_banner()

    # Optional auto-switch once (sequential, no TaskGroup)
    if args.switch_to_other:
        try:
            await anyio.sleep(max(0.0, args.dwell_seconds))
            # Determine other kind based on the initial selection
            other_kind = "mcA" if (current_kind or ("toggleA" if args.component == "toggle" else "mcA")) in ("toggleA", "toggleB") else "toggleA"
            await apply_selection(other_kind, use_reset_between=args.reset_between)
            print(f"🔁 Auto-switched to {'Multiple Choice (Variant A)' if other_kind=='mcA' else 'Toggle (Variant A)'} {'with' if args.reset_between else 'without'} reset")
        except Exception as e:
            print(f"⚠️ Auto-switch failed: {e}")

    # Input loop: use a worker thread to avoid blocking the async scheduler
    while True:
        try:
            line = await anyio.to_thread.run_sync(lambda: input("Select [1/2/3/4/r/q]: ").strip())
        except (EOFError, KeyboardInterrupt):
            print("\n⏹️ Stopped by user")
            break

        if not line:
            continue
        ch = line[0].lower()

        try:
            if ch == "1":
                await apply_selection("toggleA", use_reset_between=args.reset_between)

            elif ch == "2":
                await apply_selection("toggleB", use_reset_between=args.reset_between)

            elif ch == "3":
                await apply_selection("mcA", use_reset_between=args.reset_between)

            elif ch == "4":
                await apply_selection("mcB", use_reset_between=args.reset_between)

            elif ch == "r":
                ok = await selector.reset_device()
                print("🔄 Device reset: " + ("OK" if ok else "FAILED (port may be locked on some systems)"))
                # After reset, re-apply current selection so the device is configured again
                if current_kind:
                    await apply_selection(current_kind, use_reset_between=False)
                    print("🔁 Re-applied current component after reset")

            elif ch == "q":
                print("⏹️  Quitting...")
                break

            else:
                print("Unknown selection. Use 1/2/3/4/r/q.")

        except Exception as e:
            print(f"💥 Selection failed: {e}")

    await selector.stop()


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\n⏹️ Stopped by user")
    except Exception as e:
        print(f"\n💥 Error: {e}")