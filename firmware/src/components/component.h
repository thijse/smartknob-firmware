#pragma once

#include <Arduino.h>
#include <FreeRTOS.h>
#include <semphr.h>
#include "../apps/app.h" // ✅ Inherit from App!
#include "../proto/proto_gen/smartknob.pb.h"

// Forward declarations
class RootTask;

/**
 * Base class for remote-configurable SmartKnob components.
 *
 * Components are interactive elements that can be configured remotely
 * via protobuf messages. Unlike traditional apps, components are:
 * - Dynamically created at runtime
 * - Fully configurable via protocol messages
 * - Designed for remote control scenarios
 *
 * Components inherit from App to leverage the proven hardware integration,
 * motor notifier access, and display management that Apps provide.
 */
class Component : public App
{ // ✅ Inherit from App!
public:
    /**
     * Create a new component with the given ID.
     *
     * @param mutex Mutex for thread-safe operations (passed to App)
     * @param component_id Unique identifier for this component instance
     */
    Component(SemaphoreHandle_t mutex, const char *component_id);

    virtual ~Component() = default;

    // ========== Component-Specific Interface ==========

    /**
     * Configure this component with the provided settings.
     * Components implement this to handle their specific configuration.
     *
     * @param config Complete component configuration
     * @return true if configuration was applied successfully
     */
    virtual bool configure(const PB_AppComponent &config) = 0;

    /**
     * Get the unique ID of this component.
     */
    const char *getComponentId() const { return component_id_; }

    /**
     * Get the type name of this component (for debugging/logging).
     */
    virtual const char *getComponentType() const = 0;

    /**
     * Set component state from external source (e.g., MQTT, REST API).
     *
     * @param state_json JSON string representing the new state
     */
    virtual void setState(const char *state_json) {}

    /**
     * Get current component state as JSON string.
     *
     * @return JSON representation of current state
     */
    virtual const char *getState() { return "{}"; }

    // ========== App Interface (Inherited) ==========
    // Components can override these App methods as needed:
    // - EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state)
    // - void render()
    // - void updateStateFromSystem(AppState state)
    // - int8_t getAppId() (components should return unique negative IDs)

protected:
    // ========== Component State ==========

    char component_id_[33];            // Unique component identifier
    PB_AppComponent component_config_; // Current configuration

};
