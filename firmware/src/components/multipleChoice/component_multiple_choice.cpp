#include "component_multiple_choice.h"
#include "../../util.h"
#include <logging.h>
#include <string.h>
#include <lvgl.h>

MultipleChoice::MultipleChoice(
    SemaphoreHandle_t mutex,
    const PB_AppComponent &config) : Component(mutex, config) // ✅ Use unified constructor
{
    // Validate configuration first
    if (component_config_.type != PB_ComponentType_MULTI_CHOICE)
    {
        LOGE("MultipleChoice: Invalid component type %d", component_config_.type);
        return;
    }

    if (component_config_.which_component_config != PB_AppComponent_multi_choice_tag)
    {
        LOGE("MultipleChoice: Missing multi choice configuration");
        return;
    }

    // Get typed config from base class (single source of truth)
    const auto &config_ = getConfig();

    LOGI("MultipleChoice: About to validate %d options from protobuf", config_.options_count);

    // Validate options count (Nanopb static allocation should be safe)
    if (config_.options_count <= 0 || config_.options_count > 16)
    {
        LOGE("MultipleChoice: Invalid options count %d", config_.options_count);
        configured_ = false;
        return;
    }

    LOGI("MultipleChoice: Successfully validated %d options", config_.options_count);
    configured_ = true;

    // Initialize position based on config
    current_position = config_.initial_index;
    if (current_position < 0)
        current_position = 0;
    if (current_position >= config_.options_count)
        current_position = config_.options_count - 1;
    last_position = current_position;

    // Configure motor with user settings - enhanced for better feel
    // Clamp detent/endstop strengths to [0.0, 1.0] to avoid instability
    float detent = config_.detent_strength_unit;
    if (detent < 0.0f)
        detent = 0.0f;
    if (detent > 1.0f)
        detent = 1.0f;
    float endstop = config_.endstop_strength_unit;
    if (endstop < 0.0f)
        endstop = 0.0f;
    if (endstop > 1.0f)
        endstop = 1.0f;
    if (detent != config_.detent_strength_unit || endstop != config_.endstop_strength_unit)
    {
        LOGW("MultipleChoice: clamped strengths detent=%.2f endstop=%.2f", (double)detent, (double)endstop);
    }

    motor_config = PB_SmartKnobConfig{
        current_position,          // position
        0,                         // sub_position_unit
        (uint8_t)current_position, // position_nonce
        0,                         // min_position
        config_.options_count - 1, // max_position
        12.0 * PI / 180,           // position_width_radians
        detent,                    // detent_strength_unit (clamped)
        endstop,                   // endstop_strength_unit (clamped)
        0.5,                       // snap_point
        "",                        // id
        0,                         // detent_positions_count
        {},                        // detent_positions
        0,                         // snap_point_bias
        config_.led_hue            // led_hue
    };
    strncpy(motor_config.id, component_config_.component_id, sizeof(motor_config.id) - 1);

    LOGI("MultipleChoice: Created component '%s' with %d options, initial index %d",
         component_config_.component_id, config_.options_count, current_position);

    // Initialize screen (like ToggleComponent)
    initScreen();
}

void MultipleChoice::initScreen()
{
    if (screen == nullptr)
    {
        LOGE("MultipleChoice '%s': screen is NULL!", component_id_);
        return;
    }

    LOGI("MultipleChoice: Initializing screen for component '%s'", component_id_);

    // Get config from base class
    const auto &config_ = getConfig();

    {
        SemaphoreGuard lock(mutex_); // ✅ CRITICAL: Protect all LVGL operations

        // Create persistent UI objects (like ToggleComponent)
        if (config_.options_count == 0)
        {
            // Show error message if no options
            lv_obj_t *error_label = lv_label_create(screen);
            lv_label_set_text(error_label, "No options");
            lv_obj_center(error_label);
            lv_obj_set_style_text_color(error_label, lv_color_make(255, 0, 0), 0);
            LOGW("MultipleChoice: No options available");
            return;
        }

        // Create title label (component name)
        title_label_ = lv_label_create(screen);
        lv_label_set_text(title_label_, getDisplayName()); // Use base class method
        lv_obj_align(title_label_, LV_ALIGN_TOP_MID, 0, 16);
        lv_obj_set_style_text_color(title_label_, lv_color_make(180, 180, 180), 0);
        lv_obj_set_style_text_font(title_label_, &roboto_semi_bold_mono_16pt, 0);

        // Create main option label (current selection)
        option_label_ = lv_label_create(screen);
        lv_obj_center(option_label_);
        lv_obj_set_style_text_align(option_label_, LV_TEXT_ALIGN_CENTER, 0);
        lv_obj_set_style_text_color(option_label_, lv_color_white(), 0);

        // Use large font for 2x bigger text (48pt vs typical 24pt)
        lv_obj_set_style_text_font(option_label_, &roboto_regular_mono_48pt, 0);

        // Create position indicator label (only if multiple options)
        if (config_.options_count > 1)
        {
            position_label_ = lv_label_create(screen);
            lv_obj_align(position_label_, LV_ALIGN_BOTTOM_MID, 0, -10);
            lv_obj_set_style_text_color(position_label_, lv_color_make(120, 120, 120), 0);
            lv_obj_set_style_text_font(position_label_, &roboto_semi_bold_mono_16pt, 0);
        }
    } // ✅ Mutex automatically released here

    // Initial display update
    updateDisplay();

    // Trigger initial motor configuration
    triggerMotorConfigUpdate();

    LOGI("MultipleChoice: Screen initialization complete");
}

