# SmartKnob Component Switching Root Cause Analysis & Solution

**Date:** September 14, 2025  
**Issue:** Device crashes and instability when switching between Toggle and MultipleChoice components  
**Severity:** Critical - Causes device resets and prevents proper component functionality

## Executive Summary

The SmartKnob firmware experiences critical stability issues when switching between different component types (Toggle ↔ MultipleChoice). The device frequently crashes with `LoadProhibited` exceptions and requires hardware resets to recover. Root cause analysis reveals **race conditions during component lifecycle management** combined with **unsafe LVGL object handling** during component transitions.

## Symptoms Observed

1. **Single Switch Limitation**: Components can only be switched once before requiring device reset
2. **Configuration Update Failures**: Same component with different configuration values fails to apply
3. **Crash Pattern**: `LoadProhibited` exceptions at memory address `0x00040004` 
4. **Timing Dependency**: Crashes occur specifically during Toggle→MultipleChoice transitions
5. **Recovery Requirement**: Device reset needed to restore functionality

## Root Cause Analysis

### Primary Issue: Component Lifecycle Race Conditions

#### Problem 1: Concurrent Object Access During Destruction
```cpp
// ComponentManager::createComponent() - UNSAFE SEQUENCE
auto component = createComponentByType(config.type, config); // New component creates LVGL objects
// ❌ OLD component still active! Still receiving updateStateFromKnob() calls!
components_[component_id] = std::move(component); // Old component destructor runs NOW
```

**Race Window**: The main RootTask loop continues executing during component switching:
```cpp
// RootTask main loop - NEVER STOPS
while (1) {
    if (xQueueReceive(knob_state_queue_, &latest_state_, 0) == pdTRUE) {
        // ❌ This executes WHILE component destructor is running!
        entity_state_update_to_send = component_manager_->update(app_state);
        // Calls active_component_->updateStateFromKnob() on partially destructed object!
    }
}
```

#### Problem 2: LVGL Object Collision on Shared Screen
```cpp
// OLD MultipleChoice objects still exist:
lv_obj_t* title_label_;   // Still valid during destruction
lv_obj_t* option_label_;  // Still valid during destruction

// NEW MultipleChoice constructor creates objects on SAME screen:
title_label_ = lv_label_create(screen);  // Same parent screen!
option_label_ = lv_label_create(screen); // Same parent screen!

// Result: DUPLICATE objects exist until old destructor completes
```

#### Problem 3: No Explicit Component Deactivation
Components lack explicit deactivation mechanism:
- No way to stop incoming `updateStateFromKnob()` calls during destruction
- LVGL objects deleted in destructor, but too late to prevent corruption
- `active_component_` pointer switches before old component fully cleaned up

### Secondary Issues

#### Task Creation Pattern (Initially Suspected, Actually Safe)
The per-packet FreeRTOS task creation was initially suspected but analysis confirms it's safe:
```cpp
TagHandlerParams *params = new TagHandlerParams{
    new std::function<void(const PB_ToSmartknob &)>(callback),
    pb_rx_buffer_  // ✅ Creates full struct copy by value - SAFE
};
```
Nanopb static allocation ensures proper deep copying of string arrays.

#### Memory Fragmentation (Contributing Factor)
- 8KB stack per protocol handling task
- Multiple component creation/destruction cycles
- Large font objects (48pt roboto_regular_mono_48pt) increase allocation pressure

## Impact Analysis

### Memory Corruption Chain
1. **Component Switch Initiated**: New MultipleChoice component created
2. **Object Creation**: New LVGL objects created on shared screen
3. **Parallel Execution**: Old component still receiving motor state updates
4. **Corruption Point**: Old component calls `updateDisplay()` → `lv_label_set_text()`
5. **Crash**: LVGL internal pointer dereference fails → `LoadProhibited` exception

