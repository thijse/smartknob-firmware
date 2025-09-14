# Task: Rewrite ComponentManager Following Apps Pattern

## 🎯 **Objective**
ComponentManager is tasked with creating and intializing Components just Like Apps is for apps. Differences are that components are more configurable (though constructor) and these components are selected using the protobufserial interface, rather than MQTT and UI for the apps

Nevertheless we want to bring the code as much in line as possible:
Rewrite ComponentManager to follow the exact same architectural pattern as Apps, ensuring proper motor configuration updates and system integration. (The current ComponentManager implementation fails at setting the motor settings correctly)

## 📋 **Prerequisites**
- Previous task successfully identified that motor config is not reaching motor task
- ComponentManager needs to match Apps interface and integration patterns
- Must preserve all existing ComponentManager functionality

## 🔍 **Research Findings: Apps Integration Pattern**

### **Apps System Architecture:**

#### **1. Apps Creation & Lifecycle (DisplayTask)**
```cpp
// DisplayTask constructor
demo_apps = new CustomApps(mutex_);

// DisplayTask::enableDemo() - CRITICAL PATTERN
void DisplayTask::enableDemo() {
    display_os_mode = OSMode::RUNNING;
    demo_apps->render();                    // ⭐ IMMEDIATE render() call
    demo_apps->triggerMotorConfigUpdate();  // ⭐ IMMEDIATE motor config update
}
```

#### **2. Apps Notifier Setup (RootTask)**
```cpp
// RootTask constructor - Apps get notifiers set
display_task_->getApps()->setMotorNotifier(&motor_notifier);
display_task_->getApps()->setOSConfigNotifier(&os_config_notifier_);
```

#### **3. Apps Runtime Integration (RootTask main loop)**
```cpp
// State updates - Apps::update() called every 10ms
entity_state_update_to_send = display_task_->getApps()->update(app_state);

// Navigation handling - Apps handles button events
display_task_->getApps()->handleNavigationEvent(event);
```

#### **4. Apps Key Methods Pattern:**
```cpp
// Apps::setActive() - CRITICAL: calls render() immediately
void Apps::setActive(int8_t id) {
    active_app = apps[active_id];
    render();  // ⭐ ALWAYS calls render when setting active
}

// Apps::triggerMotorConfigUpdate() - Motor config pattern
void Apps::triggerMotorConfigUpdate() {
    if (motor_notifier != nullptr && active_app != nullptr) {
        motor_notifier->requestUpdate(active_app->getMotorConfig());
    }
}

// Apps::setMotorNotifier() - Propagates to all apps
void Apps::setMotorNotifier(MotorNotifier *motor_notifier) {
    this->motor_notifier = motor_notifier;
    for (auto& app : apps) {
        app.second->setMotorNotifier(motor_notifier);  // ⭐ PROPAGATES
    }
}

// Apps::update() - State update pattern with ID matching
EntityStateUpdate Apps::update(AppState state) {
    if (strcmp(state.motor_state.config.id, active_app->app_id) == 0) {
        new_state_update = active_app->updateStateFromKnob(state.motor_state);
        active_app->updateStateFromSystem(state);  // ⭐ ALSO calls updateStateFromSystem
    }
}
```

### **ComponentManager Current Integration:**

#### **1. ComponentManager Creation (RootTask)**
```cpp
// RootTask constructor
component_manager_ = new ComponentManager(mutex_);
component_manager_->setMotorNotifier(&motor_notifier);  // ✅ Gets notifier
```

#### **2. ComponentManager Runtime (RootTask main loop)**
```cpp
// State updates - ComponentManager::update() called when active
if (component_manager_ && component_manager_->getActiveComponent()) {
    entity_state_update_to_send = component_manager_->update(app_state);
}

// ❌ NO NAVIGATION HANDLING for ComponentManager (components use protobuf)
```

#### **3. ComponentManager Activation (RootTask protobuf handler)**
```cpp
// Component creation and activation via protobuf
bool success = component_manager_->createComponent(to_smartknob.payload.app_component);
if (success) {
    component_manager_->setActiveComponent(to_smartknob.payload.app_component.component_id);
}
```

## 🚨 **Key Missing Pieces in ComponentManager:**

### **1. Missing DisplayTask::enableDemo() Equivalent**
- Apps has `DisplayTask::enableDemo()` that calls both `render()` and `triggerMotorConfigUpdate()`
- ComponentManager activation only calls `setActiveComponent()` - no equivalent pattern

### **2. Missing Apps-Style Methods**
- ❌ No `ComponentManager::render()` method (should call `active_component_->render()`)
- ❌ No `ComponentManager::triggerMotorConfigUpdate()` method (should call `motor_notifier_->requestUpdate()`)
- ❌ Current `setActiveComponent()` doesn't call `render()` (Apps always calls render on activation)

### **3. Incomplete Interface Matching**
- ComponentManager should have same interface as Apps for system integration
- RootTask should be able to call ComponentManager methods same way it calls Apps methods

## 📋 **Implementation Plan**

