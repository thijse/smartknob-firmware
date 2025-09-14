# Task 7.2: Real-Time State Communication & RequestState Implementation

**Status prior to this test:**
 - way communication seems to be working see two_way_communication.py, yet not yet fully validated for all situations:
   -  Request knob state works, but only done once, not continuously called
   -  Request state call seems to be processed based on logs, but likely some code on firmware side to send response
   -  No howto / code best practice example to create callbacks on firmware side
 - Firmware not yet sending back state inside of app
**Date:** August 22, 2025

## 🎯 Task Overview

Implement missing RequestState callback functionality in SmartKnob firmware to enable real-time knob position tracking. This task establishes the foundation for all future callback-based communication features.

### Objectives
1. **Fix RequestState callback** - Enable on-demand knob state queries
2. **Establish callback patterns** - Create reusable framework for future features
3. **Enable position tracking** - Real-time knob rotation monitoring
4. **Document architecture** - Guide for future callback implementations

---

## 📊 Current Status Analysis

### ✅ What's Working Perfectly

**1. Basic Communication Pipeline**
- ✅ Serial connection and protobuf mode switching
- ✅ COBS encoding/decoding with CRC32 validation  
- ✅ Async communication using anyio (replaced threading)
- ✅ Clean exception handling and timeout management

**2. GET_KNOB_INFO Command (Complete)**
- ✅ Command sending and ACK reception
- ✅ Rich device information extraction:
  ```
  📦 KNOB INFORMATION:
     📋 Persistent Config (v2):
        🔧 Motor: ✅ Calibrated
           Zero Offset: 2.565, Direction: CW, Pole Pairs: 7
        📏 Strain Scale: 70.932594
     ⚙️ Settings (protocol v1):
        📺 Screen: Dim=True, Bright=19661-65535, Timeout=30000s
        💡 LED Ring: ✅ Enabled, Color: 16754176
        🚨 Beacon: ✅ Enabled
  ```

**3. Enhanced Python Tools**
- ✅ `two_way_communication.py` with message type visualization
- ✅ Command-line filtering (`--hide-logs`, `--show-only`)
- ✅ Professional output formatting with icons
- ✅ Comprehensive logging and debugging capabilities

### ❌ What's Not Working

**RequestState Functionality**
- ❌ Firmware missing `request_state_tag` callback registration
- ❌ No SmartKnobState responses to RequestState commands
- ❌ Position tracking not implemented

**Evidence from firmware logs:**
```
📝 [LOG] [serial_protocol_protobuf.cpp:170 - handlePacket] Unknown payload
```

This appears repeatedly for every RequestState command, confirming the missing callback.

---

## 🔍 Root Cause Analysis

### Firmware Message Handling

The firmware's `handlePacket()` function in `serial_protocol_protobuf.cpp` only handles:

1. **`smartknob_command_tag`** - Commands like GET_KNOB_INFO ✅
   ```cpp
   else if (pb_rx_buffer_.which_payload == PB_ToSmartknob_smartknob_command_tag)
   ```

2. **Registered tag callbacks** - Currently only:
   - `settings_tag` ✅
   - `strain_calibration_tag` ✅
   - **Missing:** `request_state_tag` ❌

### Protocol Structure

From `smartknob.proto`:
```protobuf
message ToSmartknob {
    oneof payload {
        RequestState request_state = 3;        // Needs TAG callback
        SmartKnobCommand smartknob_command = 5; // Uses COMMAND callback
    }
}
```

**The Issue:** RequestState uses tag 3, but no callback is registered for it.

---

## 📁 Key Files Reference

### Firmware Files (C++)

**`firmware/src/root_task.cpp`** - **PRIMARY FILE TO MODIFY**
- Lines ~200-220: Where callbacks are registered
- Current callbacks: `settings_tag`, `strain_calibration_tag`
- **Need to add:** `request_state_tag` callback

**`firmware/src/proto/serial_protocol_protobuf.cpp`**
- Line 170: Shows "Unknown payload" error
- `handlePacket()` function processes incoming messages
- `sendPBTxBuffer()` function sends responses