### Why MultipleChoice Triggers More Failures
- Creates 3 LVGL objects (vs Toggle's 2-3)
- Uses large 48pt font (higher memory pressure)
- More complex display update logic increases corruption window

## Solution Implementation

### Phase 1: Critical Stability Fixes

#### Fix 1: Add Component Deactivation Pattern
```cpp
// In component.h
class Component : public App {
private:
    std::atomic<bool> active_{true};
    
public:
    virtual ~Component() {
        deactivate(); // Ensure cleanup on destruction
    }
    
    virtual void deactivate() {
        active_ = false; // Stop processing new calls immediately
        cleanupLVGLObjects(); // Safe cleanup under mutex
    }
    
protected:
    virtual void cleanupLVGLObjects() {
        SemaphoreGuard lock(mutex_);
        if (title_label_) {
            lv_obj_del(title_label_);
            title_label_ = nullptr;
        }
        if (option_label_) {
            lv_obj_del(option_label_);
            option_label_ = nullptr;
        }
        if (position_label_) {
            lv_obj_del(position_label_);
            position_label_ = nullptr;
        }
    }
    
    // Guard all public methods with active check
    EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) override {
        if (!active_) {
            return EntityStateUpdate{}; // Return empty update
        }
        return updateStateFromKnobImpl(state);
    }
    
protected:
    virtual EntityStateUpdate updateStateFromKnobImpl(PB_SmartKnobState state) = 0;
};
```

#### Fix 2: Safe Component Manager Switching
```cpp
// In component_manager.cpp
bool ComponentManager::createComponent(PB_AppComponent config) {
    SemaphoreGuard lock(component_mutex_);
    
    std::string component_id(config.component_id);
    auto existing = components_.find(component_id);
    
    if (existing != components_.end()) {
        bool wasActive = (active_component_ == existing->second);
        
        // ✅ CRITICAL: Deactivate old component FIRST
        if (wasActive) {
            active_component_ = nullptr; // Stop routing calls immediately
            existing->second->deactivate(); // Clean up LVGL objects safely
        }
        
        // Remove old component (destructor runs with no active calls)
        components_.erase(existing);
        
        // Create new component
        auto new_component = createComponentByType(config.type, config);
        if (!new_component) return false;
        
        components_[component_id] = std::move(new_component);
        
        // Re-activate if it was previously active
        if (wasActive) {
            active_component_ = components_[component_id];
            render();
            triggerMotorConfigUpdate();
        }
        
        return true;
    }
    
    // ... rest of new component creation
}
```

#### Fix 3: Protected Update Method
```cpp
EntityStateUpdate ComponentManager::update(AppState state) {
    SemaphoreGuard lock(component_mutex_); // Prevent switching during update
    
    if (active_component_ != nullptr) {
        return active_component_->updateStateFromKnob(state.motor_state);
    }
    
    return EntityStateUpdate{};
}
```

### Phase 2: Architecture Improvements

#### Fix 4: Per-Component Container Pattern
```cpp
// In component.cpp - Base class implementation
void Component::createContainer() {
    if (!container_) {
        SemaphoreGuard lock(mutex_);
        container_ = lv_obj_create(screen);
        lv_obj_remove_style_all(container_);
        lv_obj_set_size(container_, LV_HOR_RES, LV_VER_RES);
        lv_obj_clear_flag(container_, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(container_, LV_OBJ_FLAG_HIDDEN); // Start hidden
    }
}

// In component_multiple_choice.cpp - Updated initScreen()
void MultipleChoice::initScreen() {
    createContainer(); // Create isolated container first
    
    SemaphoreGuard lock(mutex_);
    
    // Parent ALL objects to container_ instead of screen
    title_label_ = lv_label_create(container_);
    option_label_ = lv_label_create(container_);
    if (config_.options_count > 1) {
        position_label_ = lv_label_create(container_);
    }
    // ... rest of setup
}
```

#### Fix 5: Component Show/Hide During Activation
```cpp
// In component_manager.cpp - Updated setActiveComponent()
bool ComponentManager::setActiveComponent(const std::string &component_id) {
    SemaphoreGuard lock(component_mutex_);
    
    // Hide current component container
    if (active_component_ && active_component_->container_) {
        SemaphoreGuard lvgl_lock(screen_mutex_);
        lv_obj_add_flag(active_component_->container_, LV_OBJ_FLAG_HIDDEN);
    }
    
    auto it = components_.find(component_id);
    if (it == components_.end()) return false;
    
    active_component_ = it->second;
    
    // Show new component container
    if (active_component_->container_) {
        SemaphoreGuard lvgl_lock(screen_mutex_);
        lv_obj_clear_flag(active_component_->container_, LV_OBJ_FLAG_HIDDEN);
    }
    
    render();
    return true;
}
```

## Validation Plan

### Testing Procedure
1. **Implement Phase 1 fixes** (critical stability)
2. **Run extended alternating test**: `toggle_then_multiple_choice.py` for 500+ cycles
3. **Monitor for**:
   - No "Component mode active increment" warnings
   - No device resets
   - Successful component switching in both directions
4. **Heap monitoring**: Track memory usage before/after each switch
5. **If still unstable**: Implement Phase 2 fixes (container pattern)

### Success Criteria
- ✅ Clean component switching without crashes
- ✅ Configuration updates work correctly  
- ✅ No memory leaks during repeated switches
- ✅ Consistent motor and display behavior
- ✅ No device resets required

## Prevention Measures

### Code Review Checklist
- [ ] All component public methods check `active_` flag
- [ ] LVGL operations always use mutex protection
- [ ] Component switching follows deactivate→create→activate sequence
- [ ] Container pattern used for UI object isolation
- [ ] Destructor cleanup is explicit and immediate

### Architecture Principles
1. **Explicit Lifecycle**: Components must explicitly transition between active/inactive states
2. **UI Isolation**: Each component gets dedicated LVGL container
3. **Atomic Switching**: Component manager ensures no parallel access during transitions
4. **Defensive Programming**: All public component methods guard against inactive state

## Files Requiring Changes

### Primary Changes (Phase 1)
- `firmware/src/components/component.h` - Add deactivation pattern
- `firmware/src/components/component.cpp` - Implement base deactivation logic
- `firmware/src/components/component_manager.cpp` - Safe switching protocol
- `firmware/src/components/component_manager.h` - Add component_mutex_

### Secondary Changes (Phase 2)
- `firmware/src/components/multipleChoice/component_multiple_choice.cpp` - Container pattern
- `firmware/src/components/toggle/toggle_component.cpp` - Container pattern
- All component implementations - Update initScreen() methods

## Test Files
- `smartknob-connection/tests/toggle_then_multiple_choice.py` - Primary reproduction test
- Add new test: `smartknob-connection/tests/stress_component_switching.py`

## Conclusion

The root cause was **component lifecycle race conditions** where old components continued receiving method calls during destruction while new components created conflicting LVGL objects. The solution requires explicit component deactivation and safe switching protocols to prevent concurrent access during transitions.

Implementation of the deactivation pattern should resolve the immediate stability issues, with the container pattern providing long-term architectural robustness for complex UI scenarios.

## References

### Related Code Locations
- Race condition: `firmware/src/root_task.cpp` main loop
- Object collision: `firmware/src/components/multipleChoice/component_multiple_choice.cpp:119-136`
- Missing deactivation: `firmware/src/components/component_manager.cpp:81-95`
- Crash evidence: Raw serial logs showing `LoadProhibited` at `0x00040004`

### Performance Impact
- Phase 1 fixes: Minimal overhead (atomic bool check per method call)
- Phase 2 fixes: Slight memory overhead per component (one container object)
- Expected improvement: 100% stability, no crashes during component switching