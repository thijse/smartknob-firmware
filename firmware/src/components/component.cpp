#include "component.h"
#include "../util.h"
#include <logging.h>
#include <string.h>

Component::Component(
    SemaphoreHandle_t mutex,
    const char *component_id) : App(mutex) // ✅ Call App constructor!
{
    // Copy component ID (ensure null termination)
    strlcpy(component_id_, component_id, sizeof(component_id_));
    
    // 🔧 FIX: Set the app_id field inherited from App - this is used for ID matching in ComponentManager!
    strlcpy(app_id, component_id, sizeof(app_id));

    // Initialize configuration to default state
    memset(&component_config_, 0, sizeof(component_config_));

    //LOGD("Component '%s': Base component created", component_id_);
}

// ========== Component Hardware Integration ==========
//
// Components now inherit from App and can use all App hardware integration methods:
//
// 1. Motor Control:
//    - this->motor_config = new_config;  // Set motor configuration
//    - this->triggerMotorConfigUpdate(); // Apply motor config via motor_notifier
//
// 2. Display Control:
//    - this->screen // LVGL screen object for display updates
//    - Use LVGL functions directly to update display
//
// 3. LED Control:
//    - Components should call RootTask LED methods or work with existing patterns
//    - The old direct queue approach has been replaced with App-style integration
//
// This follows the same pattern as SwitchApp, ClimateApp, etc.
//