EntityStateUpdate MultipleChoice::updateStateFromKnob(PB_SmartKnobState state)
{
    EntityStateUpdate new_state;

    if (!configured_)
    {
        return new_state;
    }

    // Get config from base class
    const auto &config_ = getConfig();

    // Update position based on motor position
    int new_position = (int)round(state.current_position);

    // Clamp position to valid range
    if (new_position < 0)
        new_position = 0;
    if (new_position >= config_.options_count)
        new_position = config_.options_count - 1;

    if (new_position != current_position)
    {
        current_position = new_position;

        // Update motor config
        motor_config.position = current_position;
        motor_config.position_nonce = current_position;

        // Create state update with safe text handling
        const char *safe_text = get_selected_text();
        char truncated_text[32]; // Safe size for JSON

        if (safe_text && strlen(safe_text) > 30)
        {
            strncpy(truncated_text, safe_text, 27);
            strcpy(truncated_text + 27, "...");
            safe_text = truncated_text;
        }

        sprintf(new_state.app_id, "%s", component_id_);
        sprintf(new_state.entity_id, "%s", component_id_);
        sprintf(new_state.state, "{\"selected_index\": %d, \"selected_text\": \"%.30s\"}",
                current_position, safe_text ? safe_text : "");
        new_state.changed = true;

        publishStateUpdate();

        LOGI("MultipleChoice: Selection changed to index %d: '%s'",
             current_position, get_selected_text());

        // Update persistent objects (like ToggleComponent)
        updateDisplay();

        // Update motor config for LED color
        // triggerMotorConfigUpdate();
    }

    return new_state;
}

void MultipleChoice::setState(const char *state_json)
{
    if (!configured_)
    {
        LOGE("MultipleChoice: Component not configured, cannot set state");
        return;
    }

    // Parse JSON to extract selected index
    // For now, simple implementation - expects format: {"selected_index": N}
    // TODO: Add proper JSON parsing

    LOGI("MultipleChoice: setState called with: %s", state_json);
}

const char *MultipleChoice::getState()
{
    if (!configured_)
    {
        return "{}";
    }

    const auto &config_ = getConfig(); // Get config from base class

    static char state_buffer[256];
    snprintf(state_buffer, sizeof(state_buffer),
             "{\"selected_index\": %d, \"selected_text\": \"%s\", \"options_count\": %d}",
             current_position, get_selected_text(), config_.options_count);

    return state_buffer;
}

const char *MultipleChoice::get_selected_text() const
{
    const auto &config_ = getConfig(); // Get config from base class

    if (!configured_ || current_position < 0 || current_position >= config_.options_count)
    {
        LOGW("MultipleChoice: get_selected_text bounds check failed - configured: %d, position: %d, count: %d",
             configured_, current_position, config_.options_count);
        return "BOUNDS_ERROR";
    }

    // Use Nanopb static allocation strings directly
    return config_.options[current_position];
}

void MultipleChoice::updateMotorConfigFromState()
{
    if (!configured_)
        return;

    motor_config.position = current_position;
    motor_config.position_nonce = current_position;
}

void MultipleChoice::publishStateUpdate()
{
    // TODO: Implement state update publishing to external clients
    // This would notify Python clients about selection changes
}

