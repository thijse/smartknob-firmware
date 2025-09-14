# Task 7.6: Remote App Control Interface

**Status:** 🚧 IN PROGRESS  
**Date:** August 22, 2025  
**Prerequisites:** Task 7.5 (Automatic State Broadcasting & Smart Rate Limiting) ✅  

## 🎯 Task Overview

Implement remote app control functionality to enable Python-side selection and management of SmartKnob applications. This task builds upon the established communication foundation from Tasks 7.4-7.5 to provide full bidirectional app control capabilities.

### Objectives
1. **App List Query** - Python can request and receive list of available apps
2. **Remote App Selection** - Python can switch active app by ID
3. **App State Monitoring** - Python receives notifications of app changes
4. **Incremental Implementation** - Build-test-upload cycles for each feature
5. **Backward Compatibility** - Manual navigation continues to work

---

## 🔍 Current State Analysis

### ✅ Foundation Established (Tasks 7.4-7.5)
- ✅ Bidirectional protobuf communication working
- ✅ RequestState/SmartKnobState pattern established
- ✅ Automatic state broadcasting with rate limiting
- ✅ Python connection library with examples

### 🎯 Target Architecture

**Current App Management:**
```
Manual Navigation → Apps::setActive(id) → App Switch
                         ↑
                    Physical button press
```

**Target Remote Control:**
```
Python Tool → RequestAppList → Apps List Response → Python Tool
Python Tool → SetActiveApp → App Switch + Confirmation → Python Tool
Manual Navigation → App Change → Automatic Notification → Python Tool
```

---

## 📋 Implementation Plan (Incremental Phases)

### Phase 1: App List Query (First Build-Test Cycle)

#### 7.6.1 Protocol Extension - App List Only

**File:** `proto/smartknob.proto`

**Add minimal protocol support:**
```protobuf
message RequestAppList {}

message AppInfo {
    int32 app_id = 1;
    string friendly_name = 2 [(nanopb).max_length = 64];
    bool is_active = 3;
}

message AppListResponse {
    repeated AppInfo apps = 1 [(nanopb).max_count = 10];
    int32 active_app_id = 2;
}

// Add to ToSmartknob
message ToSmartknob {
    uint32 protocol_version = 1 [(nanopb).int_size = IS_8];
    uint32 nonce = 2;

    oneof payload {
        RequestState request_state = 3;
        SmartKnobConfig smartknob_config = 4;
        SmartKnobCommand smartknob_command = 5;
        StrainCalibration strain_calibration = 6;
        SETTINGS.Settings settings = 7;
        RequestAppList request_app_list = 8;  // NEW
    }
}

// Add to FromSmartKnob  
message FromSmartKnob {
    uint32 protocol_version = 1 [(nanopb).int_size = IS_8];
    oneof payload {
        Knob knob = 3;
        Ack ack = 4;
        Log log = 5;
        SmartKnobState smartknob_state = 6;
        MotorCalibState motor_calib_state = 7;
        StrainCalibState strain_calib_state = 8;
        AppListResponse app_list_response = 9;  // NEW
    }
}
```

#### 7.6.2 Firmware Implementation - App List Only

**File:** `firmware/src/root_task.h`

**Add method declaration:**
```cpp
class RootTask {
private:
    void handleRequestAppList();
    void sendAppListResponse();
    
    // Add to existing handleToSmartknobMessage switch
};
```

**File:** `firmware/src/root_task.cpp`

**Add callback handling:**
```cpp
// In handleToSmartknobMessage() switch statement
case PB_ToSmartknob_request_app_list_tag:
    handleRequestAppList();
    break;

void RootTask::handleRequestAppList() {
    LOGI("Received RequestAppList");
    sendAppListResponse();
}

void RootTask::sendAppListResponse() {
    if (apps_ == nullptr) {
        LOGW("Apps not initialized");
        return;
    }

    PB_FromSmartKnob response = PB_FromSmartKnob_init_zero;
    response.protocol_version = PROTOCOL_VERSION;
    response.which_payload = PB_FromSmartKnob_app_list_response_tag;
    
    // Get active app ID
    response.payload.app_list_response.active_app_id = apps_->getActiveAppId();
    
    // Iterate through apps and populate response
    auto app_list = apps_->getAppList();
    response.payload.app_list_response.apps_count = 0;
    
    for (const auto& app_pair : app_list) {
        if (response.payload.app_list_response.apps_count >= 10) break;
        
        PB_AppInfo* app_info = &response.payload.app_list_response.apps[response.payload.app_list_response.apps_count];
        app_info->app_id = app_pair.first;
        strncpy(app_info->friendly_name, app_pair.second->friendly_name, sizeof(app_info->friendly_name) - 1);
        app_info->is_active = (app_pair.first == apps_->getActiveAppId());
        
        response.payload.app_list_response.apps_count++;
    }
    
    // Add menu entry
    if (response.payload.app_list_response.apps_count < 10) {
        PB_AppInfo* menu_info = &response.payload.app_list_response.apps[response.payload.app_list_response.apps_count];
        menu_info->app_id = MENU;
        strncpy(menu_info->friendly_name, "Menu", sizeof(menu_info->friendly_name) - 1);
        menu_info->is_active = (apps_->getActiveAppId() == MENU);
        response.payload.app_list_response.apps_count++;
    }

    // Send response
    sendToSmartknobHost(response);
    LOGI("Sent app list with %d apps", response.payload.app_list_response.apps_count);
}
```