**`firmware/src/proto/serial_protocol_protobuf.h`**
- Protocol interface definitions
- `registerTagCallback()` method signature

### Python Files (Working)

**`smartknob-connection2/examples/two_way_communication.py`** - **TESTING TOOL**
- Enhanced communication tool with RequestState support
- Usage: `python examples/two_way_communication.py --request-state`
- Shows ACKs being received but no SmartKnobState responses

**`smartknob-connection2/smartknob/protocol.py`**
- Clean async protocol implementation
- RequestState message construction working

### Protocol Definitions

**`proto/smartknob.proto`**
- Message structure definitions
- SmartKnobState message format

**`smartknob-connection2/smartknob/proto_gen/smartknob_pb2.py`**
- Generated Python bindings (working)

---

## 🔧 Implementation Steps

### Step 1: Add RequestState Callback Registration

**File:** `firmware/src/root_task.cpp`

**Location:** Find the existing callback registrations (around lines 200-220):
```cpp
serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_settings_tag, [this](PB_ToSmartknob to_smartknob)
                                               { configuration_->setSettings(to_smartknob.payload.settings); });

serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_strain_calibration_tag, [this](PB_ToSmartknob to_smartknob)
                                               { sensors_task_->factoryStrainCalibrationCallback(to_smartknob.payload.strain_calibration.calibration_weight); });
```

**Add this callback:**
```cpp
serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_request_state_tag, [this](PB_ToSmartknob to_smartknob)
                                               { 
                                                   LOGI("=== REQUEST_STATE RECEIVED ===");
                                                   sendCurrentKnobState(); 
                                               });
```

### Step 2: Implement sendCurrentKnobState() Method

**File:** `firmware/src/root_task.cpp`

**Add this method to the RootTask class:**
```cpp
void RootTask::sendCurrentKnobState()
{
    LOGI("=== SENDING KNOB STATE ===");
    
    PB_SmartKnobState state = {};
    
    // Get current position from motor task
    if (motor_task_) {
        state.current_position = motor_task_->getCurrentPosition();
        state.sub_position_unit = motor_task_->getSubPositionUnit();
    }
    
    // Get press state from sensors
    if (sensors_task_) {
        state.press_nonce = sensors_task_->getPressNonce();
    }
    
    // Get current config
    if (configuration_) {
        state.has_config = true;
        state.config = configuration_->getCurrentKnobConfig();
    }
    
    // Send via protocol
    if (serial_protocol_protobuf_) {
        serial_protocol_protobuf_->sendKnobState(state);
    }
    
    LOGI("=== KNOB STATE SENT ===");
}
```

### Step 3: Add sendKnobState() to Protocol

**File:** `firmware/src/proto/serial_protocol_protobuf.cpp`

**Add this method:**
```cpp
void SerialProtocolProtobuf::sendKnobState(PB_SmartKnobState state)
{
    LOGI("=== SEND_KNOB_STATE START ===");
    pb_tx_buffer_ = {};
    pb_tx_buffer_.which_payload = PB_FromSmartKnob_smartknob_state_tag;
    pb_tx_buffer_.payload.smartknob_state = state;
    LOGI("Knob state prepared, position: %d", state.current_position);
    sendPBTxBuffer();
    LOGI("=== SEND_KNOB_STATE END ===");
}
```

**File:** `firmware/src/proto/serial_protocol_protobuf.h`

**Add method declaration:**
```cpp
void sendKnobState(PB_SmartKnobState state);
```

---

## 🧪 Testing Instructions

### Phase 1: Basic RequestState Response

**Test Command:**
```bash
cd smartknob-connection2
python examples/two_way_communication.py --duration 10 --request-state --state-interval 2.0
```

**Expected Before Fix:**
```
🔄 Requested knob state (attempt 1)
✅ [ACK] Command acknowledged (nonce=12345)
📝 [LOG] [serial_protocol_protobuf.cpp:170 - handlePacket] Unknown payload
```