void MultipleChoice::updateDisplay()
{
    if (!configured_)
        return;

    // Get config from base class
    const auto &config_ = getConfig();

    {
        SemaphoreGuard lock(mutex_); // ✅ CRITICAL: Protect all LVGL operations

        // Update option text (like ToggleComponent updates its labels)
        if (option_label_ != nullptr)
        {
            const char *current_text = get_selected_text();
            if (current_text && strlen(current_text) > 0)
            {
                // Protect against overly long text that could cause display issues
                static char safe_text[64]; // Safe buffer size for display
                strncpy(safe_text, current_text, sizeof(safe_text) - 1);
                safe_text[sizeof(safe_text) - 1] = '\0'; // Ensure null termination

                // Truncate with ellipsis if too long
                if (strlen(current_text) >= sizeof(safe_text) - 3)
                {
                    strcpy(safe_text + sizeof(safe_text) - 4, "...");
                    LOGW("MultipleChoice: Text truncated - original length %d", (int)strlen(current_text));
                }

                lv_label_set_text(option_label_, safe_text);
            }
            else
            {
                lv_label_set_text(option_label_, "ERROR");
            }
        }

        // Update position indicator (like "1/5")
        if (position_label_ != nullptr && config_.options_count > 1)
        {
            char position_text[16];
            snprintf(position_text, sizeof(position_text), "%d/%d",
                     current_position + 1, config_.options_count);
            lv_label_set_text(position_label_, position_text);
        }
    } // ✅ Mutex automatically released here

    LOGI("MultipleChoice: Updated display - option %d/%d: '%s'",
         current_position + 1, config_.options_count, get_selected_text());
}

// === Reconfiguration support for MultipleChoice ===
#include <logging.h>

bool MultipleChoice::configure(const PB_AppComponent &config)
{
    // Validate type and union tag
    if (config.type != PB_ComponentType_MULTI_CHOICE)
    {
        LOGE("MultipleChoice::configure: type mismatch (%d)", config.type);
        return false;
    }
    if (config.which_component_config != PB_AppComponent_multi_choice_tag)
    {
        LOGE("MultipleChoice::configure: missing multi_choice config (which=%d)", config.which_component_config);
        return false;
    }

    // Preserve current selection index across reconfig
    int preserved_position = current_position;

    // Apply new configuration
    component_config_ = config;

    const auto &cfg = getConfig();

    // Validate options and set configured_ flag
    if (cfg.options_count <= 0 || cfg.options_count > 16)
    {
        LOGE("MultipleChoice::configure: invalid options_count=%d", cfg.options_count);
        configured_ = false;
        return false;
    }
    configured_ = true;

    // Clamp preserved position to new bounds
    if (preserved_position < 0)
        preserved_position = 0;
    if (preserved_position >= cfg.options_count)
        preserved_position = cfg.options_count - 1;

    current_position = preserved_position;
    last_position = current_position;

    // Recompute motor config (mirror constructor logic, but keep position)
    // Clamp detent/endstop strengths to [0.0, 1.0] to avoid instability
    float detent = cfg.detent_strength_unit;
    if (detent < 0.0f)
        detent = 0.0f;
    if (detent > 1.0f)
        detent = 1.0f;
    float endstop = cfg.endstop_strength_unit;
    if (endstop < 0.0f)
        endstop = 0.0f;
    if (endstop > 1.0f)
        endstop = 1.0f;
    if (detent != cfg.detent_strength_unit || endstop != cfg.endstop_strength_unit)
    {
        LOGW("MultipleChoice::configure: clamped strengths detent=%.2f endstop=%.2f", (double)detent, (double)endstop);
    }

    motor_config = PB_SmartKnobConfig{
        (int32_t)current_position, // position
        0,                         // sub_position_unit
        (uint8_t)current_position, // position_nonce
        0,                         // min_position
        cfg.options_count - 1,     // max_position
        12.0 * PI / 180,           // position_width_radians
        detent,                    // detent_strength_unit (clamped)
        endstop,                   // endstop_strength_unit (clamped)
        0.5f,                      // snap_point
        "",                        // id
        0,                         // detent_positions_count
        {},                        // detent_positions
        0,                         // snap_point_bias
        cfg.led_hue                // led_hue
    };
    strncpy(motor_config.id, component_config_.component_id, sizeof(motor_config.id) - 1);

    // Update display text and index indicator to reflect new configuration
    updateDisplay();

    LOGI("MultipleChoice '%s': reconfigured (%d options, detent=%.2f, endstop=%.2f, hue=%d, pos=%d)",
         component_id_, cfg.options_count, (double)cfg.detent_strength_unit, (double)cfg.endstop_strength_unit, (int)cfg.led_hue, current_position);

    // Note: ComponentManager will call triggerMotorConfigUpdate() and render() if this component is active.
    return true;
}
