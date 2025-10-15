#pragma once

#include "../app.h"

// AngleSelectorApp: rotates through clinical C-arm presets and emits state immediately on rotation.
// Presets are displayed as two lines, e.g. top "LAO 25°" and bottom "Cranial 15°".
// Interaction semantics (v1):
// - Rotation: immediate emit (browse-to-emit) with wrap-around
// - SHORT press: no-op
// - LONG press: return to Menu

class AngleSelectorApp : public App
{
public:
    // Constructor: copies identifiers, sets icons, initializes motor_config, and builds UI.
    AngleSelectorApp(SemaphoreHandle_t mutex, char *app_id_, char *friendly_name_, char *entity_id_);

    // Called on each motor state update; maps current_position to a preset index via modulo
    // and emits JSON on index change.
    EntityStateUpdate updateStateFromKnob(PB_SmartKnobState state) override;

    // SHORT press: do not navigate away; keep within app (no-op).
    int8_t navigationNext() override;

    // LONG press: go back to Menu.
    int8_t navigationBack() override;

    // For completeness; LONG handled via navigationBack(), SHORT no-op.
    void handleNavigation(NavigationEvent event) override;

protected:
    void initScreen() override;

private:
    struct Preset
    {
        const char *primary;   // e.g., "LAO 25°"
        const char *secondary; // e.g., "Cranial 15°"
        int16_t lao_deg;       // Positive LAO; negative RAO
        int16_t cranial_deg;   // Positive Cranial; negative Caudal
    };

    // v1 preset set; defined in .cpp
    static const Preset PRESETS_[];
    static const uint8_t PRESET_COUNT_;

    // Current and last indices for change detection
    uint8_t current_index_ = 0;
    uint8_t last_index_ = 255; // sentinel to ensure first update emits

    // UI elements
    lv_obj_t *label_primary_ = nullptr;
    lv_obj_t *label_secondary_ = nullptr;
    lv_obj_t *img_preset_ = nullptr;
    // Outline labels (up, down, left, right) to simulate text stroke
    lv_obj_t *label_primary_outline_[4] = {nullptr, nullptr, nullptr, nullptr};
    lv_obj_t *label_secondary_outline_[4] = {nullptr, nullptr, nullptr, nullptr};

    // Partial ring selector visuals (climate-style)
    lv_obj_t *selector_arc = nullptr;
    lv_obj_t **selector_dots = nullptr;

    // Geometry and styling for the semi-circular bar and dots
    static const uint16_t width = 220;
    static const uint16_t top_center_angle = 270;

    static const uint8_t arc_width = 16;
    static const uint8_t dot_diameter_ = 6;

    const lv_color_t arc_bg_color = LV_COLOR_MAKE(0x28, 0x28, 0x28);
    const lv_color_t arc_indicator_color = LV_COLOR_MAKE(0xFF, 0xFF, 0xFF);
    const lv_color_t inactive_color = LV_COLOR_MAKE(0x47, 0x47, 0x47);
    const lv_color_t active_dot_color = LV_COLOR_MAKE(0xFF, 0xFF, 0xFF);

    // Helpers
    static uint8_t wrapIndex_(int32_t pos, uint8_t count);
    void updateLabelsLocked_(const Preset &p);
    void applyIndex_(uint8_t idx);

    // UI build/update helpers for selector ring
    void initSelectorArc_();
    void updateSelectorVisual_(uint8_t selected_index);
    void updatePresetImage_(uint8_t idx);
};