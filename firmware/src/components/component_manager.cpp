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
    if (active_component_)
    {
        // Apps don't have deactivate method, just clear reference
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
        // Only send state updates to component using config with same identifier.
        if (strcmp(state.motor_state.config.id, active_component_->app_id) == 0)
        {
            new_state_update = active_component_->updateStateFromKnob(state.motor_state);
            active_component_->updateStateFromSystem(state);
        }
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

    // Check if component already exists
    std::string component_id(config.component_id);
    auto existing = components_.find(component_id);

    if (existing != components_.end())
    {
        LOGI("ComponentManager: Reconfiguring existing component '%s'", config.component_id);

        // Reconfigure existing component
        bool success = existing->second->configure(config);
        if (!success)
        {
            LOGE("ComponentManager: Failed to reconfigure component '%s'", config.component_id);
            return false;
        }

        LOGI("ComponentManager: Component '%s' reconfigured successfully", config.component_id);
        return true;
    }

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
    return true;
}

bool ComponentManager::destroyComponent(const std::string &component_id)
{
    auto it = components_.find(component_id);

    if (it == components_.end())
    {
        LOGW("ComponentManager: Component '%s' not found for destruction", component_id.c_str());
        return false;
    }

    // If this is the active component, deactivate it
    if (active_component_ == it->second)
    {
        active_component_ = nullptr; // Just clear the reference (Apps don't have deactivate)
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
    if (active_component_)
    {
        if (this->motor_notifier_ != nullptr)
        {
            LOGI("ComponentManager: Triggering motor config update for active component");
            motor_notifier_->requestUpdate(active_component_->getMotorConfig());
        }
    }
    else
    {
        if (this->motor_notifier_ != nullptr)
        {
            LOGI("ComponentManager: Triggering motor config update for blocked state");
            motor_notifier_->requestUpdate(blocked_motor_config);
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