**Expected After Fix:**
```
🔄 Requested knob state (attempt 1)
✅ [ACK] Command acknowledged (nonce=12345)
📝 [LOG] [root_task.cpp] === REQUEST_STATE RECEIVED ===
📝 [LOG] [serial_protocol_protobuf.cpp] === SEND_KNOB_STATE START ===
🎛️ KNOB STATE:
   Position: 0
   Sub-position: 0.000
   Press nonce: 1
```

### Phase 2: Position Tracking

**Test:** Manually rotate the knob while running:
```bash
python examples/two_way_communication.py --request-state --state-interval 1.0 --hide-logs
```
note that the app returns where the name of the generated log, in this case log statements coming from firmware are hidden


**Expected:** Position values should change as knob is rotated.

### Phase 3: Clean Output Testing

**Test:** Verify filtering works:
```bash
python examples/two_way_communication.py --show-only=ack,smartknob_state --request-state
```

**Expected:** Only ACKs and knob state messages displayed.

---

## 🏗️ Architecture suggestions for Future Development

### Callback Registration Pattern
Possible, but requires rigorous code review

**For any new message type:**
1. Define in `smartknob.proto`
2. Regenerate protobuf bindings
3. Register callback in `root_task.cpp`:
   ```cpp
   serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_your_message_tag, 
       [this](PB_ToSmartknob to_smartknob) { 
           handleYourMessage(to_smartknob.payload.your_message); 
       });
   ```

### Response Pattern

**For sending responses:**
1. Create response method in `serial_protocol_protobuf.cpp`
2. Set `pb_tx_buffer_.which_payload` to appropriate response tag
3. Call `sendPBTxBuffer()`

### Rate Limiting Considerations

**For future automatic updates:**
- Maximum rate for return: 20-50 Hz consider something like Snippets\doevery.cpp or if Freertos provides a better solution
- Minimum change threshold: 0.1 position units
- Use timer-based or change-detection triggers
- Implement in motor task or sensors task

---

## 🎯 Success Criteria

1. **RequestState commands receive SmartKnobState responses** (not just ACKs)
2. **Position values change when knob is rotated**
3. **No more "Unknown payload" errors in firmware logs**
4. **Python tool displays real-time position data**
5. **Pattern established for future callback implementations**

---

## 📚 Additional Resources

**Testing Tools:**
- `smartknob-connection2/examples/two_way_communication.py` - Main testing tool
- `smartknob-connection2/examples/basic_monitoring.py` - Basic communication test

**Log Files:**
- Check `smartknob_twoway_*.log` files for detailed communication logs
- Firmware logs show protocol processing details

**Protocol Documentation:**
- `smartknob-connection2/Documentation/PROTOCOL.md`
- `smartknob-connection2/Documentation/IMPLEMENTATION.md`

---

---

## 🎉 Results & Findings (COMPLETED - August 22, 2025)

### ✅ Task Completion Summary

**Status: COMPLETED** ✅  
All objectives achieved with additional performance optimization beyond original scope.

### 🏆 Key Achievements

**1. RequestState Callback Implementation**
- ✅ Successfully implemented missing `request_state_tag` callback in `firmware/src/root_task.cpp`
- ✅ Added `sendCurrentKnobState()` method for real-time state responses
- ✅ Implemented `sendKnobState()` in protocol layer (`serial_protocol_protobuf.cpp`)
- ✅ Eliminated "Unknown payload" errors completely

**2. Real-Time Position Tracking**
- ✅ Position values change smoothly as knob rotates
- ✅ Sub-position precision working (fractional position tracking)
- ✅ Multi-app support confirmed (blinds, climate, menu configurations)
- ✅ Press nonce tracking functional

**3. Performance Optimization (Bonus Achievement)**
- ✅ Identified and removed excessive debug logging (6 messages per RequestState)
- ✅ Achieved **10Hz sustainable update rate** (99% success rate)
- ✅ Established performance baseline for future development

