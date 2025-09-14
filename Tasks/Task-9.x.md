# Task 9.x: Component-Based Remote Configuration

## 🎯 **Overview**

Phase 9 transforms the SmartKnob from a fixed-app device into a dynamically configurable component system. Instead of hardcoded apps, the SmartKnob will accept remote configuration messages that define interactive components like toggles, sliders, and selectors with customizable haptic feedback and visual appearance.

## 🏗️ **Architecture Vision**

### **Component-Based Design**
```
Current:   Python → SmartKnobConfig (only motor behavior)
Future:    Python → AppComponent (complete UI + behavior)

Traditional Apps:     [LightDimmer] [Climate] [Blinds] [Switch]
Component System:     [ToggleComponent] [ContinuousComponent] [MultiChoiceComponent]
                           ↑                    ↑                      ↑
                     Configurable         Configurable           Configurable
```

### **Remote Configuration Flow**
```
Python Client                 SmartKnob Firmware
     │                              │
     ├─ AppComponent msg ──────────→ │ ComponentManager
     │  ├─ component_id             │ ├─ Create/Update Component
     │  ├─ ComponentType            │ ├─ Apply Configuration  
     │  └─ ToggleConfig             │ └─ Set as Active
     │                              │
     ├─ Visual Updates ←──────────── │ Component.render()
     └─ State Changes ←───────────── │ Component.updateState()
```

## 📋 **Current Status (Completed)**

### ✅ **9.1 Protocol & Infrastructure (COMPLETE)**

**What was accomplished:**
- **Component Protocol Design**: Created `AppComponent`, `ComponentType`, and `ToggleConfig` messages
- **Cross-Platform Generation**: Unified protobuf generator for Python + C++/nanopb
- **Protocol Integration**: Added `AppComponent` to `ToSmartknob.payload` oneof
- **Documentation**: Comprehensive protocol documentation with usage examples

**Key Implementation Decisions:**
1. **Hybrid Protocol Strategy**: Base `AppComponent` with type-specific configs via oneof
2. **Subset SmartKnobConfig**: Only relevant fields for component behavior
3. **Asymmetric Haptics**: `snap_point_bias` for intuitive toggle behavior
4. **Extensible Design**: Easy to add new component types

**Files Modified:**
- `proto/smartknob.proto` - Added component messages
- `smartknob-connection2/protobuf/generate_protobuf.py` - Unified generator
- `smartknob-connection2/regenerate_protobuf.py` - Convenience wrapper

**Current Message Structure:**
```protobuf
message ToSmartknob {
    oneof payload {
        // ... existing
        AppComponent app_component = 8;  // NEW
    }
}

message AppComponent {
    string component_id = 1;
    ComponentType type = 2;
    string display_name = 3;
    
    oneof component_config {
        ToggleConfig toggle = 4;
        // Future: ContinuousConfig, MultiChoiceConfig
    }
}

message ToggleConfig {
    string off_label = 1;
    string on_label = 2;
    float snap_point = 3;           // Rotation needed (0.3-1.0)
    float snap_point_bias = 4;      // Asymmetry (-1.0 to +1.0)
    float detent_strength_unit = 5; // Detent strength (0.0-1.0)
    int32 off_led_hue = 6;          // LED color when off
    int32 on_led_hue = 7;           // LED color when on
    bool initial_state = 8;         // Starting state
}
```

## 🚧 **Next Implementation Steps**

### **9.2 Toggle Component Implementation (IN PROGRESS)**

**Objective**: Create the first fully functional remote-configurable component

**Step-by-step Implementation Plan:**

#### **Step 2.1: Component Base Classes**
```cpp
// firmware/src/apps/components/component.h
class Component : public App {
public:
    Component(SemaphoreHandle_t mutex, const char* component_id);
    virtual bool configure(const PB_AppComponent& config) = 0;
    virtual void setState(const char* state_json) {}
    virtual const char* getState() { return "{}"; }
    const char* getComponentId() const { return component_id_; }
    
protected:
    char component_id_[33];
};
```

#### **Step 2.2: Toggle Component Implementation**
```cpp
// firmware/src/apps/components/toggle_component.h/cpp
class ToggleComponent : public Component {
    bool configure(const PB_AppComponent& config) override;
    EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) override;
    void render() override;
    
private:
    PB_ToggleConfig config_;
    bool current_state_;
    void updateKnobConfig();  // Apply haptic settings
    void updateDisplay();     // Update visual appearance
};
```

#### **Step 2.3: Protocol Handler Integration**
```cpp
// In root_task.cpp
serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_app_component_tag, 
    [this](PB_ToSmartknob to_smartknob) {
        bool success = component_manager_->createComponent(to_smartknob.app_component);
        if (success) {
            component_manager_->setActiveComponent(to_smartknob.app_component.component_id);
        }
        sendAck(to_smartknob.nonce, success);
    });
```

#### **Step 2.4: Component Manager**
```cpp
// firmware/src/apps/components/component_manager.h
class ComponentManager {
public:
    bool createComponent(const PB_AppComponent& config);
    Component* getComponent(const char* component_id);
    bool setActiveComponent(const char* component_id);
    Component* getActiveComponent();
    
private:
    std::map<std::string, std::unique_ptr<Component>> components_;
    Component* active_component_;
};
```

