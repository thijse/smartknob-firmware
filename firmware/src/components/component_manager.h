#pragma once

#include "component.h"
#include "../notify/motor_notifier/motor_notifier.h"
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
class ComponentManager
{
public:
    /**
     * Create a new ComponentManager.
     *
     * @param mutex Mutex for thread safety
     */
    ComponentManager(SemaphoreHandle_t mutex);

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
    bool createComponent(const PB_AppComponent &config);

    /**
     * Remove a component by ID.
     *
     * @param component_id ID of component to remove
     * @return true if component was found and removed
     */
    bool destroyComponent(const char *component_id);

    /**
     * Get a component by ID.
     *
     * @param component_id ID of component to find
     * @return Pointer to component, or nullptr if not found
     */
    Component *getComponent(const char *component_id);

    // ========== Active Component Management ==========

    /**
     * Set the active component (receives input).
     *
     * @param component_id ID of component to activate
     * @return true if component was found and activated
     */
    bool setActiveComponent(const char *component_id);

    /**
     * Get the currently active component.
     *
     * @return Pointer to active component, or nullptr if none active
     */
    Component *getActiveComponent();

    /**
     * Deactivate the current component (no component receives input).
     */
    void deactivateAll();

    // ========== Main Loop Integration (Apps-like interface) ==========

    /**
     * Update active component and get state updates.
     *
     * This follows the same pattern as Apps::update() for main loop integration.
     * The active component handles the state and returns any external updates.
     *
     * @param state Current app state with knob/button information
     * @return Entity state update for external communication
     */
    EntityStateUpdate update(AppState state);

    /**
     * Set the motor notifier for hardware control.
     *
     * This will be passed to all components as they are created,
     * following the same pattern as Apps.
     *
     * @param motor_notifier Motor notifier instance
     */
    void setMotorNotifier(MotorNotifier *motor_notifier);

    // ========== Debug/Status ==========

    /**
     * Get the number of registered components.
     */
    size_t getComponentCount() const;

    /**
     * Get list of component IDs (for debugging).
     */
    void getComponentIds(char *buffer, size_t buffer_size) const;

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
        const char *component_id);

    // ========== State ==========

    std::map<std::string, std::unique_ptr<Component>> components_; // All registered components
    Component *active_component_;                                  // Currently active component

    // ========== System Access ==========

    SemaphoreHandle_t mutex_;       // Thread safety mutex
    MotorNotifier *motor_notifier_; // Motor notifier for components
};