### 📊 Performance Test Results

| Update Rate | Success Rate | Performance Level | Notes |
|-------------|-------------|------------------|-------|
| **1Hz** | 100% (30/30) | ✅ Perfect | Baseline performance |
| **2Hz** | 100% (30/30) | ✅ Perfect | Excellent performance |
| **10Hz** | 99% (99/100) | ✅ **Optimal** | **Recommended rate** |
| 50Hz | ~20% (50/250) | ⚠️ Limited | Bottleneck reached |
| 100Hz | ~10% (50/500) | ⚠️ Limited | Same ~10Hz actual rate |

**Key Finding:** 10Hz appears to be the optimal sustainable rate due to:
- Firmware processing overhead (protobuf encoding + serial transmission)
- Python logging overhead (console + file I/O)
- Serial bandwidth constraints at 921600 baud

### 🔧 Technical Implementation Details

**Firmware Changes:**
```cpp
// Added to root_task.cpp
serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_request_state_tag, 
    [this](PB_ToSmartknob to_smartknob) { sendCurrentKnobState(); });

void RootTask::sendCurrentKnobState() {
    PB_SmartKnobState state = latest_state_;
    state.press_nonce = press_count_;
    if (serial_protocol_protobuf_) {
        serial_protocol_protobuf_->sendKnobState(state);
    }
}
```

**Protocol Layer:**
```cpp
// Added to serial_protocol_protobuf.cpp
void SerialProtocolProtobuf::sendKnobState(PB_SmartKnobState state) {
    pb_tx_buffer_ = {};
    pb_tx_buffer_.which_payload = PB_FromSmartKnob_smartknob_state_tag;
    pb_tx_buffer_.payload.smartknob_state = state;
    sendPBTxBuffer();
}
```

### 🧪 Testing Validation

**Before Fix:**
```
🔄 Requested knob state (attempt 1)
✅ [ACK] Command acknowledged (nonce=12345)
📝 [LOG] Unknown payload  ❌
```

**After Fix:**
```
🔄 Requested knob state (attempt 1)
✅ [ACK] Command acknowledged (nonce=12345)
🎛️ KNOB STATE:  ✅
   Position: 25
   Sub-position: 0.802
   Press nonce: 1
   📋 Active Config: 'climate.climate'
```

### 🏗️ Architecture Established

**Callback Registration Pattern:**
- Template established for future message types
- Clean separation between tag callbacks and command callbacks
- Reusable pattern documented for Phase 8 development

**Response Pattern:**
- Standardized response method structure
- Proper protobuf buffer management
- Error-free serial transmission

### 🚀 Performance Recommendations

**For Real-Time Applications:**
- **Use 10Hz** for smooth position tracking
- **Use 1-2Hz** for monitoring applications to reduce system load
- **Avoid >10Hz rates** as they don't provide additional benefit

**For Future Development:**
- Implement automatic state broadcasting on position changes
- Use DoEvery pattern or FreeRTOS timers for rate limiting
- Consider change-detection triggers vs continuous polling

### 📈 Next Steps Identified

1. **Task 7.5: Automatic State Broadcasting**
   - Implement firmware-side automatic transmission on position changes
   - Add configurable rate limiting (max 10Hz)
   - Make Python polling optional via command-line argument

2. **Python Tool Enhancements**
   - Add `--polling` flag to make RequestState optional
   - Optimize logging performance for higher rates
   - Implement event-driven state reception

### 🎯 Success Criteria - ALL MET ✅

- [x] **RequestState commands receive SmartKnobState responses** (not just ACKs)
- [x] **Position values change when knob is rotated**
- [x] **No more "Unknown payload" errors in firmware logs**
- [x] **Python tool displays real-time position data**
- [x] **Pattern established for future callback implementations**
- [x] **Performance optimized to 10Hz sustainable rate**

---

**Next Task:** Task 7.5 - Implement automatic state broadcasting with smart rate limiting and change-detection triggers.