### **Phase 1: File Restructuring**
1. **Backup Current Implementation:**
   ```bash
   mv firmware/src/components/component_manager.cpp firmware/src/components/component_manager.cpp.ref
   mv firmware/src/components/component_manager.h firmware/src/components/component_manager.h.ref
   ```

2. **Copy Apps as Base:**
   ```bash
   cp firmware/src/apps/apps.cpp firmware/src/components/component_manager.cpp
   cp firmware/src/apps/apps.h firmware/src/components/component_manager.h
   ```

### **Phase 2: Core Structure Transformation**

#### **2.1 Class Declaration (component_manager.h)**
```cpp
class ComponentManager 
{
public:
    ComponentManager(SemaphoreHandle_t mutex);
    
    // === APPS-PATTERN METHODS (keep these exactly) ===
    void render();                               // Like Apps::render()
    void triggerMotorConfigUpdate();             // Like Apps::triggerMotorConfigUpdate() 
    EntityStateUpdate update(AppState state);    // Like Apps::update()
    void setMotorNotifier(MotorNotifier *motor_notifier);  // Like Apps::setMotorNotifier()
    void setOSConfigNotifier(OSConfigNotifier *os_config_notifier); // Like Apps::setOSConfigNotifier()
    
    // === COMPONENT-SPECIFIC METHODS (migrate from .ref) suggestoins: ===
    bool createComponent(const PB_AppComponent &config);     // From original ComponentManager
    bool setActiveComponent(const std::string &component_id); // From original (but modify to call render())
    std::shared_ptr<Component> getActiveComponent();         // From original
    bool handleMessage(const PB_FromClient &message);       // From original
    bool setState(const std::string &component_id, const char *state_json); // From original
    std::string getState(const std::string &component_id);  // From original
    
    // === COLLECTION MANAGEMENT (Apps pattern) ===
    void clear();                                           // Like Apps::clear()
    std::shared_ptr<Component> find(const std::string &component_id); // Like Apps::find()

private:
    std::shared_ptr<Component> createComponentByType(PB_ComponentType type, const PB_AppComponent &config); // From original
    
    // === APPS-PATTERN STATE (keep these) ===
    SemaphoreHandle_t mutex_;                              // Like Apps::app_mutex_
    std::map<std::string, std::shared_ptr<Component>> components_; // Like Apps::apps (but string keys)
    std::shared_ptr<Component> active_component_;          // Like Apps::active_app
    MotorNotifier *motor_notifier_ = nullptr;             // Like Apps::motor_notifier
    OSConfigNotifier *os_config_notifier_ = nullptr;      // Like Apps::os_config_notifier_
    PB_SmartKnobConfig blocked_motor_config;              // Like Apps::blocked_motor_config
};
```

#### **2.2 Critical Method Implementations**

**Apps-Pattern Methods (copy exactly from Apps):**
```cpp
void ComponentManager::render() {
    if (active_component_) {
        active_component_->render();  // Like Apps calls active_app->render()
    }
}

void ComponentManager::triggerMotorConfigUpdate() {
    if (motor_notifier_ != nullptr) {
        if (active_component_ != nullptr) {
            motor_notifier_->requestUpdate(active_component_->getMotorConfig());
        } else {
            motor_notifier_->requestUpdate(blocked_motor_config);
            LOGW("ComponentManager: No active component");
        }
    } else {
        LOGW("ComponentManager: Motor notifier is not set");
    }
}

EntityStateUpdate ComponentManager::update(AppState state) {
    SemaphoreGuard lock(mutex_);
    EntityStateUpdate new_state_update;
    
    if (active_component_ != nullptr) {
        // Match component ID like Apps matches app_id
        if (strcmp(state.motor_state.config.id, active_component_->getComponentId()) == 0) {
            new_state_update = active_component_->updateStateFromKnob(state.motor_state);
            // Note: Components may not have updateStateFromSystem like Apps
        }
    }
    
    return new_state_update;
}

void ComponentManager::setMotorNotifier(MotorNotifier *motor_notifier) {
    motor_notifier_ = motor_notifier;
    
    // Propagate to all components (like Apps propagates to all apps)
    for (auto &pair : components_) {
        pair.second->setMotorNotifier(motor_notifier);
    }
}
```

**Modified setActiveComponent (CRITICAL - must call render()):**
```cpp
bool ComponentManager::setActiveComponent(const std::string &component_id) {
    SemaphoreGuard lock(mutex_);
    
    auto it = components_.find(component_id);
    if (it != components_.end()) {
        active_component_ = it->second;
        
        // ⭐ CRITICAL: Follow Apps::setActive pattern - call render() immediately
        render();
        
        LOGI("ComponentManager: Component '%s' set as active", component_id.c_str());
        return true;
    }
    
    LOGE("ComponentManager: Component '%s' not found", component_id.c_str());
    return false;
}
```

### **Phase 3: System Integration Updates**

#### **3.1 RootTask Integration (root_task.cpp)**
**Current ComponentManager activation:**
```cpp
// BEFORE (missing render and motor config)
component_manager_->setActiveComponent(component_id);
```

