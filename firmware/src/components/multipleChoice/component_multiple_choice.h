#pragma once

#include "../component.h"
#include <vector>
#include <string>

/**
 * Multiple Choice Component - Based on proven ToggleComponent implementation
 *
 * Allows cycling through a user-defined list of text options using the knob.
 * Provides haptic feedback for each discrete position.
 */
class MultipleChoice : public Component {
public:
    /**
     * Create multiple choice component with full configuration (like ToggleComponent)
     * This eliminates the need for separate configure() step
     */
    MultipleChoice(SemaphoreHandle_t mutex, const PB_AppComponent &config);

    // ========== Component Interface ==========
    bool configure(const PB_AppComponent &config) override { return true; } // No-op since config is done in constructor
    const char *getComponentType() const override { return "multi_choice"; }

    // ========== State Interface ==========
    void setState(const char *state_json) override;
    const char *getState() override;

    // ========== App Interface (Inherited) ==========
    EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) override;
    void initScreen() override;  // Add this - matches ToggleComponent

    // ========== Multiple choice specific methods ==========
    int get_selected_index() const { return current_position; }
    const char* get_selected_text() const;

private:
    PB_AppComponent component_config_;
    PB_MultiChoiceConfig config_;
    bool configured_ = false;
    
    int current_position;
    int last_position;
    
    // LVGL objects (persistent like ToggleComponent)
    lv_obj_t* title_label_ = nullptr;
    lv_obj_t* option_label_ = nullptr;
    lv_obj_t* position_label_ = nullptr;
    
    void updateMotorConfigFromState();
    void updateDisplay(); // Updates persistent objects instead of render()
    void publishStateUpdate();
};
