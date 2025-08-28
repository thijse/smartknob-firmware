#pragma once

#include "component.h"
#include <map>
#include <memory>
#include <string>

/**
 * Manages the lifecycle and active state of components.
 * 
 * The ComponentManager is responsible for:
 * - Creating components from configuration messages
 * - Managing component lifecycle (activation/deactivation)
 * - Routing input to the active component
 * - Cleanup and memory management
 */
class ComponentManager {
public:
    /**
     * Create a new ComponentManager.
     * 
     * @param motor_task_queue Queue for motor commands
     * @param display_task_queue Queue for display updates (optional)
     * @param led_ring_task_queue Queue for LED updates (optional)
     * @param mutex Mutex for thread safety (optional)
     */
    ComponentManager(
        QueueHandle_t motor_task_queue,
        QueueHandle_t display_task_queue = nullptr,
        QueueHandle_t led_ring_task_queue = nullptr,
        SemaphoreHandle_t mutex = nullptr
    );
    
    ~ComponentManager();

    // ========== Component Lifecycle ==========
    
    /**
     * Create a component from configuration.
     * 
     * If a component with the same ID already exists, it will be
     * reconfigured with the new settings.
     * 
     * @param config Component configuration message
     * @return true if component was created/updated successfully
     */
    bool createComponent(const PB_AppComponent& config);
    
    /**
     * Remove a component by ID.
     * 
     * @param component_id ID of component to remove
     * @return true if component was found and removed
     */
    bool destroyComponent(const char* component_id);
    
    /**
     * Get a component by ID.
     * 
     * @param component_id ID of component to find
     * @return Pointer to component, or nullptr if not found
     */
    Component* getComponent(const char* component_id);

    // ========== Active Component Management ==========
    
    /**
     * Set the active component (receives input).
     * 
     * @param component_id ID of component to activate
     * @return true if component was found and activated
     */
    bool setActiveComponent(const char* component_id);
    
    /**
     * Get the currently active component.
     * 
     * @return Pointer to active component, or nullptr if none active
     */
    Component* getActiveComponent();
    
    /**
     * Deactivate the current component (no component receives input).
     */
    void deactivateAll();

    // ========== Input Delegation ==========
    
    /**
     * Forward knob input to the active component.
     * 
     * @param state Current knob state
     */
    void handleKnobInput(const PB_SmartKnobState& state);
    
    /**
     * Forward button input to the active component.
     * 
     * @param pressed true for press, false for release
     */
    void handleButtonInput(bool pressed);

    // ========== Rendering ==========
    
    /**
     * Render the active component.
     */
    void renderActiveComponent();

    // ========== Debug/Status ==========
    
    /**
     * Get the number of registered components.
     */
    size_t getComponentCount() const;
    
    /**
     * Get list of component IDs (for debugging).
     */
    void getComponentIds(char* buffer, size_t buffer_size) const;

private:
    // ========== Component Factory ==========
    
    /**
     * Create a component instance based on type.
     * 
     * @param type Component type from protobuf enum
     * @param component_id Unique ID for the component
     * @return New component instance, or nullptr on failure
     */
    std::unique_ptr<Component> createComponentByType(
        PB_ComponentType type,
        const char* component_id
    );

    // ========== State ==========
    
    std::map<std::string, std::unique_ptr<Component>> components_;  // All registered components
    Component* active_component_;                                   // Currently active component
    
    // ========== System Access ==========
    
    QueueHandle_t motor_task_queue_;          // Motor control queue
    QueueHandle_t display_task_queue_;        // Display update queue
    QueueHandle_t led_ring_task_queue_;       // LED update queue
    SemaphoreHandle_t mutex_;                 // Thread safety mutex
};