**NEW Apps-pattern activation:**
```cpp
// AFTER (following DisplayTask::enableDemo pattern)
if (component_manager_->setActiveComponent(component_id)) {
    // setActiveComponent now calls render() internally (like Apps::setActive)
    component_manager_->triggerMotorConfigUpdate();  // Like DisplayTask::enableDemo
}
```

#### **3.2 No Navigation Changes Needed**
- ComponentManager doesn't need `handleNavigationEvent()` - components use protobuf control
- RootTask already properly routes navigation to Apps when no component is active

### **Phase 4: Validation Requirements**

#### **4.1 Integration Checklist**
- [ ] ComponentManager created in RootTask constructor ✅ (already done)
- [ ] ComponentManager gets notifiers set ✅ (already done) 
- [ ] ComponentManager::update() called in main loop ✅ (already done)
- [ ] ComponentManager::setActiveComponent() calls render() (NEW)
- [ ] ComponentManager::triggerMotorConfigUpdate() implemented (NEW)
- [ ] ComponentManager activation calls triggerMotorConfigUpdate() (NEW)

#### **4.2 Functionality Preservation**
- [ ] Component creation via protobuf ✅ (preserve from .ref)
- [ ] Component state management ✅ (preserve from .ref)
- [ ] Component message handling ✅ (preserve from .ref)
- [ ] Thread safety with mutexes ✅ (preserve from .ref)

#### **4.3 Motor Config Flow Validation**
- [ ] ComponentManager::triggerMotorConfigUpdate() → MotorNotifier::requestUpdate() → MotorTask receives config
- [ ] Component activation triggers motor config update immediately
- [ ] Active component's getMotorConfig() called correctly

## 🎯 **Success Criteria**

### **Functional Requirements:**
1. **Motor Configuration Applied:** Components get proper endstops and haptic feedback
2. **System Integration:** ComponentManager works seamlessly with existing RootTask integration
3. **Backward Compatibility:** All existing component functionality preserved
4. **Architecture Consistency:** ComponentManager follows Apps pattern exactly

### **Testing Validation:**
1. **Physical Test:** ToggleComponent shows working endstops (position constrained to [0,1])
2. **Motor Config Test:** `motor_task.cpp` logs "Got new config" when component activated
3. **Haptic Test:** Strong detent feedback at snap points
4. **LED Test:** LED color changes based on component state

## 🔧 **Implementation Notes**

### **Critical Patterns to Preserve:**
1. **Apps::setActive() → render():** ComponentManager::setActiveComponent() must call render()
2. **DisplayTask::enableDemo() pattern:** Component activation must call triggerMotorConfigUpdate()
3. **Apps::setMotorNotifier() propagation:** Must propagate notifier to all components
4. **Apps::update() ID matching:** Must match component ID like Apps matches app_id

### **Key Differences from Apps:**
1. **Collection Keys:** Components use string IDs, Apps use integer IDs
2. **Navigation:** Components don't need handleNavigationEvent (protobuf controlled)
3. **Menu System:** Components don't need updateMenu() (no menu navigation)
4. **Component Types:** Components create via factory pattern vs Apps load via slug pattern

### **Files to Modify:**
1. `firmware/src/components/component_manager.h` - Class interface
2. `firmware/src/components/component_manager.cpp` - Implementation
3. `firmware/src/root_task.cpp` - Component activation to call triggerMotorConfigUpdate()

### **Files to Reference:**
1. `firmware/src/components/component_manager.cpp.ref` - Original functionality to preserve
2. `firmware/src/components/component_manager.h.ref` - Original interface to preserve
3. `firmware/src/apps/apps.cpp` - Pattern to follow exactly
4. `firmware/src/apps/apps.h` - Interface pattern to follow

## ⚠️ **Critical Implementation Order**

1. **FIRST:** Copy Apps files to ComponentManager location
2. **SECOND:** Rename class and includes but keep Apps structure intact
3. **THIRD:** Gradually modify collection type (int→string) and method signatures
4. **FOURTH:** Add back ComponentManager-specific methods from .ref
5. **FIFTH:** Test each integration point individually
6. **LAST:** Update RootTask component activation to call triggerMotorConfigUpdate()

## 📝 **Verification Commands**

After implementation, verify with physical test:
```bash
cd temp
python test_physical_working_with_raw_logging.py
```

**Expected logs indicating success:**
```
[motor_task.cpp:225] Got new config                    # Motor config received
ComponentManager: Triggering motor config update       # ComponentManager calling motor
ToggleComponent: State changed to ON/OFF              # Component state working
Component mode active: pos=X.XXX                      # Position constrained to [0,1]
```

## 🎯 **Next Task Dependencies**

This task enables:
- Proper motor configuration for all component types
- Working endstops and haptic feedback for components
- Consistent architecture between Apps and Components
- Foundation for additional component types (sliders, dimmers, etc.)

**This task is CRITICAL for motor configuration functionality and must be completed before any additional component development.**
