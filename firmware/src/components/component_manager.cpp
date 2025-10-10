#include "component_manager.h"
#include "toggle/toggle_component.h"
#include "multipleChoice/component_multiple_choice.h"
#include "../util.h"
#include "../root_task.h"
#include <logging.h>
#include <string.h>
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
    // Take a safe local copy of the active component under lock, then operate without holding the mutex.
    std::shared_ptr<Component> local_active;
    {
        SemaphoreGuard lock(component_mutex_);
        local_active = active_component_;
    }

    EntityStateUpdate new_state_update;
    if (local_active != nullptr)
    {
        new_state_update = local_active->updateStateFromKnob(state.motor_state);
        local_active->updateStateFromSystem(state);
    }
    return new_state_update;
}

void ComponentManager::render()
{
    // Take a safe local copy under lock to avoid TOCTOU/use-after-free
    std::shared_ptr<Component> local_active;
    {
        SemaphoreGuard lock(component_mutex_);
        local_active = active_component_;
    }

    if (local_active)
    {
        LOGI("ComponentManager: render begin active='%s' type=%d",
             local_active->getComponentId(), (int)local_active->getType());
        local_active->render();
        LOGI("ComponentManager: render end active='%s'", local_active->getComponentId());
    }
};

bool ComponentManager::setActiveComponent(const std::string &component_id)
{
    std::shared_ptr<Component> local_active;
    {
        SemaphoreGuard lock(component_mutex_);

        auto it = components_.find(component_id);
        if (it == components_.end())
        {
            LOGW("Component not found: %s", component_id.c_str());
            return false;
        }

        active_component_ = it->second;
        local_active = active_component_;
        LOGI("ComponentManager: setActiveComponent('%s') type=%d", component_id.c_str(), (int)active_component_->getType());
        root_task_.setComponentMode(true);
    }

    // Call render outside the component mutex to avoid deadlocks with render() re-locking
    render(); // Ensure screen reflects the new active component
    return true;
}

bool ComponentManager::createComponent(PB_AppComponent config) // Pass by value
{
    LOGI("ComponentManager: createComponent ENTRY type=%d which=%d", (int)config.type, (int)config.which_component_config);

    // Validate configuration and make a safe, null-terminated copy of component_id
    size_t id_len = strnlen(config.component_id, sizeof(config.component_id));
    LOGI("ComponentManager: createComponent id_len=%u", (unsigned)id_len);
    if (id_len == 0)
    {
        LOGE("ComponentManager: Component ID is empty");
        return false;
    }
    char id_buf[sizeof(config.component_id) + 1];
    memcpy(id_buf, config.component_id, id_len);
    id_buf[id_len] = '\0';
    std::string component_id(id_buf);

    LOGI("ComponentManager: Creating component '%s' (type=%d)",
         component_id.c_str(), config.type);
    // Verbose: dump type-specific config preview to verify first-creation parity
    if (config.type == PB_ComponentType_TOGGLE && config.which_component_config == PB_AppComponent_toggle_tag)
    {
        const auto &t = config.component_config.toggle;
        LOGI("ComponentManager: TOGGLE cfg id='%s' snap_point=%.2f bias=%.2f detent=%.2f hues off/on=%d/%d initial_state=%d",
             id_buf,
             (double)t.snap_point, (double)t.snap_point_bias, (double)t.detent_strength_unit,
             (int)t.off_led_hue, (int)t.on_led_hue, (int)t.initial_state);
    }
    else if (config.type == PB_ComponentType_MULTI_CHOICE && config.which_component_config == PB_AppComponent_multi_choice_tag)
    {
        const auto &m = config.component_config.multi_choice;
        LOGI("ComponentManager: MULTI_CHOICE cfg id='%s' options=%d initial_index=%d detent=%.2f endstop=%.2f hue=%d wrap=%d",
             id_buf,
             (int)m.options_count, (int)m.initial_index,
             (double)m.detent_strength_unit, (double)m.endstop_strength_unit, (int)m.led_hue, (int)m.wrap_around);
    }

    bool need_activate = false;
    bool need_refresh = false;

    std::string component_id_copy = component_id;      // maintain original variable name usage below
    std::string &component_id_ref = component_id_copy; // alias for compatibility
    std::string component_id_original = component_id;  // backup (not strictly needed)
    // Ensure we proceed using 'component_id' identifier
    component_id = component_id_ref;

    // Pre-create optimization removed: createComponentByType will be invoked inside the lock
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
                     component_id.c_str(), (int)current_type, (int)config.type);

                bool wasActive = (active_component_ == existing->second);

                // If active, clear active pointer first to prevent concurrent deref
                if (wasActive)
                {
                    active_component_ = nullptr;
                    root_task_.setComponentMode(false);
                }

                // Erase existing instance (shared_ptr will release when last ref drops)
                components_.erase(existing);

                // Create new instance of requested type (prefer pre-created outside lock)
                auto new_component = createComponentByType(config.type, config);
                if (!new_component)
                {
                    LOGE("ComponentManager: Failed to recreate component '%s' of type %d",
                         component_id.c_str(), (int)config.type);
                    return false;
                }

                // Store and wire motor notifier
                components_[component_id] = new_component;
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

                LOGI("ComponentManager: Component '%s' recreated successfully", component_id.c_str());
            }
            else
            {
                LOGI("ComponentManager: Reconfiguring existing component '%s'", component_id.c_str());

                // Reconfigure existing component of same type
                bool success = existing->second->configure(config);
                if (!success)
                {
                    LOGE("ComponentManager: Failed to reconfigure component '%s'", component_id.c_str());
                    return false;
                }

                // If this component is currently active, refresh UI and motor config after unlocking
                if (active_component_ == existing->second)
                {
                    need_refresh = true;
                }

                LOGI("ComponentManager: Component '%s' reconfigured successfully", component_id.c_str());
            }
        }
        else
        {
            // Create new component (prefer pre-created outside lock)
            LOGI("ComponentManager: About to create component of type %d", config.type);
            auto component = createComponentByType(config.type, config);
            if (!component)
            {
                LOGE("ComponentManager: Failed to create component of type %d", config.type);
                return false;
            }
            LOGI("ComponentManager: Component '%s' created and configured in constructor", component_id.c_str());

            // Store the component
            components_[component_id] = component;

            // Set motor notifier if available (like Apps do)
            if (motor_notifier_)
            {
                components_[component_id]->setMotorNotifier(motor_notifier_);
            }

            LOGI("ComponentManager: Component '%s' created successfully", component_id.c_str());
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
        LOGI("ComponentManager: Creating ToggleComponent with full config");
        return std::shared_ptr<Component>(new ToggleComponent(
            screen_mutex_, // Pass mutex to App constructor
            config         // Pass the temporary copy, which is valid during the constructor call
            ));

    case PB_ComponentType_MULTI_CHOICE:
        LOGI("ComponentManager: Creating MultipleChoice with full config");
        return std::shared_ptr<Component>(new MultipleChoice(
            screen_mutex_, // Pass mutex to App constructor
            config         // Pass the temporary copy, which is valid during the constructor call
            ));

    default:
        LOGE("ComponentManager: Unknown component type %d", type);
        return nullptr;
    }
}