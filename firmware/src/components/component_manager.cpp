#include "component_manager.h"
#include "toggle/toggle_component.h"
#include "../util.h"
#include <logging.h>
#include <string.h>

ComponentManager::ComponentManager(
    QueueHandle_t motor_task_queue,
    QueueHandle_t display_task_queue,
    QueueHandle_t led_ring_task_queue,
    SemaphoreHandle_t mutex
) : motor_task_queue_(motor_task_queue),
    display_task_queue_(display_task_queue),
    led_ring_task_queue_(led_ring_task_queue),
    mutex_(mutex),
    active_component_(nullptr)
{
    // Note: Don't use LOGI here - logging system may not be initialized during global construction
}

ComponentManager::~ComponentManager() {
    // Deactivate current component
    deactivateAll();
    
    // Clear all components (unique_ptr will auto-delete)
    components_.clear();
    
    // Note: Don't use LOGI here - object might be destroyed during global cleanup
}

bool ComponentManager::createComponent(const PB_AppComponent& config) {
    // Validate configuration
    if (strlen(config.component_id) == 0) {
        LOGE("ComponentManager: Component ID is empty");
        return false;
    }
    
    LOGI("ComponentManager: Creating component '%s' (type=%d)", 
         config.component_id, config.type);
    
    // Check if component already exists
    std::string component_id(config.component_id);
    auto existing = components_.find(component_id);
    
    if (existing != components_.end()) {
        LOGI("ComponentManager: Reconfiguring existing component '%s'", config.component_id);
        
        // Reconfigure existing component
        bool success = existing->second->configure(config);
        if (!success) {
            LOGE("ComponentManager: Failed to reconfigure component '%s'", config.component_id);
            return false;
        }
        
        LOGI("ComponentManager: Component '%s' reconfigured successfully", config.component_id);
        return true;
    }
    
    // Create new component
    auto component = createComponentByType(config.type, config.component_id);
    if (!component) {
        LOGE("ComponentManager: Failed to create component of type %d", config.type);
        return false;
    }
    
    // Configure the component
    bool success = component->configure(config);
    if (!success) {
        LOGE("ComponentManager: Failed to configure component '%s'", config.component_id);
        return false;
    }
    
    // Store the component
    components_[component_id] = std::move(component);
    
    LOGI("ComponentManager: Component '%s' created successfully", config.component_id);
    return true;
}

bool ComponentManager::destroyComponent(const char* component_id) {
    std::string id(component_id);
    auto it = components_.find(id);
    
    if (it == components_.end()) {
        LOGW("ComponentManager: Component '%s' not found for destruction", component_id);
        return false;
    }
    
    // If this is the active component, deactivate it
    if (active_component_ == it->second.get()) {
        active_component_->deactivate();
        active_component_ = nullptr;
    }
    
    // Remove from map (unique_ptr will auto-delete)
    components_.erase(it);
    
    LOGI("ComponentManager: Component '%s' destroyed", component_id);
    return true;
}

Component* ComponentManager::getComponent(const char* component_id) {
    std::string id(component_id);
    auto it = components_.find(id);
    
    if (it == components_.end()) {
        return nullptr;
    }
    
    return it->second.get();
}

bool ComponentManager::setActiveComponent(const char* component_id) {
    Component* component = getComponent(component_id);
    if (!component) {
        LOGE("ComponentManager: Cannot activate unknown component '%s'", component_id);
        return false;
    }
    
    // Deactivate current component
    if (active_component_) {
        active_component_->deactivate();
    }
    
    // Activate new component
    active_component_ = component;
    active_component_->activate();
    
    LOGI("ComponentManager: Component '%s' activated", component_id);
    return true;
}

Component* ComponentManager::getActiveComponent() {
    return active_component_;
}

void ComponentManager::deactivateAll() {
    if (active_component_) {
        active_component_->deactivate();
        active_component_ = nullptr;
        LOGI("ComponentManager: All components deactivated");
    }
}

void ComponentManager::handleKnobInput(const PB_SmartKnobState& state) {
    if (active_component_) {
        active_component_->handleKnobInput(state);
    }
}

void ComponentManager::handleButtonInput(bool pressed) {
    if (active_component_) {
        active_component_->handleButtonInput(pressed);
    }
}

void ComponentManager::renderActiveComponent() {
    if (active_component_) {
        active_component_->render();
    }
}

size_t ComponentManager::getComponentCount() const {
    return components_.size();
}

void ComponentManager::getComponentIds(char* buffer, size_t buffer_size) const {
    if (buffer_size == 0) return;
    
    buffer[0] = '\0';  // Start with empty string
    
    bool first = true;
    for (const auto& pair : components_) {
        if (!first) {
            strncat(buffer, ", ", buffer_size - strlen(buffer) - 1);
        }
        strncat(buffer, pair.first.c_str(), buffer_size - strlen(buffer) - 1);
        first = false;
    }
}

std::unique_ptr<Component> ComponentManager::createComponentByType(
    PB_ComponentType type,
    const char* component_id
) {
    switch (type) {
        case PB_ComponentType_TOGGLE:
            LOGI("ComponentManager: Creating ToggleComponent '%s'", component_id);
            return std::unique_ptr<Component>(new ToggleComponent(
                component_id,
                motor_task_queue_,
                display_task_queue_,
                led_ring_task_queue_,
                mutex_
            ));
            
        default:
            LOGE("ComponentManager: Unknown component type %d", type);
            return nullptr;
    }
}
