#pragma once

#include "../component.h"

/**
 * Toggle Component - Based on proven SwitchApp implementation
 * 
 * Starting with SwitchApp's proven LVGL initialization pattern,
 * then gradually adding Component interface and protobuf configuration.
 */
class ToggleComponent : public Component
{
public:
    /**
     * Create toggle component with full configuration (like SwitchApp)
     * This eliminates the need for separate configure() step
     */
    ToggleComponent(SemaphoreHandle_t mutex, const PB_AppComponent &config);

    // ========== Component Interface ==========
    bool configure(const PB_AppComponent &config) override { return true; } // No-op since config is done in constructor
    const char *getComponentType() const override { return "toggle"; }
    
    // ========== State Interface ==========
    void setState(const char *state_json) override;
    const char *getState() override;

    // ========== App Interface (Inherited) ==========
    EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) override;

private:
    // ========== SwitchApp-style Implementation ==========
    void initScreen();
    
    // LVGL objects (like SwitchApp)
    lv_obj_t *arc_;
    lv_obj_t *status_label;
    
    // State tracking (like SwitchApp)
    uint8_t current_position = 0;
    uint8_t last_position = 0;
    float sub_position_unit = 0;
    long last_updated_ms = 0;
    bool first_run = false;
    
    // Component configuration (set once in constructor)
    PB_AppComponent component_config_;  // Full protobuf config for display_name etc.
    PB_ToggleConfig config_;           // Toggle-specific config
    bool configured_ = false;
    
    // State buffer for getState()
    char state_buffer_[128];
};
