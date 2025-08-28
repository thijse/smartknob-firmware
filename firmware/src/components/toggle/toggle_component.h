#pragma once

#include "../component.h"

/**
 * Toggle Component - Remote-configurable two-position switch.
 * 
 * Implements a toggle switch that can be configured with:
 * - Custom labels for on/off states
 * - Asymmetric haptic feedback (snap_point_bias)
 * - Custom LED colors for each state
 * - Configurable haptic strength
 * 
 * The toggle switch is designed for intuitive use cases like:
 * - Door locks (biased toward "locked" for safety)
 * - Light switches (equal resistance both ways)
 * - Security systems (biased toward "armed")
 */
class ToggleComponent : public Component {
public:
    /**
     * Create a new ToggleComponent.
     * 
     * @param component_id Unique identifier for this toggle
     * @param motor_task_queue Queue for motor commands
     * @param display_task_queue Queue for display updates (optional)
     * @param led_ring_task_queue Queue for LED updates (optional)
     * @param mutex Mutex for thread safety (optional)
     */
    ToggleComponent(
        const char* component_id,
        QueueHandle_t motor_task_queue,
        QueueHandle_t display_task_queue = nullptr,
        QueueHandle_t led_ring_task_queue = nullptr,
        SemaphoreHandle_t mutex = nullptr
    );

    // ========== Component Interface ==========
    
    /**
     * Configure this toggle with the provided settings.
     * 
     * @param config Complete component configuration including ToggleConfig
     * @return true if configuration was applied successfully
     */
    bool configure(const PB_AppComponent& config) override;
    
    /**
     * Handle knob rotation and position input.
     * 
     * Implements toggle logic:
     * - Detects when knob crosses the snap point
     * - Applies haptic feedback
     * - Updates internal state
     * - Triggers visual updates
     * 
     * @param state Current knob state (position, velocity, etc.)
     */
    void handleKnobInput(const PB_SmartKnobState& state) override;
    
    /**
     * Handle button press/release events.
     * 
     * For toggles, button press can be used to:
     * - Reset to default position
     * - Toggle between states
     * - Trigger additional actions
     * 
     * @param pressed true for button press, false for release
     */
    void handleButtonInput(bool pressed) override;
    
    /**
     * Update the visual appearance (display and LEDs).
     * 
     * Updates:
     * - Display text with current state label
     * - LED ring color based on current state
     * - Any additional visual feedback
     */
    void render() override;
    
    /**
     * Set toggle state from external source (e.g., MQTT, REST API).
     * 
     * Expected JSON format:
     * {"state": true}  or  {"state": false}
     * 
     * @param state_json JSON string representing the new state
     */
    void setState(const char* state_json) override;
    
    /**
     * Get current toggle state as JSON string.
     * 
     * Returns JSON format:
     * {"state": true, "label": "On"}
     * 
     * @return JSON representation of current state
     */
    const char* getState() override;
    
    /**
     * Get the type name of this component.
     */
    const char* getComponentType() const override { return "toggle"; }

private:
    // ========== State Management ==========
    
    PB_ToggleConfig config_;           // Toggle-specific configuration
    bool current_state_;               // Current toggle state (false=off, true=on)
    bool last_knob_state_;             // Last knob position state (for edge detection)
    float last_knob_position_;         // Last knob position (for change detection)
    uint32_t last_state_change_time_;  // Time of last state change (for debouncing)
    
    // State buffer for getState() return value
    char state_buffer_[128];
    
    // ========== Helper Methods ==========
    
    /**
     * Apply motor configuration based on current state and toggle config.
     * 
     * Sets up:
     * - Snap point position and bias
     * - Detent strength
     * - Position limits
     * - Haptic feedback characteristics
     */
    void updateMotorConfig();
    
    /**
     * Update LED ring based on current state.
     * 
     * Uses the configured on/off hue values from ToggleConfig.
     */
    void updateLEDs();
    
    /**
     * Update display with current state information.
     * 
     * Shows:
     * - Component display name
     * - Current state label (on_label/off_label)
     * - Any additional status information
     */
    void updateDisplay();
    
    /**
     * Check if knob position indicates a state change.
     * 
     * Uses the snap_point and snap_point_bias to determine
     * if the knob has moved far enough to trigger a toggle.
     * 
     * @param knob_position Current knob position (-1.0 to +1.0)
     * @return true if state should change, false otherwise
     */
    bool shouldToggleState(float knob_position);
    
    /**
     * Actually change the toggle state.
     * 
     * Updates internal state and triggers all necessary updates:
     * - Motor configuration
     * - Visual feedback
     * - External state broadcasting
     * 
     * @param new_state The new toggle state
     */
    void changeState(bool new_state);
    
    /**
     * Get the label for the current state.
     * 
     * @return Pointer to the appropriate label string
     */
    const char* getCurrentLabel() const;
    
    /**
     * Convert knob position to toggle position.
     * 
     * Takes into account the snap_point_bias to create
     * asymmetric behavior where one direction is easier.
     * 
     * @param knob_position Raw knob position
     * @return Adjusted position for toggle logic
     */
    float getAdjustedPosition(float knob_position) const;
};
