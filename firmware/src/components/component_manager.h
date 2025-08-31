#pragma once

#include <map>
#include <memory>
#include <string>

#include "../app_config.h"
#include "../notify/motor_notifier/motor_notifier.h"
#include "../navigation/navigation.h"
#include "../notify/os_config_notifier/os_config_notifier.h"
#include "component.h"

class ComponentManager
{

public:
    ComponentManager(SemaphoreHandle_t mutex);
    ~ComponentManager(); // Add explicit destructor declaration

    // === APPS-PATTERN METHODS (keep these exactly) ===
    void render();                                                  // Like Apps::render()
    void triggerMotorConfigUpdate();                                // Like Apps::triggerMotorConfigUpdate()
    EntityStateUpdate update(AppState state);                       // Like Apps::update()
    void setMotorNotifier(MotorNotifier *motor_notifier);           // Like Apps::setMotorNotifier()
    void setOSConfigNotifier(OSConfigNotifier *os_config_notifier); // Like Apps::setOSConfigNotifier()

    // === COMPONENT-SPECIFIC METHODS ===
    bool createComponent(const PB_AppComponent &config);                   // From original ComponentManager
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

private:
    std::shared_ptr<Component> createComponentByType(PB_ComponentType type, const PB_AppComponent &config); // From original

protected:
    SemaphoreHandle_t screen_mutex_;
    SemaphoreHandle_t component_mutex_; // Like app_mutex_ but for components

    std::map<std::string, std::shared_ptr<Component>> components_; // Like apps but string keys for components

    std::shared_ptr<Component> active_component_ = nullptr; // Like active_app

    std::shared_ptr<Component> find(uint8_t id); // Keep for compatibility (might be unused)

    PB_SmartKnobConfig root_level_motor_config;

    MotorNotifier *motor_notifier;

    OSConfigNotifier *os_config_notifier_;
};
