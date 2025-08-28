#include "toggle_component.h"
#include "../../util.h"
#include <logging.h>
#include <string.h>
#include <math.h>

// Debouncing and timing constants
#define DEBOUNCE_TIME_MS 50
#define SNAP_THRESHOLD 0.1f

ToggleComponent::ToggleComponent(
    const char* component_id,
    QueueHandle_t motor_task_queue,
    QueueHandle_t display_task_queue,
    QueueHandle_t led_ring_task_queue,
    SemaphoreHandle_t mutex
) : Component(component_id, motor_task_queue, display_task_queue, led_ring_task_queue, mutex),
    current_state_(false),
    last_knob_state_(false),
    last_knob_position_(0.0f),
    last_state_change_time_(0)
{
    // Initialize configuration to default values
    memset(&config_, 0, sizeof(config_));
    
    // Set sensible defaults
    strcpy(config_.off_label, "Off");
    strcpy(config_.on_label, "On");
    config_.snap_point = 0.5f;           // 50% rotation to toggle
    config_.snap_point_bias = 0.0f;      // Symmetric by default
    config_.detent_strength_unit = 0.5f; // Medium haptic feedback
    config_.off_led_hue = 0;             // Red when off
    config_.on_led_hue = 120;            // Green when on
    config_.initial_state = false;       // Start in off state
    
    current_state_ = config_.initial_state;
    
    // Initialize state buffer
    memset(state_buffer_, 0, sizeof(state_buffer_));
    
    // Note: Don't use LOGI here - logging system may not be initialized during construction
}

bool ToggleComponent::configure(const PB_AppComponent& config) {
    // Validate configuration
    if (config.type != PB_ComponentType_TOGGLE) {
        LOGE("ToggleComponent '%s': Invalid component type %d", component_id_, config.type);
        return false;
    }
    
    if (config.which_component_config != PB_AppComponent_toggle_tag) {
        LOGE("ToggleComponent '%s': Missing toggle configuration", component_id_);
        return false;
    }
    
    LOGI("ToggleComponent '%s': Configuring toggle", component_id_);
    
    // Store the complete component configuration
    component_config_ = config;
    config_ = config.component_config.toggle;
    
    // Validate and clamp configuration values
    config_.snap_point = fmaxf(0.1f, fminf(1.0f, config_.snap_point));
    config_.snap_point_bias = fmaxf(-1.0f, fminf(1.0f, config_.snap_point_bias));
    config_.detent_strength_unit = fmaxf(0.0f, fminf(1.0f, config_.detent_strength_unit));
    
    // Clamp LED hue values to valid range
    config_.off_led_hue = config_.off_led_hue % 360;
    config_.on_led_hue = config_.on_led_hue % 360;
    if (config_.off_led_hue < 0) config_.off_led_hue += 360;
    if (config_.on_led_hue < 0) config_.on_led_hue += 360;
    
    // Set initial state
    current_state_ = config_.initial_state;
    last_knob_state_ = current_state_;
    
    // Apply initial configuration
    updateMotorConfig();
    updateLEDs();
    updateDisplay();
    
    LOGI("ToggleComponent '%s': Configured successfully (snap_point=%.2f, bias=%.2f)", 
         component_id_, config_.snap_point, config_.snap_point_bias);
    
    return true;
}

void ToggleComponent::handleKnobInput(const PB_SmartKnobState& state) {
    // Get current time for debouncing
    uint32_t current_time = millis();
    
    // Skip if we're in debounce period
    if (current_time - last_state_change_time_ < DEBOUNCE_TIME_MS) {
        return;
    }
    
    // Store the current position
    float knob_position = state.current_position;
    
    // Check if we should toggle state based on knob position
    bool should_toggle = shouldToggleState(knob_position);
    
    if (should_toggle && current_time - last_state_change_time_ >= DEBOUNCE_TIME_MS) {
        // Toggle the state
        changeState(!current_state_);
        last_state_change_time_ = current_time;
    }
    
    last_knob_position_ = knob_position;
}

void ToggleComponent::handleButtonInput(bool pressed) {
    if (pressed) {
        // On button press, toggle the state
        uint32_t current_time = millis();
        if (current_time - last_state_change_time_ >= DEBOUNCE_TIME_MS) {
            changeState(!current_state_);
            last_state_change_time_ = current_time;
            LOGI("ToggleComponent '%s': Button toggle to %s", 
                 component_id_, current_state_ ? "ON" : "OFF");
        }
    }
}

void ToggleComponent::render() {
    updateDisplay();
    updateLEDs();
}

void ToggleComponent::setState(const char* state_json) {
    if (!state_json) return;
    
    // Simple JSON parsing for {"state": true/false}
    // Look for "state" field and parse boolean value
    const char* state_field = strstr(state_json, "\"state\"");
    if (state_field) {
        const char* colon = strchr(state_field, ':');
        if (colon) {
            // Skip whitespace after colon
            colon++;
            while (*colon == ' ' || *colon == '\t') colon++;
            
            bool new_state;
            if (strncmp(colon, "true", 4) == 0) {
                new_state = true;
            } else if (strncmp(colon, "false", 5) == 0) {
                new_state = false;
            } else {
                LOGW("ToggleComponent '%s': Invalid state value in JSON", component_id_);
                return;
            }
            
            if (new_state != current_state_) {
                changeState(new_state);
                LOGI("ToggleComponent '%s': State set via JSON to %s", 
                     component_id_, new_state ? "ON" : "OFF");
            }
        }
    }
}