#### **Step 2.5: Python Test Client**
```python
# smartknob-connection2/examples/test_toggle_component.py
async def create_toggle_component(knob, component_id, config):
    msg = smartknob_pb2.ToSmartknob()
    msg.app_component.component_id = component_id
    msg.app_component.type = smartknob_pb2.ComponentType.TOGGLE
    msg.app_component.toggle.CopyFrom(config)
    await knob.send_message(msg)
```

### **Implementation Considerations & Decisions Made**

#### **1. Haptic Behavior Design**
**Decision**: Use `snap_point_bias` for asymmetric feedback
**Rationale**: 
- Provides intuitive UX (harder to accidentally activate dangerous states)
- Leverages existing SmartKnobConfig infrastructure
- Single parameter controls asymmetry direction and strength

**Examples**:
```python
# Door lock: Biased toward locked (safe state)
toggle_config.snap_point = 0.7
toggle_config.snap_point_bias = 0.3   # Harder to unlock

# Light switch: Biased toward on (convenience)  
toggle_config.snap_point = 0.5
toggle_config.snap_point_bias = -0.2  # Easier to turn on
```

#### **2. Component Lifecycle Management**
**Decision**: ComponentManager owns component instances
**Rationale**:
- Central control over component creation/destruction
- Easy switching between components
- Memory management and error handling

#### **3. Protocol Message Design**
**Decision**: Single `AppComponent` message with type-specific oneof configs
**Rationale**:
- Type safety (only appropriate config per component type)
- Extensible (easy to add new component types)
- Efficient (no unused fields)

#### **4. Integration with Existing App Framework**
**Decision**: Components extend `App` base class
**Rationale**:
- Reuses existing display, motor notification, and lifecycle infrastructure
- Minimal changes to existing codebase
- Smooth migration path from fixed apps to components

## 🔮 **Future Component Types (9.3-9.4)**

### **ContinuousConfig (Sliders/Dimmers)**
```protobuf
message ContinuousConfig {
    float min_value = 1;     // 0.0
    float max_value = 2;     // 100.0  
    float step_size = 3;     // 1.0
    string unit = 4;         // "%", "°C", "lux"
    float initial_value = 5;
    int32 led_hue = 6;       // Single color or gradient
}
```

### **MultiChoiceConfig (Selectors)**
```protobuf
message MultiChoiceConfig {
    repeated string options = 1;    // ["Off", "Heat", "Cool", "Auto"]
    uint32 initial_selection = 2;   // Index of default option
    bool wrap_around = 3;           // Can go from last to first
    repeated int32 option_colors = 4; // Per-option LED colors
}
```

## 🎯 **Success Criteria**

### **For 9.2 (Toggle Component)**
- [ ] Python client can create toggle components remotely
- [ ] Toggle responds to knob rotation with asymmetric haptic feedback
- [ ] Visual feedback changes based on toggle state
- [ ] Component state broadcasts back to Python on changes
- [ ] Multiple toggle components can coexist and be switched between

### **For Complete Phase 9**
- [ ] All three component types (Toggle, Continuous, MultiChoice) implemented
- [ ] Components support full visual customization (colors, labels)
- [ ] Component persistence across reboots
- [ ] Python library with helper functions for common component configurations
- [ ] Documentation and examples for all component types

## 📁 **File Structure (Planned)**

```
firmware/src/apps/
├── components/
│   ├── component.h              # Base component class
│   ├── component.cpp
│   ├── component_manager.h      # Component lifecycle management  
│   ├── component_manager.cpp
│   ├── toggle_component.h       # Toggle implementation
│   ├── toggle_component.cpp
│   ├── continuous_component.h   # Future: slider/dimmer
│   └── multi_choice_component.h # Future: selector
├── app.h                        # Existing app base class
└── apps.cpp                     # Integration point

smartknob-connection2/examples/
├── test_toggle_component.py     # Toggle component examples
├── test_continuous_component.py # Future: slider examples  
└── component_gallery.py        # Demo of all component types
```

## 🚨 **Known Challenges & Mitigation**

### **1. Memory Management**
**Challenge**: Dynamic component creation could cause memory fragmentation
**Mitigation**: 
- Pre-allocate component pool
- Implement component recycling
- Add memory usage monitoring

### **2. Display System Integration**  
**Challenge**: Existing apps assume fixed display layouts
**Mitigation**:
- Components own their screen regions
- Implement display virtualization layer
- Gradual migration from fixed to dynamic layouts

### **3. State Synchronization**
**Challenge**: Keeping Python client and firmware component state in sync
**Mitigation**:
- Implement reliable state broadcasting
- Add state reconciliation on reconnection
- Use nonce-based acknowledgment system

## 📚 **References & Dependencies**

### **Protobuf Generation**
- Use `python smartknob-connection2/regenerate_protobuf.py --all` after protocol changes
- Requires nanopb submodule: `git submodule update --init --recursive`

### **Testing Tools**
- `smartknob-connection2/examples/two_way_communication.py` - Basic protocol testing
- `smartknob-connection2/examples/basic_monitoring.py` - State monitoring

### **Related Documentation**
- `smartknob-connection2/Documentation/PROTOCOL.md` - Protocol specification
- `proto/smartknob.proto` - Message definitions with documentation
- Phase 8 task list - Cleanup required before component implementation

---

**Status**: Phase 9.1 complete, Phase 9.2 ready for implementation  
**Next Action**: Implement Component base class and ComponentManager  
**Estimated Effort**: 9.2 = ~2-3 days, Complete Phase 9 = ~2-3 weeks
