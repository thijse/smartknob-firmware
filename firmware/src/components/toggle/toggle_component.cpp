#include "toggle_component.h"
#include "../../util.h"
#include <logging.h>
#include <string.h>

ToggleComponent::ToggleComponent(
    SemaphoreHandle_t mutex,
    const PB_AppComponent &config) : Component(mutex, config) // ✅ Use unified constructor
{
    // Validate configuration first
    if (component_config_.type != PB_ComponentType_TOGGLE)
    {
        LOGE("ToggleComponent: Invalid component type %d", component_config_.type);
        return;
    }

    if (component_config_.which_component_config != PB_AppComponent_toggle_tag)
    {
        LOGE("ToggleComponent: Missing toggle configuration");
        return;
    }

    // Get typed config from base class (single source of truth)
    const auto &config_ = getConfig();
    configured_ = true;

    // Initialize position based on config
    current_position = config_.initial_state ? 1 : 0;
    last_position = current_position;

    // Configure motor with user settings (clamp strengths to [0.0, 1.0] for stability)
    float detent = config_.detent_strength_unit;
    if (detent < 0.0f)
        detent = 0.0f;
    if (detent > 1.0f)
        detent = 1.0f;
    if (detent != config_.detent_strength_unit)
    {
        LOGW("ToggleComponent: clamped detent_strength_unit from %.2f to %.2f", (double)config_.detent_strength_unit, (double)detent);
    }

    motor_config = PB_SmartKnobConfig{
        current_position,                                                // position
        0,                                                               // sub_position_unit
        current_position,                                                // position_nonce
        0,                                                               // min_position
        1,                                                               // max_position
        60 * PI / 180,                                                   // position_width_radians
        detent,                                                          // detent_strength_unit (clamped)
        1,                                                               // endstop_strength_unit
        config_.snap_point,                                              // snap_point
        "",                                                              // id
        0,                                                               // detent_positions_count
        {},                                                              // detent_positions
        config_.snap_point_bias,                                         // snap_point_bias (honor config)
        current_position == 0 ? config_.off_led_hue : config_.on_led_hue // led_hue
    };
    {
        size_t src_len = strnlen(component_id_, sizeof(component_id_));
        size_t copy_len = (src_len < sizeof(motor_config.id) - 1) ? src_len : (sizeof(motor_config.id) - 1);
        memcpy(motor_config.id, component_id_, copy_len);
        motor_config.id[copy_len] = '\0';
    }

    // Diagnostic: log applied haptics at creation
    LOGI("ToggleComponent '%s': created (snap_point=%.2f, bias=%.2f, detent=%.2f, hues off/on=%d/%d)",
         component_id_, (double)config_.snap_point, (double)config_.snap_point_bias, (double)detent, (int)config_.off_led_hue, (int)config_.on_led_hue);

    // Initialize state buffer
    memset(state_buffer_, 0, sizeof(state_buffer_));

    // Initialize screen
    initScreen();
}

void ToggleComponent::initScreen()
{
    if (screen == nullptr)
    {
        LOGE("ToggleComponent '%s': screen is NULL!", component_id_);
        return;
    }

    SemaphoreGuard lock(mutex_);

    // Create arc
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

    // Get config from base class
    const auto &config_ = getConfig();

    // Create status label with user configured labels
    status_label = lv_label_create(screen);
    lv_label_set_text(status_label, current_position == 0 ? config_.off_label : config_.on_label);
    lv_obj_set_style_text_color(status_label, LV_COLOR_MAKE(0xFF, 0xFF, 0xFF), 0);
    lv_obj_center(status_label);

    // Set initial background color based on state
    if (current_position == 0)
    {
        lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);
    }
    else
    {
        lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x80, 0x00), 0);
    }

    // Create component name label
    lv_obj_t *label = lv_label_create(screen);
    lv_label_set_text(label, getDisplayName()); // Use base class method
    lv_obj_align(label, LV_ALIGN_BOTTOM_MID, 0, -48);
}

EntityStateUpdate ToggleComponent::updateStateFromKnob(PB_SmartKnobState state)
{
    EntityStateUpdate new_state;

    current_position = state.current_position;
    sub_position_unit = state.sub_position_unit * motor_config.position_width_radians;

    // Update motor config for tracking
    motor_config.position_nonce = current_position;
    motor_config.position = current_position;

    // Calculate velocity
    static float previous_sub_position_unit = 0.0f;
    float vel = (sub_position_unit * 100 - previous_sub_position_unit * 100) / (millis() - last_updated_ms);

    // Update arc display
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
        // Guard LVGL updates with the shared LVGL mutex
        SemaphoreGuard lock(mutex_);
        if (current_position == 0)
        {
            lv_arc_set_value(arc_, 0);
        }
        else
        {
            lv_arc_set_value(arc_, 100);
        }
    }

    // Update display and LED on position change
    if (last_position != current_position && first_run)
    {
        SemaphoreGuard lock(mutex_);

        // Get config from base class
        const auto &config_ = getConfig();

        if (current_position == 0)
        {
            lv_label_set_text(status_label, config_.off_label);
            lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);
            lv_obj_set_style_arc_color(arc_, dark_arc_bg, LV_PART_MAIN);
        }
        else
        {
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

        // TODO: LED color switching not working - triggerMotorConfigUpdate() called but LEDs don't change color
        // Possible issues: motor task not processing led_hue changes, LED ring task needs different approach,
        // or timing issue with config updates. Need to investigate motor_task.cpp LED handling.
        // triggerMotorConfigUpdate();
    }

    last_updated_ms = millis();
    previous_sub_position_unit = sub_position_unit;
    first_run = true;

    return new_state;
}

