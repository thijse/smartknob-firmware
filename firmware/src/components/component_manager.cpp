#include "component_manager.h"
#include "toggle/toggle_component.h"
#include "../util.h"
#include <logging.h>
#include <string.h>

ComponentManager::ComponentManager(
    SemaphoreHandle_t mutex) : mutex_(mutex),
                               motor_notifier_(nullptr),
                               active_component_(nullptr)
{
    LOGI("ComponentManager: Initialized with App-based architecture");
}

ComponentManager::~ComponentManager()
{
    // Deactivate current component
    deactivateAll();

    // Clear all components (unique_ptr will auto-delete)
    components_.clear();

    // Note: Don't use LOGI here - object might be destroyed during global cleanup
}

bool ComponentManager::createComponent(const PB_AppComponent &config)
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
    auto component = createComponentByType(config.type, config);
    if (!component)
    {
        LOGE("ComponentManager: Failed to create component of type %d", config.type);
        return false;
    }
    LOGI("ComponentManager: Component '%s' created and configured in constructor", config.component_id);

    // No need to call configure() since it's done in constructor (like SwitchApp)
    LOGI("ComponentManager: Component '%s' configured successfully", config.component_id); // Store the component
    components_[component_id] = std::move(component);

    // Set motor notifier if available (like Apps do)
    if (motor_notifier_)
    {
        components_[component_id]->setMotorNotifier(motor_notifier_);
    }

    LOGI("ComponentManager: Component '%s' created successfully", config.component_id);
    return true;
}

void ComponentManager::setMotorNotifier(MotorNotifier *motor_notifier)
{
    motor_notifier_ = motor_notifier;

    // Set motor notifier on all existing components
    for (auto &pair : components_)
    {
        pair.second->setMotorNotifier(motor_notifier_);
    }

    LOGI("ComponentManager: Motor notifier set for %zu components", components_.size());
}

bool ComponentManager::destroyComponent(const char *component_id)
{
    std::string id(component_id);
    auto it = components_.find(id);

    if (it == components_.end())
    {
        LOGW("ComponentManager: Component '%s' not found for destruction", component_id);
        return false;
    }

    // If this is the active component, deactivate it
    if (active_component_ == it->second.get())
    {
        active_component_ = nullptr; // Just clear the reference (Apps don't have deactivate)
    }

    // Remove from map (unique_ptr will auto-delete)
    components_.erase(it);

    LOGI("ComponentManager: Component '%s' destroyed", component_id);
    return true;
}

Component *ComponentManager::getComponent(const char *component_id)
{
    std::string id(component_id);
    auto it = components_.find(id);

    if (it == components_.end())
    {
        return nullptr;
    }

    return it->second.get();
}

bool ComponentManager::setActiveComponent(const char *component_id)
{
    Component *component = getComponent(component_id);
    if (!component)
    {
        LOGE("ComponentManager: Cannot activate unknown component '%s'", component_id);
        return false;
    }

    // Deactivate current component
    if (active_component_)
    {
        // Apps don't have deactivate method, just clear reference
    }

    // Activate new component
    active_component_ = component;
    // Apps don't have activate method, they're active when set as active_component_

    LOGI("ComponentManager: Component '%s' activated", component_id);
    return true;
}

Component *ComponentManager::getActiveComponent()
{
    return active_component_;
}

void ComponentManager::deactivateAll()
{
    if (active_component_)
    {
        // Apps don't have deactivate method, just clear reference
        active_component_ = nullptr;
        LOGI("ComponentManager: All components deactivated");
    }
}

EntityStateUpdate ComponentManager::update(AppState state)
{
    if (active_component_)
    {
        // Call the component's updateStateFromKnob method (inherited from App)
        EntityStateUpdate entity_update = active_component_->updateStateFromKnob(state.motor_state);

        // Render the component (inherited from App)
        active_component_->render();

        return entity_update;
    }

    return EntityStateUpdate{};
}

size_t ComponentManager::getComponentCount() const
{
    return components_.size();
}

void ComponentManager::getComponentIds(char *buffer, size_t buffer_size) const
{
    if (buffer_size == 0)
        return;

    buffer[0] = '\0'; // Start with empty string

    bool first = true;
    for (const auto &pair : components_)
    {
        if (!first)
        {
            strncat(buffer, ", ", buffer_size - strlen(buffer) - 1);
        }
        strncat(buffer, pair.first.c_str(), buffer_size - strlen(buffer) - 1);
        first = false;
    }
}

std::unique_ptr<Component> ComponentManager::createComponentByType(
    PB_ComponentType type,
    const PB_AppComponent &config)
{
    switch (type)
    {
    case PB_ComponentType_TOGGLE:
        LOGI("ComponentManager: Creating ToggleComponent '%s' with full config", config.component_id);
        return std::unique_ptr<Component>(new ToggleComponent(
            mutex_,  // ✅ Pass mutex to App constructor
            config   // ✅ Pass full config for constructor-time configuration
            ));

    default:
        LOGE("ComponentManager: Unknown component type %d", type);
        return nullptr;
    }
}
