#include "component_manager.h"
#include "toggle/toggle_component.h"
#include "multipleChoice/component_multiple_choice.h"
#include "../util.h"
#include "../root_task.h"
#include <logging.h>

ComponentManager::ComponentManager(RootTask &root_task, SemaphoreHandle_t mutex) : root_task_(root_task), screen_mutex_(mutex)
{
    component_mutex_ = xSemaphoreCreateMutex();
}

ComponentManager::~ComponentManager()
{
    // Deactivate current component
    deactivateAll();

    // Clear all components (shared_ptr will auto-delete)
    components_.clear();

    // Note: Don't use LOGI here - object might be destroyed during global cleanup
}

void ComponentManager::deactivateAll()
{
    SemaphoreGuard lock(component_mutex_);
    if (active_component_)
    {
        // Clear active reference under lock to prevent races
        active_component_ = nullptr;
        root_task_.setComponentMode(false);
        LOGI("ComponentManager: All components deactivated");
    }
}

void ComponentManager::add(const std::string &id, std::shared_ptr<Component> component)
{
    SemaphoreGuard lock(component_mutex_);
    components_.insert(std::make_pair(id, component));
}

void ComponentManager::clear()
{
    SemaphoreGuard lock(component_mutex_);
    components_.clear();
}

EntityStateUpdate ComponentManager::update(AppState state)
{
    // TODO: update with AppState
    SemaphoreGuard lock(component_mutex_);
    EntityStateUpdate new_state_update;

    if (active_component_ != nullptr)
    {
        // Relaxed: always forward state to the active component
        new_state_update = active_component_->updateStateFromKnob(state.motor_state);
        active_component_->updateStateFromSystem(state);
    }

    return new_state_update;
}

void ComponentManager::render()
{
    if (active_component_)
    {
        active_component_->render();
    }
};

bool ComponentManager::setActiveComponent(const std::string &component_id)
{
    SemaphoreGuard lock(component_mutex_);

    auto it = components_.find(component_id);
    if (it == components_.end())
    {
        LOGW("Component not found: %s", component_id.c_str());
        return false;
    }

    active_component_ = it->second;
    LOGI("ComponentManager: setActiveComponent('%s') type=%d", component_id.c_str(), (int)active_component_->getType());
    root_task_.setComponentMode(true);
    render(); // CRITICAL: Apps pattern - always call render when setting active
    return true;
}

bool ComponentManager::createComponent(PB_AppComponent config) // Pass by value
{
    // Validate configuration
    if (strlen(config.component_id) == 0)
    {
        LOGE("ComponentManager: Component ID is empty");
        return false;
    }

    LOGI("ComponentManager: Creating component '%s' (type=%d)",
         config.component_id, config.type);

    bool need_activate = false;
    bool need_refresh = false;

    std::string component_id(config.component_id);

    {
        // Serialize all mutations and pointer updates under component_mutex_
        SemaphoreGuard lock(component_mutex_);

        auto existing = components_.find(component_id);

        if (existing != components_.end())
        {
            // If type changed for same ID, destroy and recreate
            PB_ComponentType current_type = existing->second->getType();
            if (current_type != config.type)
            {
                LOGW("ComponentManager: Type change for '%s': %d -> %d, recreating component",
                     config.component_id, (int)current_type, (int)config.type);

                bool wasActive = (active_component_ == existing->second);

                // If active, clear active pointer first to prevent concurrent deref
                if (wasActive)
                {
                    active_component_ = nullptr;
                    root_task_.setComponentMode(false);
                }

                // Erase existing instance (shared_ptr will release when last ref drops)
                components_.erase(existing);

                // Create new instance of requested type
                auto new_component = createComponentByType(config.type, config);
                if (!new_component)
                {
                    LOGE("ComponentManager: Failed to recreate component '%s' of type %d",
                         config.component_id, (int)config.type);
                    return false;
                }

                // Store and wire motor notifier
                components_[component_id] = std::move(new_component);
                if (motor_notifier_ != nullptr)
                {
                    components_[component_id]->setMotorNotifier(motor_notifier_);
                }

                // If it was active, re-activate after releasing the lock
                if (wasActive)
                {
                    active_component_ = components_[component_id];
                    root_task_.setComponentMode(true);
                    need_activate = true; // defer render/motor update until after unlocking
                }

                LOGI("ComponentManager: Component '%s' recreated successfully", config.component_id);
            }
            else
            {
                LOGI("ComponentManager: Reconfiguring existing component '%s'", config.component_id);

                // Reconfigure existing component of same type
                bool success = existing->second->configure(config);
                if (!success)
                {
                    LOGE("ComponentManager: Failed to reconfigure component '%s'", config.component_id);
                    return false;
                }

                // If this component is currently active, refresh UI and motor config after unlocking
                if (active_component_ == existing->second)
                {
                    need_refresh = true;
                }

                LOGI("ComponentManager: Component '%s' reconfigured successfully", config.component_id);
            }
        }
        else
        {
            // Create new component
            LOGI("ComponentManager: About to create component of type %d", config.type);
            auto component = createComponentByType(config.type, config); // Pass the copy forward
            if (!component)
            {
                LOGE("ComponentManager: Failed to create component of type %d", config.type);
                return false;
            }
            LOGI("ComponentManager: Component '%s' created and configured in constructor", config.component_id);

            // Store the component
            components_[component_id] = std::move(component);

            // Set motor notifier if available (like Apps do)
            if (motor_notifier_)
            {
                components_[component_id]->setMotorNotifier(motor_notifier_);
            }

            LOGI("ComponentManager: Component '%s' created successfully", config.component_id);
        }
    } // unlock component_mutex_

    // Perform render/motor updates outside the lock to avoid deadlocks and long critical sections
    if (need_activate || need_refresh)
    {
        render();                   // Ensure screen reflects the new/updated configuration
        triggerMotorConfigUpdate(); // Push updated haptics/LEDs to MotorTask
    }

    return true;
}