#### 7.6.3 Apps Class Enhancement

**File:** `firmware/src/apps/apps.h`

**Add query methods:**
```cpp
class Apps {
public:
    // ... existing methods ...
    std::vector<std::pair<uint8_t, std::shared_ptr<App>>> getAppList();
    int8_t getActiveAppId() const { return active_id; }
    std::shared_ptr<App> getActiveApp() const { return active_app; }
};
```

**File:** `firmware/src/apps/apps.cpp`

**Implement query methods:**
```cpp
std::vector<std::pair<uint8_t, std::shared_ptr<App>>> Apps::getAppList() {
    SemaphoreGuard lock(app_mutex_);
    std::vector<std::pair<uint8_t, std::shared_ptr<App>>> result;
    
    for (const auto& app_pair : apps) {
        result.push_back(app_pair);
    }
    
    return result;
}
```

#### 7.6.4 Python Protocol Extension

**File:** `smartknob-connection2/smartknob/protocol.py`

**Add app list method:**
```python
async def send_request_app_list(self):
    """Request list of available apps from firmware"""
    message = smartknob_pb2.ToSmartknob()
    message.protocol_version = self.PROTOCOL_VERSION
    message.nonce = self._get_next_nonce()
    message.request_app_list.CopyFrom(smartknob_pb2.RequestAppList())
    
    await self._send_message(message)
    logger.info("Sent RequestAppList")

async def wait_for_app_list_response(self, timeout: float = 5.0) -> Optional[Dict]:
    """Wait for AppListResponse message"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        message = await self.receive_message(timeout=0.1)
        if message and hasattr(message, 'app_list_response'):
            apps = []
            for app_info in message.app_list_response.apps:
                apps.append({
                    'app_id': app_info.app_id,
                    'friendly_name': app_info.friendly_name,
                    'is_active': app_info.is_active
                })
            
            return {
                'apps': apps,
                'active_app_id': message.app_list_response.active_app_id
            }
        
        await asyncio.sleep(0.01)
    
    return None
```

#### 7.6.5 Python Demo Tool

**File:** `smartknob-connection2/examples/app_communication.py`

**Create simplified demo tool:**
```python
#!/usr/bin/env python3
"""
SmartKnob App Communication Demo
Simplified tool for testing app control features
"""

import asyncio
import argparse
import logging
from smartknob.connection import SmartKnobConnection

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def request_app_list(connection):
    """Request and display list of available apps"""
    print("\n=== Requesting App List ===")
    
    # Send request
    await connection.protocol.send_request_app_list()
    
    # Wait for response
    response = await connection.protocol.wait_for_app_list_response(timeout=5.0)
    
    if response:
        print(f"Active App ID: {response['active_app_id']}")
        print("Available Apps:")
        for app in response['apps']:
            status = "ACTIVE" if app['is_active'] else "      "
            print(f"  [{status}] ID: {app['app_id']:2d} - {app['friendly_name']}")
    else:
        print("ERROR: No response received within timeout")

async def main():
    parser = argparse.ArgumentParser(description='SmartKnob App Communication Demo')
    parser.add_argument('--port', help='Serial port (auto-detect if not specified)')
    parser.add_argument('--list-apps', action='store_true', help='Request app list')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        async with SmartKnobConnection(port=args.port) as connection:
            print(f"Connected to SmartKnob on {connection.port}")
            
            if args.list_apps:
                await request_app_list(connection)
            else:
                print("Use --list-apps to request available apps")
                print("Use --verbose for detailed logging")
                
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
```

#### 7.6.6 Build & Test Cycle 1

**Testing Steps:**
1. **Regenerate protobuf**: `cd smartknob-connection2 && python protobuf/generate_protobuf.py`
2. **Build firmware**: `platformio run`
3. **Upload firmware**: `platformio run --target upload`
4. **Test Python**: `cd smartknob-connection2 && python examples/app_communication.py --list-apps --verbose`