void ToggleComponent::setState(const char *state_json)
{
    if (!state_json)
        return;

    // Simple JSON parsing for {"state": true/false}
    const char *state_field = strstr(state_json, "\"state\"");
    if (state_field)
    {
        const char *colon = strchr(state_field, ':');
        if (colon)
        {
            colon++;
            while (*colon == ' ' || *colon == '\t')
                colon++;

            bool new_state;
            if (strncmp(colon, "true", 4) == 0)
            {
                new_state = true;
            }
            else if (strncmp(colon, "false", 5) == 0)
            {
                new_state = false;
            }
            else
            {
                return;
            }

            // Update position to match state
            uint8_t new_position = new_state ? 1 : 0;
            if (new_position != current_position)
            {
                current_position = new_position;
                motor_config.position = current_position;
                triggerMotorConfigUpdate();
            }
        }
    }
}

const char *ToggleComponent::getState()
{
    // Get config from base class
    const auto &config_ = getConfig();

    snprintf(state_buffer_, sizeof(state_buffer_),
             "{\"state\": %s, \"label\": \"%s\"}",
             current_position > 0 ? "true" : "false",
             current_position > 0 ? config_.on_label : config_.off_label);
    return state_buffer_;
}

// === Reconfiguration support for ToggleComponent ===
#include <logging.h>

bool ToggleComponent::configure(const PB_AppComponent &config)
{
    // Validate type and union tag
    if (config.type != PB_ComponentType_TOGGLE)
    {
        LOGE("ToggleComponent::configure: type mismatch (%d)", config.type);
        return false;
    }
    if (config.which_component_config != PB_AppComponent_toggle_tag)
    {
        LOGE("ToggleComponent::configure: missing toggle config (which=%d)", config.which_component_config);
        return false;
    }

    // Preserve current position across reconfig
    uint8_t preserved_position = current_position > 0 ? 1 : 0;

    // Apply new configuration
    component_config_ = config;
    configured_ = true;

    const auto &cfg = getConfig();

    // Clamp/normalize preserved position
    current_position = preserved_position;
    last_position = current_position;

    // Recompute motor config (mirror constructor logic, but keep position)
    // Clamp strengths to [0.0, 1.0] for stability
    float detent = cfg.detent_strength_unit;
    if (detent < 0.0f)
        detent = 0.0f;
    if (detent > 1.0f)
        detent = 1.0f;
    if (detent != cfg.detent_strength_unit)
    {
        LOGW("ToggleComponent::configure: clamped detent_strength_unit from %.2f to %.2f", (double)cfg.detent_strength_unit, (double)detent);
    }

    motor_config = PB_SmartKnobConfig{
        current_position,                                        // position
        0,                                                       // sub_position_unit
        current_position,                                        // position_nonce
        0,                                                       // min_position
        1,                                                       // max_position
        60 * PI / 180,                                           // position_width_radians
        detent,                                                  // detent_strength_unit (clamped)
        1,                                                       // endstop_strength_unit
        cfg.snap_point,                                          // snap_point
        "",                                                      // id
        0,                                                       // detent_positions_count
        {},                                                      // detent_positions
        cfg.snap_point_bias,                                     // snap_point_bias
        current_position == 0 ? cfg.off_led_hue : cfg.on_led_hue // led_hue
    };
    {
        size_t src_len = strnlen(component_id_, sizeof(component_id_));
        size_t copy_len = (src_len < sizeof(motor_config.id) - 1) ? src_len : (sizeof(motor_config.id) - 1);
        memcpy(motor_config.id, component_id_, copy_len);
        motor_config.id[copy_len] = '\0';
    }

    // Update UI to reflect new labels/colors
    {
        SemaphoreGuard lock(mutex_);
        if (status_label != nullptr)
        {
            lv_label_set_text(status_label, current_position == 0 ? cfg.off_label : cfg.on_label);
        }
        if (screen != nullptr)
        {
            if (current_position == 0)
            {
                lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);
                if (arc_ != nullptr)
                {
                    lv_obj_set_style_arc_color(arc_, dark_arc_bg, LV_PART_MAIN);
                }
            }
            else
            {
                lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x80, 0x00), 0);
                if (arc_ != nullptr)
                {
                    lv_obj_set_style_arc_color(arc_, lv_color_mix(dark_arc_bg, LV_COLOR_MAKE(0x00, 0x80, 0x00), 128), LV_PART_MAIN);
                }
            }
        }
    }

    LOGI("ToggleComponent '%s': reconfigured (snap_point=%.2f, bias=%.2f, detent=%.2f, hues off/on=%d/%d)",
         component_id_, (double)cfg.snap_point, (double)cfg.snap_point_bias, (double)cfg.detent_strength_unit, (int)cfg.off_led_hue, (int)cfg.on_led_hue);

    // Note: ComponentManager will call triggerMotorConfigUpdate() and render() if this component is active.
    return true;
}
