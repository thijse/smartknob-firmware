# SmartKnob Component Development Guide

This guide explains how to create custom components for the SmartKnob firmware, using the ToggleComponent as a reference implementation.

## Overview

SmartKnob components provide interactive interfaces that combine:
- **Haptic feedback** through motor control
- **Visual display** using LVGL graphics
- **State management** via protobuf configuration
- **Communication** with external systems

Components inherit from the `Component` base class and follow the Apps architecture pattern for consistency and reliability.

## Component Architecture

### Base Classes

```cpp
// Component.h - Base class for all components
class Component : public App {
public:
    Component(SemaphoreHandle_t mutex, const char* component_id);
    
    // Component-specific interface
    virtual bool configure(const PB_AppComponent &config) = 0;
    virtual const char* getComponentType() const = 0;
    virtual void setState(const char* state_json) = 0;
    virtual const char* getState() = 0;
    
    // Inherited from App
    virtual EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) = 0;
    
protected:
    SemaphoreHandle_t mutex_;
    char component_id_[32];
    PB_SmartKnobConfig motor_config;
};
```

### ComponentManager Integration

Components are managed by the ComponentManager which follows the Apps pattern:

```cpp
// ComponentManager creates and manages component lifecycle
std::shared_ptr<Component> component = createComponentByType(config);
if (component && component->configure(config)) {
    active_component_ = component;
    // Component becomes active and receives knob input
}
```

## Creating a New Component

### 1. Define the Component Class

Create header file `your_component.h`:

```cpp
#pragma once
#include "../component.h"

class YourComponent : public Component {
public:
    YourComponent(SemaphoreHandle_t mutex, const PB_AppComponent &config);
    
    // Component interface
    bool configure(const PB_AppComponent &config) override;
    const char* getComponentType() const override { return "your_type"; }
    void setState(const char* state_json) override;
    const char* getState() override;
    
    // App interface
    EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) override;
    
private:
    void initScreen();
    
    // LVGL objects
    lv_obj_t* your_display_objects_;
    
    // State tracking
    int current_value_;
    bool configured_;
    
    // Configuration
    PB_YourComponentConfig config_;
    char state_buffer_[128];
};
```

### 2. Implement the Component

Create implementation file `your_component.cpp`:

```cpp
#include "your_component.h"
#include "../../util.h"
#include <logging.h>

YourComponent::YourComponent(SemaphoreHandle_t mutex, const PB_AppComponent &config) 
    : Component(mutex, config.component_id) {
    
    // Validate configuration
    if (config.type != PB_ComponentType_YOUR_TYPE) {
        LOGE("YourComponent: Invalid component type");
        return;
    }
    
    // Store configuration
    config_ = config.component_config.your_config;
    configured_ = true;
    
    // Initialize motor configuration
    motor_config = PB_SmartKnobConfig{
        0,                              // position
        0,                              // sub_position_unit  
        0,                              // position_nonce
        config_.min_value,              // min_position
        config_.max_value,              // max_position
        config_.step_size * PI / 180,   // position_width_radians
        config_.detent_strength,        // detent_strength_unit
        1,                              // endstop_strength_unit
        0.6,                            // snap_point
        "",                             // id
        0,                              // id_nonce
        {},                             // detent_positions
        0,                              // detent_positions_count
        config_.led_hue,                // led_hue
    };
    strncpy(motor_config.id, component_id_, sizeof(motor_config.id) - 1);
    
    // Initialize display
    initScreen();
}

bool YourComponent::configure(const PB_AppComponent &config) {
    // Configuration done in constructor for this pattern
    return configured_;
}

void YourComponent::initScreen() {
    // Create LVGL interface
    // Use SemaphoreGuard for thread safety
    SemaphoreGuard lock(mutex_);
    
    your_display_objects_ = lv_obj_create(screen);
    // ... LVGL setup code
}

EntityStateUpdate YourComponent::updateStateFromKnob(PB_SmartKnobState state) {
    EntityStateUpdate new_state = {};
    
    // Process knob input and update internal state
    int new_value = state.current_position;
    
    if (new_value != current_value_) {
        current_value_ = new_value;
        
        // Update display
        SemaphoreGuard lock(mutex_);
        // ... update LVGL objects
        
        // Update motor configuration if needed
        motor_config.led_hue = calculateLedHue(current_value_);
        triggerMotorConfigUpdate();
        
        // Prepare state update
        sprintf(new_state.app_id, "%s", component_id_);
        sprintf(new_state.entity_id, "%s", component_id_);
        sprintf(new_state.state, "{\"value\": %d}", current_value_);
        new_state.changed = true;
    }
    
    return new_state;
}

void YourComponent::setState(const char* state_json) {
    // Parse JSON state and update component
    // Example: {"value": 42}
}

const char* YourComponent::getState() {
    snprintf(state_buffer_, sizeof(state_buffer_), 
             "{\"value\": %d}", current_value_);
    return state_buffer_;
}
```

