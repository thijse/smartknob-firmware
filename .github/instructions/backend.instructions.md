---
applyTo: 'smartknob-connection/**'
---


### Python backend setup
- Create and activate a virtual environment:
  - Windows:
    - cd smartknob-connection
    - .\venv\Scripts\activate
    - if does not exist: python -m venv venv
- Install dependencies (assuming smartknob-connection is the current directory):
  - pip install -r /requirements.txt

Protobuf regeneration
- Canonical sources in [proto/](proto/smartknob.proto:1)
- Quick regenerate:
  - assuming smartknob-connection is the current directory and environment is activated:
  - [regenerate_protobuf.py](regenerate_protobuf.py:19) --python | --cpp | --all
- Advanced generator and targets:
  - [protobuf/generate_protobuf.py](smartknob-connection/protobuf/generate_protobuf.py:83)
- See detailed guidance: [docs/Firmware/protobuf.md](docs/Firmware/protobuf.md:1)

What you will build
- A Python process that discovers a SmartKnob over USB, starts an async protocol loop, receives FromSmartKnob messages, and sends commands/config or high-level components.

Core concepts and references
- Device discovery: [find_smartknob_ports()](smartknob-connection/smartknob/connection.py:28)
- Connection manager: [SmartKnobConnection](smartknob-connection/smartknob/protocol.py:593)
- Start/stop lifecycle: [SmartKnobConnection.start()](smartknob-connection/smartknob/protocol.py:617), [SmartKnobConnection.stop()](smartknob-connection/smartknob/protocol.py:641)
- Read loop task: [SmartKnobConnection.start_read_loop()](smartknob-connection/smartknob/protocol.py:729)
- Message callbacks: [SmartKnobConnection.set_message_callback()](smartknob-connection/smartknob/protocol.py:650), [SmartKnobConnection.set_raw_data_callback()](smartknob-connection/smartknob/protocol.py:655)
- Commands and settings: [SmartKnobProtocol.send_command()](smartknob-connection/smartknob/protocol.py:469), [SmartKnobProtocol.send_settings()](smartknob-connection/smartknob/protocol.py:487)
- App components (high-level UI): [SmartKnobProtocol.send_toggle()](smartknob-connection/smartknob/protocol.py:559), [SmartKnobProtocol.send_multi_choice()](smartknob-connection/smartknob/protocol.py:523)
- Protocol messages: [proto/smartknob.proto](proto/smartknob.proto:1)

Best practices (concise)
- When creating asynchronous tools, use `anyio` for structured concurrency. Here are the key patterns:
-  Basic Async Operations

  ```python
  import anyio

  async def my_async_function():
      # Sleep without blocking
      await anyio.sleep(1.0)
      
      # Perform async I/O
      result = await some_async_operation()
      return result
  ```
  - use Task Groups for Concurrent Operations

- E.g. use an AnyIO task group to:
  - Start the connection via [SmartKnobConnection.start()](smartknob-connection/smartknob/protocol.py:617)
  - Run [SmartKnobConnection.start_read_loop()](smartknob-connection/smartknob/protocol.py:729) as a background task
- Register callbacks early:
  - Use [SmartKnobConnection.set_message_callback()](smartknob-connection/smartknob/protocol.py:650) to consume FromSmartKnob (log/ack/knob/state)
  - Use [SmartKnobConnection.set_raw_data_callback()](smartknob-connection/smartknob/protocol.py:655) when diagnosing framing issues
- Prefer the component helpers to configure on-device UI quickly:
  - [SmartKnobProtocol.send_toggle()](smartknob-connection/smartknob/protocol.py:559) for two-state controls
  - [SmartKnobProtocol.send_multi_choice()](smartknob-connection/smartknob/protocol.py:523) for discrete options
- Keep retries simple:
  - The protocol already queues, assigns nonces, and clears entries on [ACK](smartknob-connection/smartknob/protocol.py:395); you typically only need to send once
- Reset behavior (ESP32 specifics):
  - Reset-at-close is determined at open; see [SmartKnobProtocol.start()](smartknob-connection/smartknob/protocol.py:174)
  - Use [SmartKnobConnection.reset_device()](smartknob-connection/smartknob/protocol.py:746) when you need a clean boot; be aware of "reset immunity" right after a connection

Minimal workflow (step-by-step)
- Discover a device with [find_smartknob_ports()](smartknob-connection/smartknob/connection.py:28)
- Create [SmartKnobConnection](smartknob-connection/smartknob/protocol.py:593) with the selected port
- Optionally call [SmartKnobConnection.set_message_callback()](smartknob-connection/smartknob/protocol.py:650) before starting
- Start the connection with [SmartKnobConnection.start()](smartknob-connection/smartknob/protocol.py:617)
- In a task group, run [SmartKnobConnection.start_read_loop()](smartknob-connection/smartknob/protocol.py:729)
- Send a command (e.g., GET_KNOB_INFO) using [SmartKnobProtocol.send_command()](smartknob-connection/smartknob/protocol.py:469)
- Optionally push UI components via [SmartKnobProtocol.send_toggle()](smartknob-connection/smartknob/protocol.py:559) or [SmartKnobProtocol.send_multi_choice()](smartknob-connection/smartknob/protocol.py:523)
- On shutdown, call [SmartKnobConnection.stop()](smartknob-connection/smartknob/protocol.py:641)



Troubleshooting
- Common serial/driver/protocol issues: [docs/PythonClient/TROUBLESHOOTING.md](docs/PythonClient/TROUBLESHOOTING.md:1)
- Protocol audit and tests live under smartknob-connection/tests; start with test_connection and protocol audits

Notes
- Paths and examples standardize on smartknob-connection
- Older references to smartknob-connection2 exist historically in some docs; for new work, use smartknob-connection
