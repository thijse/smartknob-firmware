#include "component.h"
#include "../util.h"
#include <logging.h>
#include <string.h>

Component::Component(
    SemaphoreHandle_t mutex,
    const PB_AppComponent &config) : App(mutex) // ✅ Call App constructor!
{
    // Store the full protobuf configuration (Nanopb static allocation handles strings safely)
    component_config_ = config;

    // Copy component ID to inherited fields
    strlcpy(component_id_, config.component_id, sizeof(component_id_));
    strlcpy(app_id, config.component_id, sizeof(app_id));

    LOGD("Component '%s': Base component created with type %d", component_id_, config.type);
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
