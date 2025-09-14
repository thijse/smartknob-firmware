# Task 10.2: Investigate Message Loss/Delay in use_multiple_choice.py vs Raw Logging

## Problem Statement

The `examples/use_multiple_choice.py` script is experiencing message loss and delayed event processing, while the raw logging test script `tests/test_physical_working_with_raw_logging_multiple_choice.py` appears to receive all messages correctly. This suggests a difference in how the two scripts use the protocol layer or handle message processing.

## Symptoms

### In `examples/use_multiple_choice.py`:
1. **Missing intermediate values**: Not all knob rotation positions are displayed/processed
2. **Delayed button press events**: Button press events only appear when followed by a subsequent knob turn
3. **Event batching**: Multiple position changes sometimes appear together instead of individually?

### In `tests/test_physical_working_with_raw_logging_multiple_choice.py`:
- Appears to capture all events correctly (as evidenced by log file `smartknob_multiple_choice_20250901_124341.log`)
- No apparent message loss or delays

## Investigation Areas

### 1. Protocol Usage Differences
- **Message Callbacks**: Compare how each script sets up and handles `on_message` callbacks
- **Raw Data Callbacks**: The test script uses `on_raw_data` callback for logging - does this affect timing?
- **Connection Parameters**: Check if different connection settings affect message flow
- **Protocol Read Loop**: Investigate if there are differences in how the read loop is invoked



## Specific Files to Investigate

### Primary Files:
- `smartknob-connection2/examples/use_multiple_choice.py` (problematic)
- `smartknob-connection2/tests/test_physical_working_with_raw_logging_multiple_choice.py` (working)
- `smartknob-connection2/smartknob/protocol.py` (shared protocol layer)

### Evidence Files:
- `smartknob-connection2/smartknob_multiple_choice_20250901_124341.log` (raw logging output showing all events, check if indeed every selection number is in there, both in the raw logs as well as the unpacked protobuf packages)


