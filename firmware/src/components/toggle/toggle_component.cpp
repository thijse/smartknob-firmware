#include "toggle_component.h"
#include "../../util.h"
#include <logging.h>
#include <string.h>

ToggleComponent::ToggleComponent(
    SemaphoreHandle_t mutex,
    const char *component_id) : Component(mutex, component_id)
{
    LOGI("ToggleComponent '%s': Constructor using SwitchApp pattern", component_id);
    
    // Initialize with SwitchApp-style motor config
    motor_config = PB_SmartKnobConfig{
        current_position,  // position
        0,                 // sub_position_unit  
        current_position,  // position_nonce
        0,                 // min_position
        1,                 // max_position
        60 * PI / 180,     // position_width_radians (same as SwitchApp)
        1,                 // detent_strength_unit
        1,                 // endstop_strength_unit
        0.55,              // snap_point (same as SwitchApp)
        "",                // id
        0,                 // id_nonce
        {},                // detent_positions
        0,                 // detent_positions_count
        27,                // led_hue
    };
    strncpy(motor_config.id, component_id, sizeof(motor_config.id) - 1);
    
    // Set default toggle config
    memset(&config_, 0, sizeof(config_));
    strcpy(config_.off_label, "OFF");
    strcpy(config_.on_label, "ON");
    config_.snap_point = 0.55f;
    config_.detent_strength_unit = 1.0f;
    config_.off_led_hue = 0;   // Red
    config_.on_led_hue = 120;  // Green
    config_.initial_state = false;
    
    // Initialize state buffer
    memset(state_buffer_, 0, sizeof(state_buffer_));
    
    // Initialize screen using SwitchApp's proven pattern
    LOGI("ToggleComponent '%s': Calling initScreen() from constructor", component_id);
    initScreen();
    
    LOGI("ToggleComponent '%s': Constructor completed successfully", component_id);
}

void ToggleComponent::initScreen()
{
    LOGI("ToggleComponent '%s': initScreen() using SwitchApp pattern", component_id_);
    
    // Use SwitchApp's proven LVGL initialization
    if (screen == nullptr) {
        LOGE("ToggleComponent '%s': screen is NULL!", component_id_);
        return;
    }
    
    SemaphoreGuard lock(mutex_);
    
    // Create arc (like SwitchApp)
    arc_ = lv_arc_create(screen);
    lv_obj_set_size(arc_, 210, 210);
    lv_arc_set_rotation(arc_, 225);
    lv_arc_set_bg_angles(arc_, 0, 90);
    lv_arc_set_value(arc_, 0);
    lv_obj_center(arc_);
    
    lv_obj_set_style_arc_opa(arc_, LV_OPA_0, LV_PART_INDICATOR);
    lv_obj_set_style_arc_color(arc_, dark_arc_bg, LV_PART_MAIN);
    lv_obj_set_style_bg_color(arc_, LV_COLOR_MAKE(0xFF, 0xFF, 0xFF), LV_PART_KNOB);
    
    lv_obj_set_style_arc_width(arc_, 24, LV_PART_MAIN);
    lv_obj_set_style_arc_width(arc_, 24, LV_PART_INDICATOR);
    lv_obj_set_style_pad_all(arc_, -5, LV_PART_KNOB);
    
    // Create status label (like SwitchApp) - always use text not images
    status_label = lv_label_create(screen);
    lv_label_set_text(status_label, config_.off_label);
    lv_obj_set_style_text_color(status_label, LV_COLOR_MAKE(0xFF, 0xFF, 0xFF), 0);
    lv_obj_center(status_label);
    
    // Create component name label
    lv_obj_t *label = lv_label_create(screen);
    lv_label_set_text(label, component_id_);
    lv_obj_align(label, LV_ALIGN_BOTTOM_MID, 0, -48);
    
    LOGI("ToggleComponent '%s': initScreen() completed successfully", component_id_);
}

bool ToggleComponent::configure(const PB_AppComponent &config)
{
    LOGI("ToggleComponent '%s': configure() called", component_id_);
    
    // Validate configuration
    if (config.type != PB_ComponentType_TOGGLE) {
        LOGE("ToggleComponent '%s': Invalid component type %d", component_id_, config.type);
        return false;
    }
    
    if (config.which_component_config != PB_AppComponent_toggle_tag) {
        LOGE("ToggleComponent '%s': Missing toggle configuration", component_id_);
        return false;
    }
    
    // Store configuration
    component_config_ = config;
    config_ = config.component_config.toggle;
    configured_ = true;
    
    // Update motor configuration with new settings
    motor_config.snap_point = config_.snap_point;
    motor_config.detent_strength_unit = config_.detent_strength_unit;
    motor_config.led_hue = current_position == 0 ? config_.off_led_hue : config_.on_led_hue;
    
    // Update display with new labels (if screen is initialized)
    if (status_label) {
        SemaphoreGuard lock(mutex_);
        lv_label_set_text(status_label, current_position == 0 ? config_.off_label : config_.on_label);
    }
    
    // Trigger motor update
    triggerMotorConfigUpdate();
    
    LOGI("ToggleComponent '%s': Configured successfully", component_id_);
    return true;
}