bool ComponentManager::destroyComponent(const std::string &component_id)
{
    SemaphoreGuard lock(component_mutex_);

    auto it = components_.find(component_id);

    if (it == components_.end())
    {
        LOGW("ComponentManager: Component '%s' not found for destruction", component_id.c_str());
        return false;
    }

    // If this is the active component, deactivate it under lock
    if (active_component_ == it->second)
    {
        active_component_ = nullptr; // Just clear the reference (Apps don't have deactivate)
        root_task_.setComponentMode(false);
    }

    // Remove from map (shared_ptr will auto-delete)
    components_.erase(it);

    LOGI("ComponentManager: Component '%s' destroyed", component_id.c_str());
    return true;
}

void ComponentManager::setMotorNotifier(MotorNotifier *motor_notifier)
{
    this->motor_notifier_ = motor_notifier;
}

void ComponentManager::triggerMotorConfigUpdate()
{
    // Make thread-safe local copies under lock, then operate without holding the mutex
    std::shared_ptr<Component> local_active;
    MotorNotifier *local_notifier = nullptr;
    PB_SmartKnobConfig local_blocked_cfg;

    {
        SemaphoreGuard lock(component_mutex_);
        local_active = active_component_;
        local_notifier = motor_notifier_;
        local_blocked_cfg = blocked_motor_config;
    }

    if (local_active)
    {
        if (local_notifier != nullptr)
        {
            auto cfg = local_active->getMotorConfig();
            LOGI("ComponentManager: Triggering motor update for active='%s' type=%d cfg.id='%s' pos=%ld max=%ld hue=%d",
                 local_active->getComponentId(),
                 (int)local_active->getType(),
                 cfg.id,
                 (long)cfg.position,
                 (long)cfg.max_position,
                 (int)cfg.led_hue);
            local_notifier->requestUpdate(cfg);
        }
        else
        {
            LOGW("ComponentManager: motor_notifier_ is null for active component");
        }
    }
    else
    {
        if (local_notifier != nullptr)
        {
            LOGI("ComponentManager: Triggering motor config update for blocked state");
            local_notifier->requestUpdate(local_blocked_cfg);
        }
        else
        {
            LOGW("ComponentManager: motor_notifier_ is null for blocked state");
        }
    }
}

// ComponentManager doesn't need handleNavigationEvent - components use protobuf control

std::shared_ptr<Component> ComponentManager::find(const std::string &component_id)
{
    std::map<std::string, std::shared_ptr<Component>>::iterator it;
    for (it = components_.begin(); it != components_.end(); it++)
    {
        if (it->first == component_id)
        {
            return it->second;
        }
    }
    return nullptr;
}

std::shared_ptr<Component> ComponentManager::getActiveComponent()
{
    SemaphoreGuard lock(component_mutex_);
    // Return a copy-by-value under lock to safely increment refcount
    return active_component_;
}

void ComponentManager::setOSConfigNotifier(OSConfigNotifier *os_config_notifier)
{
    os_config_notifier_ = os_config_notifier;
}

std::shared_ptr<Component> ComponentManager::createComponentByType(
    PB_ComponentType type,
    PB_AppComponent config) // Pass by value
{
    switch (type)
    {
    case PB_ComponentType_TOGGLE:
        LOGI("ComponentManager: Creating ToggleComponent '%s' with full config", config.component_id);
        return std::shared_ptr<Component>(new ToggleComponent(
            screen_mutex_, // Pass mutex to App constructor
            config         // Pass the temporary copy, which is valid during the constructor call
            ));

    case PB_ComponentType_MULTI_CHOICE:
        LOGI("ComponentManager: Creating MultipleChoice '%s' with full config", config.component_id);
        return std::shared_ptr<Component>(new MultipleChoice(
            screen_mutex_, // Pass mutex to App constructor
            config         // Pass the temporary copy, which is valid during the constructor call
            ));

    default:
        LOGE("ComponentManager: Unknown component type %d", type);
        return nullptr;
    }
}