### 3. Add Protobuf Configuration

Define your component's configuration in `smartknob.proto`:

```protobuf
message YourComponentConfig {
    string title = 1;
    int32 min_value = 2;
    int32 max_value = 3;
    int32 initial_value = 4;
    float step_size = 5;
    float detent_strength = 6;
    int32 led_hue = 7;
}

// Add to AppComponent message
message AppComponent {
    string component_id = 1;
    ComponentType type = 2;
    string display_name = 3;
    
    oneof component_config {
        ToggleConfig toggle = 4;
        YourComponentConfig your_config = 5;  // Add your config here
    }
}

// Add to ComponentType enum
enum ComponentType {
    TOGGLE = 0;
    YOUR_TYPE = 1;  // Add your type here
}
```

### 4. Register with ComponentManager

Add your component to the ComponentManager factory:

```cpp
// In ComponentManager::createComponentByType()
switch (config.type) {
    case PB_ComponentType_TOGGLE:
        return std::make_shared<ToggleComponent>(mutex_, config);
    case PB_ComponentType_YOUR_TYPE:
        return std::make_shared<YourComponent>(mutex_, config);
    default:
        LOGE("Unknown component type: %d", config.type);
        return nullptr;
}
```

## ToggleComponent Example Analysis

The ToggleComponent demonstrates key patterns:

### Constructor-Based Configuration
```cpp
ToggleComponent::ToggleComponent(SemaphoreHandle_t mutex, const PB_AppComponent &config) 
    : Component(mutex, config.component_id) {
    
    // Validate configuration immediately
    if (config.type != PB_ComponentType_TOGGLE) {
        LOGE("ToggleComponent: Invalid component type");
        return;
    }
    
    // Store configuration and mark as configured
    config_ = config.component_config.toggle;
    configured_ = true;
    
    // Setup motor configuration based on user settings
    motor_config = PB_SmartKnobConfig{
        current_position,                    // Start position
        0,                                   // sub_position_unit
        current_position,                    // position_nonce
        0,                                   // min_position (OFF)
        1,                                   // max_position (ON)
        60 * PI / 180,                       // position_width_radians
        config_.detent_strength_unit,        // User-configurable strength
        1,                                   // endstop_strength_unit
        config_.snap_point,                  // User-configurable snap point
        "",                                  // id (set below)
        0,                                   // id_nonce
        {},                                  // detent_positions
        0,                                   // detent_positions_count
        current_position == 0 ? config_.off_led_hue : config_.on_led_hue, // LED color
    };
}
```

### Display Initialization
```cpp
void ToggleComponent::initScreen() {
    SemaphoreGuard lock(mutex_);
    
    // Create main display objects
    arc_ = lv_arc_create(screen);
    lv_arc_set_range(arc_, 0, 100);
    lv_arc_set_size(arc_, 200, 200);
    lv_obj_center(arc_);
    
    // Create status label with initial state
    status_label = lv_label_create(screen);
    const char* initial_label = current_position == 0 ? config_.off_label : config_.on_label;
    lv_label_set_text(status_label, initial_label);
    lv_obj_center(status_label);
}
```

