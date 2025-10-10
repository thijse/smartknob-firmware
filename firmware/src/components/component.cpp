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

    // Copy component ID and display name to inherited fields using bounded copy (nanopb may not null-terminate)
    {
        // component_id_
        size_t id_src_max = sizeof(component_config_.component_id);
        size_t id_len = strnlen(config.component_id, id_src_max);
        size_t id_dst_max = sizeof(component_id_) - 1;
        size_t id_copy_len = (id_len < id_dst_max) ? id_len : id_dst_max;
        memcpy(component_id_, config.component_id, id_copy_len);
        component_id_[id_copy_len] = '\0';

        // App::app_id mirrors the component_id_ (safe)
        size_t app_dst_max = sizeof(app_id) - 1;
        size_t app_len = strnlen(component_id_, app_dst_max);
        memcpy(app_id, component_id_, app_len);
        app_id[app_len] = '\0';

        // display_name_
        size_t dn_src_max = sizeof(component_config_.display_name);
        size_t dn_len = strnlen(config.display_name, dn_src_max);
        size_t dn_dst_max = sizeof(display_name_) - 1;
        size_t dn_copy_len = (dn_len < dn_dst_max) ? dn_len : dn_dst_max;
        memcpy(display_name_, config.display_name, dn_copy_len);
        display_name_[dn_copy_len] = '\0';
    }

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