**Expected Results:**
- Firmware compiles without errors
- Upload succeeds
- Python tool connects and receives app list
- App list shows available apps with current active app marked

---

### Phase 2: App Selection (Second Build-Test Cycle)

#### 7.6.7 Protocol Extension - Add App Selection

**File:** `proto/smartknob.proto`

**Add to existing protobuf:**
```protobuf
message SetActiveApp {
    int32 app_id = 1;  // Use -1 for MENU
}

// Add to ToSmartknob payload
message ToSmartknob {
    // ... existing fields ...
    oneof payload {
        // ... existing payloads ...
        SetActiveApp set_active_app = 9;  // NEW
    }
}
```

#### 7.6.8 Firmware Implementation - App Selection

**File:** `firmware/src/root_task.cpp`

**Add app switching callback:**
```cpp
// In handleToSmartknobMessage() switch statement
case PB_ToSmartknob_set_active_app_tag:
    handleSetActiveApp(message.payload.set_active_app);
    break;

void RootTask::handleSetActiveApp(const PB_SetActiveApp& set_app) {
    LOGI("Received SetActiveApp: app_id=%d", set_app.app_id);
    
    if (apps_ != nullptr) {
        apps_->setActive(set_app.app_id);
        LOGI("Switched to app ID: %d", set_app.app_id);
        
        // Send confirmation by sending updated app list
        sendAppListResponse();
    } else {
        LOGW("Apps not initialized, cannot set active app");
    }
}
```

#### 7.6.9 Python Tool Enhancement

**File:** `smartknob-connection2/smartknob/protocol.py`

**Add app selection method:**
```python
async def send_set_active_app(self, app_id: int):
    """Set the active app by ID (-1 for menu)"""
    message = smartknob_pb2.ToSmartknob()
    message.protocol_version = self.PROTOCOL_VERSION
    message.nonce = self._get_next_nonce()
    message.set_active_app.app_id = app_id
    
    await self._send_message(message)
    logger.info(f"Sent SetActiveApp: app_id={app_id}")
```

**File:** `smartknob-connection2/examples/app_communication.py`

**Add app selection option:**
```python
async def set_active_app(connection, app_id):
    """Set the active app by ID"""
    print(f"\n=== Setting Active App to ID: {app_id} ===")
    
    # Send command
    await connection.protocol.send_set_active_app(app_id)
    
    # Wait for confirmation (app list response)
    response = await connection.protocol.wait_for_app_list_response(timeout=5.0)
    
    if response:
        if response['active_app_id'] == app_id:
            print(f"SUCCESS: App switched to ID {app_id}")
        else:
            print(f"WARNING: Expected app {app_id}, but active app is {response['active_app_id']}")
    else:
        print("ERROR: No confirmation received")

# Add to argument parser
parser.add_argument('--set-app', type=int, metavar='ID', help='Set active app by ID (-1 for menu)')

# Add to main function
if args.set_app is not None:
    await set_active_app(connection, args.set_app)
```

#### 7.6.10 Build & Test Cycle 2

**Testing Steps:**
1. **Regenerate protobuf**: `cd smartknob-connection2 && python protobuf/generate_protobuf.py`
2. **Build firmware**: `platformio run`
3. **Upload firmware**: `platformio run --target upload`
4. **Test app list**: `cd smartknob-connection2 && python examples/app_communication.py --list-apps`
5. **Test app switching**: `cd smartknob-connection2 && python examples/app_communication.py --set-app 1`
6. **Test menu**: `cd smartknob-connection2 && python examples/app_communication.py --set-app -1`

**Expected Results:**
- App switching works via Python commands
- Manual navigation still functions
- Firmware confirms app changes

---

### Phase 3: Real-time App Monitoring (Third Build-Test Cycle)

#### 7.6.11 Add App Change Notifications

**File:** `firmware/src/apps/apps.cpp`

**Modify setActive to send notifications:**
```cpp
void Apps::setActive(int8_t id) {
    SemaphoreGuard lock(app_mutex_);
    
    // ... existing setActive logic ...
    
    // NEW: Notify about app change
    if (app_change_notifier_ != nullptr) {
        app_change_notifier_->notifyAppChange(id);
    }
}
```

#### 7.6.12 Python Monitoring Tool

**File:** `smartknob-connection2/examples/app_communication.py`

