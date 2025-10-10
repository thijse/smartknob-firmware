# Task: Diagnose intermittent failures when switching between Toggle and MultipleChoice components

Summary
- When switching from a Toggle component to a MultipleChoice component (and alternating back and forth), the device frequently fails to display the correct UI or reboots unexpectedly. In many runs, the script warns that it “Did not observe 'Component mode active' increment after MultipleChoice,” and raw serial logging indicates likely resets.

Scope
- Focus on transport integrity, firmware reception/activation of AppComponent payloads, and device stability during component switches.
- Provide reproducible steps and concrete artifacts (structured and raw logs) for analysis.
- Avoid presupposing a specific root cause in the main body of this task description.

Reproduction Steps
1. Connect the device via USB/serial and ensure no other process is accessing the port.
2. Run the alternating test:
   - python smartknob-connection/tests/toggle_then_multiple_choice.py
   - This connects once, sends Toggle, handshakes (GET_KNOB_INFO), sends MultipleChoice, and then alternates Toggle ↔ MultipleChoice indefinitely with dwell times.
3. Observe console output and consult the generated logs:
   - Structured log: [smartknob-connection/logs/toggle_then_multiple_choice/](smartknob-connection/logs/toggle_then_multiple_choice/)
   - Raw serial log: [smartknob-connection/logs/toggle_then_multiple_choice_raw/](smartknob-connection/logs/toggle_then_multiple_choice_raw/)

Objective Data Points
- Transport/ACK correlation:
  - The host generates nonces for outgoing frames and records ACKs from firmware, confirming correct frame delivery on the wire.
  - Observed behavior: ACKs are generally received for both Toggle and MultipleChoice dispatches, indicating physical delivery of frames.
- Firmware RX logging:
  - Structured logs contain firmware-emitted lines indicating COBS/CRC-validated frames were decoded and dispatched (e.g., RX payload_tag for AppComponent and summaries including component_id).
  - In some failing runs, the script logs: “Warning: Did not observe 'Component mode active' increment after MultipleChoice,” indicating firmware either did not complete activation or subsequently reset before reporting active state.
- UI activation marker:
  - The script tracks occurrences of “Component mode active” in firmware logs as an activation indicator. This is expected to increment on each successful switch.
  - Data point: After Toggle → handshake → MultipleChoice, the increment often fails to appear for the MultipleChoice transition, while Toggle activation is commonly observed.
- Raw serial logging:
  - A full raw (timestamp-prefixed) byte stream is recorded in a dedicated file for each run.
  - Example artifact called out by the user: [smartknob-connection/logs/toggle_then_multiple_choice_raw/smartknob_raw_20250914_171319.log](smartknob-connection/logs/toggle_then_multiple_choice_raw/smartknob_raw_20250914_171319.log)
  - Expectation: If resets/crashes occur, this file typically includes boot banners or panic traces interleaved with any printable logs.
- Single-session process:
  - The test avoids serial port re-open timing between separate processes by keeping a single connection alive for the full alternating run.
  - Data point: Failures are still observed within a single sustained session, ruling out inter-process timing effects.
- Handshake check:
  - A GET_KNOB_INFO handshake precedes MultipleChoice dispatch in the alternating loop, and its ACK is tracked, confirming the link is alive immediately before the failing switch.
- Haptic parameters:
  - The test uses detent/endstop strengths ≤ 1.0 to remain within documented safe ranges and reduce the chance of instability from excessive motor strength.
  - Despite this, the issue still reproduces sometimes during the MultipleChoice switch.

Tools Used (and where)
- Host test scripts:
  - Alternating stress test with structured and raw logging:
    - [smartknob-connection/tests/toggle_then_multiple_choice.py](smartknob-connection/tests/toggle_then_multiple_choice.py)
      - Generates two logs:
        - Structured: [smartknob-connection/logs/toggle_then_multiple_choice/](smartknob-connection/logs/toggle_then_multiple_choice/)
        - Raw: [smartknob-connection/logs/toggle_then_multiple_choice_raw/](smartknob-connection/logs/toggle_then_multiple_choice_raw/)
  - Reference raw-logging tests (patterns reused for robust capture):
    - [smartknob-connection/tests/test_physical_working_with_raw_logging_toggle.py](smartknob-connection/tests/test_physical_working_with_raw_logging_toggle.py)
    - [smartknob-connection/tests/test_physical_working_with_raw_logging.py](smartknob-connection/tests/test_physical_working_with_raw_logging.py)
  - Multiple choice example with decoupled message processing and ACK tracking:
    - [smartknob-connection/tests/use_multiple_choice.py](smartknob-connection/tests/use_multiple_choice.py)
- Protocol layer:
  - Async protocol with COBS+CRC32 framing, nonce/ACK queue, raw data callback, and read loop:
    - [smartknob-connection/smartknob/protocol.py](smartknob-connection/smartknob/protocol.py)
