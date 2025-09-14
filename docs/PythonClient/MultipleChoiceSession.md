# MultipleChoiceSession (Python high-level API)

High-level helper to configure and use the MULTI_CHOICE component on the SmartKnob, keeping examples very small and readable.

This class abstracts:
- Sending the MULTI_CHOICE AppComponent (component_id, title, options, strengths, LED hue)
- Waiting for readiness (ACK or activation log)
- Emitting simple callbacks for connected, value changes, and button presses
- A fast-producer / slow-consumer pattern, so serial reading never blocks

Core implementation:
- Protocol helpers:
  - [SmartKnobProtocol.send_app_component()](../../smartknob-connection2/smartknob/protocol.py:479)
  - [SmartKnobProtocol.send_multi_choice()](../../smartknob-connection2/smartknob/protocol.py:489)
- High-level session:
  - [MultipleChoiceSession](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:43)
  - [MultipleChoiceSession.connect()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:110)
  - [MultipleChoiceSession.on_connected()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:217)
  - [MultipleChoiceSession.on_value_selected()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:221)
  - [MultipleChoiceSession.on_button_pressed()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:225)
  - [MultipleChoiceSession.run_forever()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:229)
  - [MultipleChoiceSession.update_options()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:236)

Minimal example
- See [examples/multiple_choice_simple.py](../../smartknob-connection2/examples/multiple_choice_simple.py:1)
- Roughly:
  1. Find the port
  2. Create a session with options
  3. Register simple callbacks
  4. Run forever

```python
from smartknob.highlevel import MultipleChoiceSession
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
```

Public API

- Construction and lifecycle
  - [MultipleChoiceSession.__init__()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:59)
    - Accepts an already-started SmartKnobConnection and MULTI_CHOICE parameters
  - [MultipleChoiceSession.connect()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:110)
    - Convenience classmethod: opens a connection, creates the session, sends setup, waits for readiness
  - Context manager support for automatic start/stop

- Callbacks (set at any time)
  - [MultipleChoiceSession.on_connected()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:217)
  - [MultipleChoiceSession.on_value_selected()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:221)
  - [MultipleChoiceSession.on_button_pressed()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:225)

- Runtime helpers
  - [MultipleChoiceSession.run_forever()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:229)
  - [MultipleChoiceSession.get_current()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:254)
  - [MultipleChoiceSession.update_options()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:236)
    - Re-sends config only when changed (idempotent)

How it determines readiness
- Primary: ACK correlation with the exact nonce used to send the setup (via [SmartKnobProtocol._handle_ack()](../../smartknob-connection2/smartknob/protocol.py:365))
- Fallback: Detects the firmware activation log message, same as in the advanced example ("Component mode active")

Keeping existing examples working
- The advanced example is preserved unchanged:
  - [examples/use_multiple_choice.py](../../smartknob-connection2/examples/use_multiple_choice.py:1)
  - It will continue to work, now alongside the simpler example:
  - [examples/multiple_choice_simple.py](../../smartknob-connection2/examples/multiple_choice_simple.py:1)

Migration from the advanced example
- Old approach in the example constructs the AppComponent manually and calls a private queue method:
  - [MultipleChoiceMonitor.create_multiple_choice_component()](../../smartknob-connection2/examples/use_multiple_choice.py:107)
  - Avoid calling private protocol methods and use the helper instead:
    - [SmartKnobProtocol.send_multi_choice()](../../smartknob-connection2/smartknob/protocol.py:489)
- Easiest path: replace the custom message loop and setup with the high-level session:
  1) Create the session using [MultipleChoiceSession.connect()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:110)
  2) Register callbacks [on_connected()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:217), [on_value_selected()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:221), [on_button_pressed()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:225)
  3) Call [run_forever()](../../smartknob-connection2/smartknob/highlevel/multiple_choice.py:229)

Design notes
- Uses AnyIO memory object streams to decouple the serial reader (fast producer) from the message consumer
- Idempotent configuration avoids unnecessary resends
- No firmware changes were required; uses existing MultipleChoice component behavior

Troubleshooting
- If you see linter/typing warnings on the generated protobuf classes (e.g. AppComponent, ToSmartknob), they are safe to ignore; they come from type stubs not matching generated modules.
- Ensure the device is switched to protobuf mode; the connection helper sends 'q' automatically via [SmartKnobProtocol.start()](../../smartknob-connection2/smartknob/protocol.py:144).