EntityStateUpdate ToggleComponent::updateStateFromKnob(PB_SmartKnobState state)
{
    // Use SwitchApp's proven updateStateFromKnob implementation
    EntityStateUpdate new_state;
    
    current_position = state.current_position;
    sub_position_unit = state.sub_position_unit * motor_config.position_width_radians;
    
    // Update motor config for tracking
    motor_config.position_nonce = current_position;
    motor_config.position = current_position;
    
    // Calculate velocity (like SwitchApp)
    static float previous_sub_position_unit = 0.0f;
    float vel = (sub_position_unit * 100 - previous_sub_position_unit * 100) / (millis() - last_updated_ms);
    
    // Update arc display (like SwitchApp)
    if (abs(vel) > 0.75f || current_position != last_position)
    {
        if (current_position == 0 && sub_position_unit < 0)
        {
            sub_position_unit = 0;
        }
        else if (current_position == 1 && sub_position_unit > 0)
        {
            sub_position_unit = 0;
        }

        SemaphoreGuard lock(mutex_);
        if (current_position == 0)
        {
            lv_arc_set_value(arc_, abs(sub_position_unit) * 100);
        }
        else
        {
            lv_arc_set_value(arc_, 100 - abs(sub_position_unit) * 100);
        }
    }
    else
    {
        if (current_position == 0)
        {
            lv_arc_set_value(arc_, 0);
        }
        else
        {
            lv_arc_set_value(arc_, 100);
        }
    }
    
    // Update display and LED on position change (like SwitchApp)
    if (last_position != current_position && first_run) {
        SemaphoreGuard lock(mutex_);
        
        if (current_position == 0) {
            lv_label_set_text(status_label, config_.off_label);
            lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);
            lv_obj_set_style_arc_color(arc_, dark_arc_bg, LV_PART_MAIN);
        } else {
            lv_label_set_text(status_label, config_.on_label);
            lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x80, 0x00), 0);
            lv_obj_set_style_arc_color(arc_, lv_color_mix(dark_arc_bg, LV_COLOR_MAKE(0x00, 0x80, 0x00), 128), LV_PART_MAIN);
        }
        
        // Create state update
        sprintf(new_state.app_id, "%s", component_id_);
        sprintf(new_state.entity_id, "%s", component_id_);
        sprintf(new_state.state, "{\"state\": %s}", current_position > 0 ? "true" : "false");
        new_state.changed = true;
        
        last_position = current_position;
        
        // Update LED hue
        motor_config.led_hue = current_position == 0 ? config_.off_led_hue : config_.on_led_hue;
        triggerMotorConfigUpdate();
        
        LOGI("ToggleComponent '%s': State changed to %s", component_id_, 
             current_position > 0 ? "ON" : "OFF");
    }
    
    last_updated_ms = millis();
    previous_sub_position_unit = sub_position_unit;
    first_run = true;
    
    return new_state;
}

void ToggleComponent::setState(const char *state_json)
{
    if (!state_json) return;
    
    // Simple JSON parsing for {"state": true/false}
    const char *state_field = strstr(state_json, "\"state\"");
    if (state_field) {
        const char *colon = strchr(state_field, ':');
        if (colon) {
            colon++;
            while (*colon == ' ' || *colon == '\t') colon++;
            
            bool new_state;
            if (strncmp(colon, "true", 4) == 0) {
                new_state = true;
            } else if (strncmp(colon, "false", 5) == 0) {
                new_state = false;
            } else {
                return;
            }
            
            // Update position to match state
            uint8_t new_position = new_state ? 1 : 0;
            if (new_position != current_position) {
                current_position = new_position;
                motor_config.position = current_position;
                triggerMotorConfigUpdate();
                
                LOGI("ToggleComponent '%s': State set via JSON to %s",
                     component_id_, new_state ? "ON" : "OFF");
            }
        }
    }
}

const char *ToggleComponent::getState()
{
    snprintf(state_buffer_, sizeof(state_buffer_),
             "{\"state\": %s, \"label\": \"%s\"}",
             current_position > 0 ? "true" : "false",
             current_position > 0 ? config_.on_label : config_.off_label);
    return state_buffer_;
}