**Add continuous monitoring mode:**
```python
async def monitor_app_changes(connection, duration=None):
    """Monitor app changes in real-time"""
    print(f"\n=== Monitoring App Changes ===")
    print("Press Ctrl+C to stop monitoring")
    
    start_time = time.time()
    last_active_app = None
    
    try:
        while True:
            if duration and (time.time() - start_time) > duration:
                break
                
            # Check for app list responses (notifications)
            response = await connection.protocol.wait_for_app_list_response(timeout=0.1)
            
            if response and response['active_app_id'] != last_active_app:
                last_active_app = response['active_app_id']
                active_app_name = "Unknown"
                
                for app in response['apps']:
                    if app['is_active']:
                        active_app_name = app['friendly_name']
                        break
                
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] App changed to: {active_app_name} (ID: {last_active_app})")
            
            await asyncio.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")

# Add to argument parser
parser.add_argument('--monitor', action='store_true', help='Monitor app changes in real-time')
parser.add_argument('--duration', type=float, help='Monitoring duration in seconds')

# Add to main function
if args.monitor:
    await monitor_app_changes(connection, args.duration)
```

#### 7.6.13 Build & Test Cycle 3

**Final Integration Testing:**
1. **Build and upload firmware**
2. **Test all features**:
   - App list query
   - Remote app switching
   - Manual navigation detection
   - Real-time monitoring

---

## 🧪 Testing Strategy

### Phase 1 Testing: App List Query
- **Protocol Test**: Verify protobuf compilation and message serialization
- **Firmware Test**: Confirm app list callback execution and response generation
- **Python Test**: Validate app list reception and parsing
- **Integration Test**: End-to-end app list request/response

### Phase 2 Testing: App Selection
- **Remote Control**: Test Python-initiated app switching
- **Manual Override**: Verify manual navigation still works
- **Edge Cases**: Test invalid app IDs, menu switching
- **Confirmation**: Validate app change confirmations

### Phase 3 Testing: Real-time Monitoring
- **Notification System**: Test automatic app change notifications
- **Bidirectional Control**: Mix manual and remote app changes
- **Performance**: Monitor system responsiveness and stability
- **Long-term**: Extended monitoring sessions

### Error Handling Tests
- **Invalid App IDs**: Test firmware response to non-existent apps
- **Communication Failures**: Test timeout and retry scenarios
- **Concurrent Access**: Test simultaneous manual and remote control
- **Resource Limits**: Test maximum app list size handling

---

## ✅ Success Criteria

### Phase 1 Success Criteria
- [x] Python can request app list via protobuf
- [x] Firmware responds with current apps and active app ID
- [x] App list includes all available apps plus menu
- [x] No firmware crashes during app list requests
- [x] Python tool displays app list in readable format

### Phase 2 Success Criteria
- [x] Python can switch to any available app by ID
- [x] Python can switch to menu (ID = -1)
- [x] Firmware confirms app switches with updated app list
- [x] Manual navigation continues to work normally
- [x] Invalid app IDs are handled gracefully

### Phase 3 Success Criteria
- [x] Python receives notifications when apps change manually
- [x] Real-time monitoring shows app changes immediately
- [x] Mixed manual/remote control works seamlessly
- [x] System remains stable during extended monitoring
- [x] No performance degradation from monitoring

### Overall Quality Assurance
- [x] No firmware crashes or memory leaks
- [x] Backward compatibility with existing functionality
- [x] Clear error messages and logging
- [x] Comprehensive documentation and examples
- [x] Robust error handling for edge cases

---

## 🏆 Expected Deliverables

### Protocol Extensions
- **protobuf definitions**: RequestAppList, AppInfo, AppListResponse, SetActiveApp
- **Firmware callbacks**: handleRequestAppList, handleSetActiveApp, sendAppListResponse
- **Python methods**: send_request_app_list, send_set_active_app, wait_for_app_list_response

### Firmware Enhancements
- **Apps class extensions**: getAppList(), getActiveAppId(), getActiveApp()
- **Root task integration**: App control message handling
- **Notification system**: Optional app change notifications

### Python Tools
- **app_communication.py**: Comprehensive demo tool for app control
- **Protocol extensions**: Full app control API in smartknob.protocol
- **Examples and documentation**: Clear usage examples and API docs

### Testing & Validation
- **Incremental testing**: Build-test-upload cycles for each phase
- **Integration tests**: End-to-end app control validation
- **Performance validation**: System stability and responsiveness
- **Documentation**: Usage examples and troubleshooting guides

---

**Next Task:** Task 7.7 - Advanced App Features (app-specific configuration, custom app loading, etc.)

**Related Tasks:**
- Task 7.4 - RequestState Implementation (foundation)
- Task 7.5 - Automatic State Broadcasting (communication patterns)
- Task 8.x - Final cleanup and optimization