- Firmware (for context of logging and component activation path):
  - Protobuf serial protocol (decodes frames, ACKs nonces, logs RX summaries):
    - [firmware/src/proto/serial_protocol_protobuf.cpp](firmware/src/proto/serial_protocol_protobuf.cpp)
  - Root task component handling and activation:
    - [firmware/src/root_task.cpp](firmware/src/root_task.cpp)
  - Component manager lifecycle (create/destroy/reconfigure, render, motor config updates):
    - [firmware/src/components/component_manager.cpp](firmware/src/components/component_manager.cpp)
  - Component implementations:
    - MultipleChoice: [firmware/src/components/multipleChoice/component_multiple_choice.cpp](firmware/src/components/multipleChoice/component_multiple_choice.cpp)
    - Toggle: [firmware/src/components/toggle/toggle_component.cpp](firmware/src/components/toggle/toggle_component.cpp)

Key Artifacts Generated Per Run
- Structured log (text):
  - Directory: [smartknob-connection/logs/toggle_then_multiple_choice/](smartknob-connection/logs/toggle_then_multiple_choice/)
  - Contains:
    - ENQUEUED lines with nonces for AppComponent and handshake command
    - ✅ ACK lines correlating with nonces
    - 📝 LOG lines from firmware (RX summaries, component activation markers)
    - Warnings if activation markers are not observed for a switch
- Raw serial log (binary with timestamp prefixes):
  - Directory: [smartknob-connection/logs/toggle_then_multiple_choice_raw/](smartknob-connection/logs/toggle_then_multiple_choice_raw/)
  - Example provided: [smartknob-connection/logs/toggle_then_multiple_choice_raw/smartknob_raw_20250914_171319.log](smartknob-connection/logs/toggle_then_multiple_choice_raw/smartknob_raw_20250914_171319.log)
  - Intended to capture crash/reset signatures (e.g., boot banners, panic traces) and any interleaved text logs

Observed Patterns (from current runs)
- Toggle usually activates; MultipleChoice intermittently fails to activate.
- The script often warns: “Did not observe 'Component mode active' increment after MultipleChoice.”
- Anecdotal observation from the user: the device appears to crash/reset at or shortly after switching to MultipleChoice.
- Raw log presence requested by the user suggests resets are indeed occurring in those runs.

Acceptance Criteria for Resolution
- Alternating test runs for at least 10 minutes without:
  - Missing activation increments when switching to MultipleChoice
  - Device resets/reboots or panic signatures in raw serial log
- Structured log shows consistent:
  - ACKs for each submitted AppComponent
  - Firmware RX log lines for app_component with the correct component_id
  - “Component mode active” increments after each switch
- Raw serial log shows no reset/boot banners or panic traces during the run.

Attachments / References
- Alternating test script: [smartknob-connection/tests/toggle_then_multiple_choice.py](smartknob-connection/tests/toggle_then_multiple_choice.py)
- Example raw log mentioned by user: [smartknob-connection/logs/toggle_then_multiple_choice_raw/smartknob_raw_20250914_171319.log](smartknob-connection/logs/toggle_then_multiple_choice_raw/smartknob_raw_20250914_171319.log)
- Supporting raw-logging patterns:
  - [smartknob-connection/tests/test_physical_working_with_raw_logging_toggle.py](smartknob-connection/tests/test_physical_working_with_raw_logging_toggle.py)
  - [smartknob-connection/tests/test_physical_working_with_raw_logging.py](smartknob-connection/tests/test_physical_working_with_raw_logging.py)
- Protocol implementation: [smartknob-connection/smartknob/protocol.py](smartknob-connection/smartknob/protocol.py)
- Firmware context (for RX/logging/activation path):
  - [firmware/src/proto/serial_protocol_protobuf.cpp](firmware/src/proto/serial_protocol_protobuf.cpp)
  - [firmware/src/root_task.cpp](firmware/src/root_task.cpp)
  - [firmware/src/components/component_manager.cpp](firmware/src/components/component_manager.cpp)
  - [firmware/src/components/multipleChoice/component_multiple_choice.cpp](firmware/src/components/multipleChoice/component_multiple_choice.cpp)
  - [firmware/src/components/toggle/toggle_component.cpp](firmware/src/components/toggle/toggle_component.cpp)

Next Steps (analysis workflow suggestion)
- Parse the referenced raw log for reset signatures and correlate timestamps with structured log events (nonces, RX lines, activation markers).
- If resets are confirmed, scope whether they happen:
  - Immediately upon receiving/processing MultipleChoice app_component
  - During motor config application or UI render
  - During knob state update immediately after activation
- If no resets are present, consider path where activation is silently failing (e.g., resource exhaustion or task deadlock) and expand firmware-side logging around component creation/activation and motor update triggers.

---

Conjectures (Separate; safe to remove before handing off for unbiased analysis)
- MultipleChoice-related stability issues during motor configuration or UI rendering may still be present under certain sequences or timings, even with reduced haptic strengths (≤ 1.0).
- A race or timing sensitivity in the component manager lifecycle (destroy/recreate vs. reconfigure) might intermittently prevent activation, leaving the system in a partially applied state that trips a watchdog or subsequent failure.
- Transport timing combined with immediate motor updates could cause brief spikes in workload leading to reset conditions (e.g., WDT if a critical loop stalls).
- An LVGL or display mutex contention pattern during re-render could stall a task long enough to trigger a watchdog under specific conditions.
- Power draw spikes from motor engagement when switching profiles could cause brownout-like behavior on marginal setups.