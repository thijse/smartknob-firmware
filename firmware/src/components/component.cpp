#include "component.h"
#include "../util.h"
#include <logging.h>
#include <string.h>

Component::Component(
    const char* component_id,
    QueueHandle_t motor_task_queue,
    QueueHandle_t display_task_queue,
    QueueHandle_t led_ring_task_queue,
    SemaphoreHandle_t mutex
) : motor_task_queue_(motor_task_queue),
    display_task_queue_(display_task_queue),
    led_ring_task_queue_(led_ring_task_queue),
    mutex_(mutex),
    is_active_(false)
{
    // Copy component ID (ensure null termination)
    strlcpy(component_id_, component_id, sizeof(component_id_));
    
    // Initialize configuration to default state
    memset(&component_config_, 0, sizeof(component_config_));
    
    // Note: Don't use LOGI here - logging system may not be initialized during global construction
}

void Component::updateMotorConfig(const PB_SmartKnobConfig& config) {
    if (motor_task_queue_ == nullptr) {
        LOGW("Component '%s': Motor task queue not available", component_id_);
        return;
    }
    
    // Send motor configuration
    // Note: This assumes the motor task expects PB_SmartKnobConfig messages
    // We might need to wrap this in a different message type depending on the actual motor task interface
    if (xQueueSend(motor_task_queue_, &config, pdMS_TO_TICKS(10)) != pdTRUE) {
        LOGW("Component '%s': Failed to send motor config", component_id_);
    } else {
        LOGD("Component '%s': Motor config updated", component_id_);
    }
}

void Component::updateLEDs(int32_t hue, uint8_t saturation, uint8_t brightness) {
    if (led_ring_task_queue_ == nullptr) {
        LOGD("Component '%s': LED ring not available", component_id_);
        return;
    }
    
    // Create LED update message
    // Note: We'll need to check the actual LED ring message format
    // For now, creating a placeholder structure
    struct {
        uint8_t type;           // Message type
        int32_t hue;           // HSV hue
        uint8_t saturation;    // HSV saturation
        uint8_t brightness;    // HSV brightness
    } led_msg = {
        .type = 1,  // Solid color type (placeholder)
        .hue = hue,
        .saturation = saturation,
        .brightness = brightness
    };
    
    if (xQueueSend(led_ring_task_queue_, &led_msg, pdMS_TO_TICKS(10)) != pdTRUE) {
        LOGW("Component '%s': Failed to send LED update", component_id_);
    } else {
        LOGD("Component '%s': LED updated (hue=%d)", component_id_, (int)hue);
    }
}

void Component::updateDisplay(const char* text, uint8_t font_size) {
    if (display_task_queue_ == nullptr) {
        LOGD("Component '%s': Display not available", component_id_);
        return;
    }
    
    // Create display update message
    // Note: We'll need to check the actual display message format
    // For now, creating a placeholder structure
    struct {
        uint8_t type;           // Message type
        char text[64];         // Display text
        uint8_t font_size;     // Font size
    } display_msg = {
        .type = 1,  // Text display type (placeholder)
        .font_size = font_size
    };
    
    strlcpy(display_msg.text, text, sizeof(display_msg.text));
    
    if (xQueueSend(display_task_queue_, &display_msg, pdMS_TO_TICKS(10)) != pdTRUE) {
        LOGW("Component '%s': Failed to send display update", component_id_);
    } else {
        LOGD("Component '%s': Display updated ('%s')", component_id_, text);
    }
}
