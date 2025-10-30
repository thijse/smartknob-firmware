#pragma once

#include "../app.h"

// MultipleChoiceApp: A simple selector app with hardcoded options
// Migrated from Component architecture to App architecture for stability

class MultipleChoiceApp : public App
{
public:
    // Constructor: copies identifiers, sets icons, initializes motor_config, and builds UI.
    MultipleChoiceApp(SemaphoreHandle_t mutex, char *app_id_, char *friendly_name_, char *entity_id_);

    // Called on each motor state update; maps current_position to option index
    // and emits JSON state on change.
    EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) override;

    // SHORT press: stay in app (no navigation)
    int8_t navigationNext() override;

    // LONG press: go back to Menu
    int8_t navigationBack() override;

    // Handle navigation events
    void handleNavigation(NavigationEvent event) override;

    // Set which option list to display (for sub-index support)
    void setSubIndex(uint8_t sub_index);

protected:
    void initScreen() override;

private:
    // UI elements
    lv_obj_t *title_label_ = nullptr;
    lv_obj_t *option_label_ = nullptr;

    // Partial ring selector visuals (from angle_selector)
    lv_obj_t *selector_arc = nullptr;
    lv_obj_t **selector_dots = nullptr;

    // Current sub-index (which option list is active)
    uint8_t current_sub_index_ = 0;

    // Define multiple option lists
    static constexpr uint8_t NUM_LISTS_ = 7;
    static constexpr uint8_t MAX_OPTIONS_PER_LIST_ = 4;
    static const char *const OPTION_LISTS_[NUM_LISTS_][MAX_OPTIONS_PER_LIST_];
    static const char *const LIST_TITLES_[NUM_LISTS_];
    static const uint8_t LIST_OPTION_COUNTS_[NUM_LISTS_];

    // State tracking
    int current_position = 0;
    int last_position = -1;

    // Selector arc styling (from angle_selector)
    static constexpr uint16_t width = 220;
    static constexpr uint8_t arc_width = 8;
    static constexpr uint16_t top_center_angle = 270;
    const lv_color_t arc_bg_color = LV_COLOR_MAKE(0x38, 0x38, 0x38);
    const lv_color_t active_dot_color = LV_COLOR_MAKE(0xFF, 0xFF, 0xFF);
    const lv_color_t inactive_color = LV_COLOR_MAKE(0x60, 0x60, 0x60);

    // Helper methods
    void updateDisplay();
    const char *get_selected_text() const;
    void initSelectorArc_();
    void updateSelectorVisual_(uint8_t selected_index);

    // Helper to get current option list
    const char *const *getCurrentOptions_() const;
    uint8_t getCurrentOptionsCount_() const;
};
