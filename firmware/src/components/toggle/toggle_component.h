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
    bool configure(const PB_AppComponent &config) override { return configured_; } // Return current status
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

    // Configuration state (no redundant storage)
    bool configured_ = false;

    // Helper for clean access to typed config
    const PB_ToggleConfig &getConfig() const
    {
        return component_config_.component_config.toggle;
    }

    // State buffer for getState()
    char state_buffer_[128];
};
