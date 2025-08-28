#pragma once

#include <Arduino.h>
#include <FreeRTOS.h>
#include <semphr.h>
#include "../task.h"
#include "../proto/proto_gen/smartknob.pb.h"
#include "../motor_foc/motor_task.h"
#include "../display_task.h"
#include "../led_ring/led_ring_task.h"

/**
 * Base class for remote-configurable SmartKnob components.
 * 
 * Components are interactive elements that can be configured remotely
 * via protobuf messages. Unlike traditional apps, components are:
 * - Dynamically created at runtime
 * - Fully configurable via protocol messages
 * - Designed for remote control scenarios
 * 
 * This base class provides common functionality and defines the interface
 * that all component types must implement.
 */
class Component {
public:
    /**
     * Create a new component with the given ID.
     * 
     * @param component_id Unique identifier for this component instance
     * @param motor_task_queue Queue for sending motor commands
     * @param display_task_queue Queue for sending display updates (optional)
     * @param led_ring_task_queue Queue for sending LED updates (optional)
     * @param mutex Mutex for thread-safe operations
     */
    Component(
        const char* component_id,
        QueueHandle_t motor_task_queue,
        QueueHandle_t display_task_queue = nullptr,
        QueueHandle_t led_ring_task_queue = nullptr,
        SemaphoreHandle_t mutex = nullptr
    );
    
    virtual ~Component() = default;

    // ========== Component Lifecycle ==========
    
    /**
     * Configure this component with the provided settings.
     * 
     * Called when the component is first created or when configuration
     * is updated remotely. Implementation should validate the config
     * and apply it to the component's behavior.
     * 
     * @param config Complete component configuration
     * @return true if configuration was applied successfully
     */
    virtual bool configure(const PB_AppComponent& config) = 0;
    
    /**
     * Activate this component (becomes the active input handler).
     * Called when this component should start responding to user input.
     */
    virtual void activate() {}
    
    /**
     * Deactivate this component (no longer handles input).
     * Called when another component becomes active or system switches to apps.
     */
    virtual void deactivate() {}

    // ========== Input Handling ==========
    
    /**
     * Handle knob rotation and position input.
     * 
     * @param state Current knob state (position, velocity, etc.)
     */
    virtual void handleKnobInput(const PB_SmartKnobState& state) = 0;
    
    /**
     * Handle button press/release events.
     * 
     * @param pressed true for button press, false for release
     */
    virtual void handleButtonInput(bool pressed) {}

    // ========== Rendering ==========
    
    /**
     * Update the visual appearance (display and LEDs).
     * Called periodically and when component state changes.
     */
    virtual void render() = 0;

    // ========== State Management ==========
    
    /**
     * Set component state from external source (e.g., MQTT, REST API).
     * 
     * @param state_json JSON string representing the new state
     */
    virtual void setState(const char* state_json) {}
    
    /**
     * Get current component state as JSON string.
     * 
     * @return JSON representation of current state
     */
    virtual const char* getState() { return "{}"; }

    // ========== Component Identity ==========
    
    /**
     * Get the unique ID of this component.
     */
    const char* getComponentId() const { return component_id_; }
    
    /**
     * Get the type name of this component (for debugging/logging).
     */
    virtual const char* getComponentType() const = 0;

protected:
    // ========== Helper Methods ==========
    
    /**
     * Update motor configuration for haptic feedback.
     * 
     * @param config Motor configuration to apply
     */
    void updateMotorConfig(const PB_SmartKnobConfig& config);
    
    /**
     * Update LED ring with solid color.
     * 
     * @param hue HSV hue value (0-360)
     * @param saturation HSV saturation (0-100)
     * @param brightness HSV brightness (0-100)
     */
    void updateLEDs(int32_t hue, uint8_t saturation = 100, uint8_t brightness = 80);
    
    /**
     * Update display with text.
     * 
     * @param text Text to display
     * @param font_size Font size (optional)
     */
    void updateDisplay(const char* text, uint8_t font_size = 2);

    // ========== Component State ==========
    
    char component_id_[33];                    // Unique component identifier
    PB_AppComponent component_config_;         // Current configuration
    bool is_active_;                          // Whether this component is currently active
    
    // ========== System Access ==========
    
    QueueHandle_t motor_task_queue_;          // Motor control queue
    QueueHandle_t display_task_queue_;        // Display update queue (optional)
    QueueHandle_t led_ring_task_queue_;       // LED update queue (optional)
    SemaphoreHandle_t mutex_;                 // Thread safety mutex (optional)
};