### State Update Processing
```cpp
EntityStateUpdate ToggleComponent::updateStateFromKnob(PB_SmartKnobState state) {
    EntityStateUpdate new_state = {};
    
    // Calculate current position from knob state
    int calculated_position = state.current_position;
    
    // Check for position changes
    if (last_position != calculated_position && first_run) {
        SemaphoreGuard lock(mutex_);
        
        // Update display based on new position
        if (calculated_position == 0) {
            lv_label_set_text(status_label, config_.off_label);
            lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);
        } else {
            lv_label_set_text(status_label, config_.on_label);
            lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x80, 0x00), 0);
        }
        
        // Create state update for external systems
        sprintf(new_state.app_id, "%s", component_id_);
        sprintf(new_state.entity_id, "%s", component_id_);
        sprintf(new_state.state, "{\"state\": %s}", 
                calculated_position > 0 ? "true" : "false");
        new_state.changed = true;
        
        last_position = calculated_position;
        
        // Update LED color
        motor_config.led_hue = calculated_position == 0 ? config_.off_led_hue : config_.on_led_hue;
        
        // TODO: LED color switching not working - triggerMotorConfigUpdate() called but LEDs don't change color
        // Possible issues: motor task not processing led_hue changes, LED ring task needs different approach,
        // or timing issue with config updates. Need to investigate motor_task.cpp LED handling.
        triggerMotorConfigUpdate();
    }
    
    return new_state;
}
```

## Best Practices

### 1. Thread Safety
Always use `SemaphoreGuard lock(mutex_)` when accessing LVGL objects:

```cpp
void updateDisplay() {
    SemaphoreGuard lock(mutex_);
    lv_label_set_text(label, "New Text");
    lv_obj_invalidate(label);
}
```

### 2. Motor Configuration Updates
Call `triggerMotorConfigUpdate()` when motor behavior changes:

```cpp
// Update motor configuration
motor_config.detent_strength_unit = new_strength;
motor_config.led_hue = new_color;
triggerMotorConfigUpdate();  // Send to motor task
```

### 3. State Management
Provide JSON-based state interface for external integration:

```cpp
const char* getState() override {
    snprintf(state_buffer_, sizeof(state_buffer_), 
             "{\"position\": %d, \"enabled\": %s}", 
             current_position_, enabled_ ? "true" : "false");
    return state_buffer_;
}
```

### 4. Configuration Validation
Always validate configuration in the constructor:

```cpp
if (config.type != expected_type || !has_required_config) {
    LOGE("Component: Invalid configuration");
    configured_ = false;
    return;
}
```

### 5. Error Handling
Log errors appropriately and maintain component state:

```cpp
if (!some_operation()) {
    LOGE("Component: Operation failed");
    // Maintain valid state, don't crash
    return default_state;
}
```

## Integration Points

### ComponentManager
- Registers component types
- Creates component instances
- Manages component lifecycle
- Routes knob input to active component

### Motor Task
- Receives motor configuration updates
- Applies haptic feedback
- Controls LED ring colors
- Provides position feedback

### Root Task
- Processes component state updates
- Forwards states to external systems
- Handles component switching
- Manages communication protocol

### Display System
- Provides LVGL graphics context
- Handles screen refresh
- Manages UI threading
- Coordinates with other visual elements

## Debugging Tips

### 1. Enable Component Logging
```cpp
#define LOG_LOCAL_LEVEL ESP_LOG_DEBUG
#include <logging.h>

LOGD("Component: State changed to %d", new_state);
```

### 2. Monitor Motor Configuration
```cpp
LOGD("Motor config: pos=%d, strength=%.2f, hue=%d", 
     motor_config.position, motor_config.detent_strength_unit, motor_config.led_hue);
```

### 3. Test State Updates
```cpp
EntityStateUpdate state = updateStateFromKnob(test_knob_state);
LOGD("State update: %s -> %s", state.entity_id, state.state);
```

### 4. Validate LVGL Objects
```cpp
if (lv_obj_is_valid(your_object)) {
    lv_obj_set_style_whatever(your_object, value, 0);
} else {
    LOGE("LVGL object is invalid!");
}
```

This guide provides the foundation for creating robust, interactive SmartKnob components that integrate seamlessly with the existing firmware architecture.