const char* ToggleComponent::getState() {
    // Create JSON representation of current state
    snprintf(state_buffer_, sizeof(state_buffer_), 
             "{\"state\": %s, \"label\": \"%s\"}", 
             current_state_ ? "true" : "false",
             getCurrentLabel());
    return state_buffer_;
}

void ToggleComponent::updateMotorConfig() {
    if (motor_task_queue_ == nullptr) {
        LOGD("ToggleComponent '%s': Motor task queue not available", component_id_);
        return;
    }
    
    // Create motor configuration for toggle behavior
    PB_SmartKnobConfig motor_config = {};
    
    // Set up as a 2-position toggle
    motor_config.position_nonce = 1;
    motor_config.position_width_radians = 1.0f;  // 1 radian per position
    motor_config.position = current_state_ ? 1 : 0;  // 0 = off, 1 = on
    motor_config.min_position = 0;
    motor_config.max_position = 1;
    motor_config.snap_point = config_.snap_point;
    motor_config.snap_point_bias = config_.snap_point_bias;
    
    // Haptic feedback settings
    motor_config.detent_strength_unit = config_.detent_strength_unit;
    motor_config.endstop_strength_unit = 1.0f;  // Strong endstops
    
    // Apply the motor configuration using base class helper
    Component::updateMotorConfig(motor_config);
    
    LOGD("ToggleComponent '%s': Motor config updated (position=%d)", 
         component_id_, current_state_ ? 1 : 0);
}

void ToggleComponent::updateLEDs() {
    int32_t hue = current_state_ ? config_.on_led_hue : config_.off_led_hue;
    uint8_t saturation = 100;  // Full saturation
    uint8_t brightness = 80;   // 80% brightness
    
    // Use base class helper method
    Component::updateLEDs(hue, saturation, brightness);
    
    LOGD("ToggleComponent '%s': LEDs updated (hue=%d)", component_id_, (int)hue);
}

void ToggleComponent::updateDisplay() {
    if (display_task_queue_ == nullptr) {
        LOGD("ToggleComponent '%s': Display not available", component_id_);
        return;
    }
    
    // Create display text with component name and current state
    char display_text[64];
    snprintf(display_text, sizeof(display_text), "%s\n%s", 
             component_config_.display_name, getCurrentLabel());
    
    // Use base class helper method
    Component::updateDisplay(display_text, 2);  // Font size 2
    
    LOGD("ToggleComponent '%s': Display updated ('%s')", component_id_, display_text);
}

bool ToggleComponent::shouldToggleState(float knob_position) {
    // Get adjusted position accounting for bias
    float adjusted_position = getAdjustedPosition(knob_position);
    
    // Determine if we've crossed the snap point
    bool knob_indicates_on = (adjusted_position > config_.snap_point);
    
    // Check if this represents a state change
    bool should_change = (knob_indicates_on != current_state_);
    
    // Add some hysteresis to prevent rapid toggling
    if (should_change) {
        float position_change = fabsf(adjusted_position - last_knob_position_);
        if (position_change < SNAP_THRESHOLD) {
            should_change = false;
        }
    }
    
    return should_change;
}

void ToggleComponent::changeState(bool new_state) {
    if (new_state == current_state_) {
        return;  // No change needed
    }
    
    current_state_ = new_state;
    
    // Update all feedback systems
    updateMotorConfig();
    updateLEDs();
    updateDisplay();
    
    LOGI("ToggleComponent '%s': State changed to %s (%s)", 
         component_id_, 
         current_state_ ? "ON" : "OFF",
         getCurrentLabel());
    
    // TODO: Broadcast state change to external systems (MQTT, etc.)
}

const char* ToggleComponent::getCurrentLabel() const {
    return current_state_ ? config_.on_label : config_.off_label;
}

float ToggleComponent::getAdjustedPosition(float knob_position) const {
    // Apply bias to make one direction easier than the other
    // bias = -1.0: easier to turn on (toward +1)
    // bias = +1.0: easier to turn off (toward -1)  
    // bias = 0.0: symmetric behavior
    
    float adjusted = knob_position;
    
    if (config_.snap_point_bias != 0.0f) {
        // Apply asymmetric scaling
        if (config_.snap_point_bias > 0.0f) {
            // Make turning off (toward -1) easier
            if (adjusted < 0) {
                adjusted *= (1.0f + config_.snap_point_bias);
            } else {
                adjusted *= (1.0f - config_.snap_point_bias * 0.5f);
            }
        } else {
            // Make turning on (toward +1) easier
            if (adjusted > 0) {
                adjusted *= (1.0f - config_.snap_point_bias);
            } else {
                adjusted *= (1.0f + config_.snap_point_bias * 0.5f);
            }
        }
    }
    
    // Normalize to 0-1 range for snap point comparison
    return (adjusted + 1.0f) / 2.0f;
}
