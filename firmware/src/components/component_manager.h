#pragma once

#include <map>
#include <memory>
#include <string>

#include "../app_config.h"
#include "../notify/motor_notifier/motor_notifier.h"
#include "../navigation/navigation.h"
#include "../notify/os_config_notifier/os_config_notifier.h"
#include "component.h"

// Forward declaration
class RootTask;

class ComponentManager
{

public:
    ComponentManager(RootTask &root_task, SemaphoreHandle_t mutex);
    ~ComponentManager(); // Add explicit destructor declaration

    // === APPS-PATTERN METHODS (keep these exactly) ===
    void render();                                                  // Like Apps::render()
    void triggerMotorConfigUpdate();                                // Like Apps::triggerMotorConfigUpdate()
    EntityStateUpdate update(AppState state);                       // Like Apps::update()
    void setMotorNotifier(MotorNotifier *motor_notifier);           // Like Apps::setMotorNotifier()
    void setOSConfigNotifier(OSConfigNotifier *os_config_notifier); // Like Apps::setOSConfigNotifier()

    // === COMPONENT-SPECIFIC METHODS ===
    bool createComponent(PB_AppComponent config);                          // Pass by value
    bool destroyComponent(const std::string &component_id);                // From original ComponentManager
    bool setActiveComponent(const std::string &component_id);              // From original (but modify to call render())
    std::shared_ptr<Component> getActiveComponent();                       // From original
    void add(const std::string &id, std::shared_ptr<Component> component); // Like Apps::add but for components
    void deactivateAll();                                                  // From original ComponentManager

    // === COLLECTION MANAGEMENT (Apps pattern) ===
    void clear();                                                     // Like Apps::clear()
    std::shared_ptr<Component> find(const std::string &component_id); // Like Apps::find()

    PB_SmartKnobConfig blocked_motor_config = {
        .position_width_radians = 60 * M_PI / 180,
        .endstop_strength_unit = 0,
        .snap_point = 0.5,
        .detent_positions_count = 0,
        .detent_positions = {},
    };

    PB_SmartKnobConfig getMotorConfig()
    {
        return motor_config_;
    }

private:
    std::shared_ptr<Component> createComponentByType(PB_ComponentType type, PB_AppComponent config); // Pass by value

protected:
    RootTask &root_task_;
    SemaphoreHandle_t screen_mutex_;
    SemaphoreHandle_t component_mutex_; // Like app_mutex_ but for components

    std::map<std::string, std::shared_ptr<Component>> components_; // Like apps but string keys for components

    std::shared_ptr<Component> active_component_ = nullptr;

    MotorNotifier *motor_notifier_;        // From Apps
    OSConfigNotifier *os_config_notifier_; // From Apps
    PB_SmartKnobConfig motor_config_ = {
        .detent_strength_unit = 0,
        .endstop_strength_unit = 1,
        .snap_point = 1.1,
        .detent_positions_count = 0,
        .snap_point_bias = 0,
    };
};
