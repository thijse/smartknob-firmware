#include "angle_selector.h"
#include "cJSON.h"
#include <cstring>
#include <logging.h>
#include <math.h>
#include <assert.h>

// External images for neuro presets (168x168 RGB565)
LV_IMG_DECLARE(neuro_preset_angle_1_p);
LV_IMG_DECLARE(neuro_preset_angle_2_p);
LV_IMG_DECLARE(neuro_preset_angle_3_p);
LV_IMG_DECLARE(neuro_preset_angle_4_p);

// Preset definitions (v1)
const AngleSelectorApp::Preset AngleSelectorApp::PRESETS_[] = {
    {"RAO 85°", "Cran 87°", -85, 87},
    {"RAO 192°", "Cran 12°", -192, 12},
    {"LAO 84°", "Cran 78°", 84, 78},
    {"LAO 88°", "Cran 86°", 88, 86},
    // {"LAO 25°", "Cran 15°", 25, 15},
    // {"RAO 85°", "Caud 10°", -30, -10},
    // {"AP 0°", "Cran 0°", 0, 0},
    // {"LAT 90°", "Cran 0°", 90, 0},
};

const uint8_t AngleSelectorApp::PRESET_COUNT_ = sizeof(AngleSelectorApp::PRESETS_) / sizeof(AngleSelectorApp::Preset);

// Helper: wrap index for unbounded positions
uint8_t AngleSelectorApp::wrapIndex_(int32_t pos, uint8_t count)
{
    if (count == 0)
        return 0;
    int32_t m = pos % count;
    if (m < 0)
        m += count;
    return static_cast<uint8_t>(m);
}

AngleSelectorApp::AngleSelectorApp(SemaphoreHandle_t mutex, char *app_id_, char *friendly_name_, char *entity_id_)
    : App(mutex)
{
    // Identifiers
    sprintf(app_id, "%s", app_id_);
    sprintf(friendly_name, "%s", friendly_name_);
    sprintf(entity_id, "%s", entity_id_);

    // Icons (neutral selector icon)
    LV_IMG_DECLARE(x80_timer);
    LV_IMG_DECLARE(x40_timer);
    big_icon = x80_timer;
    small_icon = x40_timer;

    // Motor config: coarse selector detents, wrap enabled (max_position = -1)
    motor_config = PB_SmartKnobConfig{
        .position = 0,
        .sub_position_unit = 0,
        .position_nonce = 0,
        .min_position = 0,
        .max_position = -1, // unbounded / wrap
        .position_width_radians = 25 * PI / 180,
        .detent_strength_unit = 1,
        .endstop_strength_unit = 1,
        .snap_point = 1.1,
        .detent_positions_count = 0,
        .detent_positions = {},
        .snap_point_bias = 0,
        .led_hue = 27,
    };
    // Route updates correctly into this app
    strncpy(motor_config.id, app_id, sizeof(motor_config.id) - 1);

    // Build UI and set initial labels
    initScreen();
    applyIndex_(0);

    // Push initial motor config to the motor task
    // Never do this, it will crash the app: triggerMotorConfigUpdate();
}

void AngleSelectorApp::initScreen()
{
    SemaphoreGuard lock(mutex_);
    // Black background (consistent with App ctor)
    lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);

    // Preset image widget (shows 168x168 preset illustration) - create first to render under others
    img_preset_ = lv_img_create(screen);
    lv_obj_align(img_preset_, LV_ALIGN_CENTER, 0, 0); // place below the text lines
    updatePresetImage_(current_index_);

    // Partial ring selector (semi-circular bar + dots) at the top
    initSelectorArc_();

    // Outline labels to simulate text stroke (created before white labels to render underneath)
    {
        static const int8_t dx[4] = {-2, 2, 0, 0};
        static const int8_t dy[4] = {0, 0, -2, 2};

        for (int i = 0; i < 4; ++i)
        {
            // Primary outlines around center with y offset -6
            label_primary_outline_[i] = lv_label_create(screen);
            lv_obj_set_style_text_font(label_primary_outline_[i], &roboto_light_mono_24pt, 0);
            lv_obj_set_style_text_color(label_primary_outline_[i], LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);
            lv_label_set_text(label_primary_outline_[i], "");
            lv_obj_align(label_primary_outline_[i], LV_ALIGN_CENTER, dx[i], -6 + dy[i]);

            // Secondary outlines around center with y offset +18
            label_secondary_outline_[i] = lv_label_create(screen);
            lv_obj_set_style_text_font(label_secondary_outline_[i], &roboto_light_mono_24pt, 0);
            lv_obj_set_style_text_color(label_secondary_outline_[i], LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);
            lv_label_set_text(label_secondary_outline_[i], "");
            lv_obj_align(label_secondary_outline_[i], LV_ALIGN_CENTER, dx[i], 18 + dy[i]);
        }
    }

    // Primary line (e.g., "LAO 25°")
    label_primary_ = lv_label_create(screen);
    lv_obj_set_style_text_font(label_primary_, &roboto_light_mono_24pt, 0);
    lv_obj_set_style_text_color(label_primary_, LV_COLOR_MAKE(0xFF, 0xFF, 0xFF), 0);
    lv_label_set_text(label_primary_, "");
    lv_obj_align(label_primary_, LV_ALIGN_CENTER, 0, -6);

    // Secondary line (e.g., "Cranial 15°")
    label_secondary_ = lv_label_create(screen);
    lv_obj_set_style_text_font(label_secondary_, &roboto_light_mono_24pt, 0);
    lv_obj_set_style_text_color(label_secondary_, LV_COLOR_MAKE(0xFF, 0xFF, 0xFF), 0);
    lv_label_set_text(label_secondary_, "");
    lv_obj_align(label_secondary_, LV_ALIGN_CENTER, 0, 18);
}

void AngleSelectorApp::updateLabelsLocked_(const Preset &p)
{
    // Assumes mutex_ is held by caller
    // Update white labels
    lv_label_set_text(label_primary_, p.primary);
    lv_label_set_text(label_secondary_, p.secondary);

    // Update black outline labels (up, down, left, right)
    for (int i = 0; i < 4; ++i)
    {
        if (label_primary_outline_[i])
            lv_label_set_text(label_primary_outline_[i], p.primary);
        if (label_secondary_outline_[i])
            lv_label_set_text(label_secondary_outline_[i], p.secondary);
    }
}

void AngleSelectorApp::applyIndex_(uint8_t idx)
{
    current_index_ = idx;
    {
        SemaphoreGuard lock(mutex_);
        updateLabelsLocked_(PRESETS_[idx]);
        updateSelectorVisual_(idx);
        updatePresetImage_(idx);
    }
}

EntityStateUpdate AngleSelectorApp::updateStateFromKnob(PB_SmartKnobState state)
{
    EntityStateUpdate new_state;

    // Track position for consistency; immediate emit on index change
    int32_t pos = state.current_position;
    // Use wrap for unbounded rotation
    uint8_t idx = wrapIndex_(pos, PRESET_COUNT_);

    // Keep motor_config in sync (optional, consistent with other apps)
    motor_config.position = pos;
    motor_config.sub_position_unit = state.sub_position_unit;
    motor_config.position_nonce = state.current_position; // align with position steps

    if (idx != last_index_)
    {
        // Update labels
        {
            SemaphoreGuard lock(mutex_);
            updatePresetImage_(idx);
            updateLabelsLocked_(PRESETS_[idx]);
            updateSelectorVisual_(idx);
        }

        // Build JSON state
        cJSON *json = cJSON_CreateObject();
        char preset_name[64];
        snprintf(preset_name, sizeof(preset_name) - 1, "%s / %s", PRESETS_[idx].primary, PRESETS_[idx].secondary);
        cJSON_AddStringToObject(json, "preset", preset_name);
        cJSON_AddNumberToObject(json, "lao_deg", PRESETS_[idx].lao_deg);
        cJSON_AddNumberToObject(json, "cranial_deg", PRESETS_[idx].cranial_deg);
        cJSON_AddNumberToObject(json, "index", idx);

        char *json_str = cJSON_PrintUnformatted(json);
        snprintf(new_state.state, sizeof(new_state.state) - 1, "%s", json_str ? json_str : "{}");
        if (json_str)
        {
            cJSON_free(json_str);
        }
        cJSON_Delete(json);

        // Fill identifiers
        snprintf(new_state.app_id, sizeof(new_state.app_id) - 1, "%s", app_id);
        snprintf(new_state.entity_id, sizeof(new_state.entity_id) - 1, "%s", entity_id);
        snprintf(new_state.app_slug, sizeof(new_state.app_slug) - 1, "%s", APP_SLUG_ANGLE_SELECTOR);

        new_state.changed = true;

        // Track index change
        last_index_ = idx;
        current_index_ = idx;
    }

    return new_state;
}

int8_t AngleSelectorApp::navigationNext()
{
    // SHORT press: no-op; do not navigate away
    return DONT_NAVIGATE;
}

int8_t AngleSelectorApp::navigationBack()
{
    // LONG press: return to Menu
    return MENU;
}

void AngleSelectorApp::handleNavigation(NavigationEvent event)
{
    // No additional behavior needed for v1; Apps handles setActive(MENU) when navigationBack()==MENU
    switch (event)
    {
    case NavigationEvent::LONG:
        // explicit no-op (Apps will read navigationBack())
        break;
    case NavigationEvent::SHORT:
    default:
        break;
    }
}

// Build partial ring selector with climate-style semi-circle and evenly spaced dots
void AngleSelectorApp::initSelectorArc_()
{
    // Assumes mutex_ is held by caller
    selector_arc = lv_arc_create(screen);

    // Geometry angle calculations
    uint8_t dot_amount = PRESET_COUNT_;

    float angle_step = (float)10.0f;
    float angle_range = angle_step * (dot_amount - 1);
    float half_angle_range = angle_range / 2.0f;
    uint16_t start_angle = -half_angle_range + top_center_angle;
    uint16_t end_angle = half_angle_range + top_center_angle;

    // Remove knob handle visuals
    lv_obj_remove_style(selector_arc, NULL, LV_PART_KNOB);
    lv_obj_set_size(selector_arc, width, width);

    // Align to top-middle to place the semi-circle at the top of the screen
    lv_obj_center(selector_arc);

    // Style
    lv_obj_set_style_arc_width(selector_arc, arc_width, LV_PART_MAIN);
    lv_obj_set_style_arc_width(selector_arc, 0, LV_PART_INDICATOR);
    lv_obj_set_style_arc_opa(selector_arc, LV_OPA_TRANSP, LV_PART_INDICATOR);
    lv_obj_set_style_arc_color(selector_arc, arc_bg_color, LV_PART_MAIN);

    // Geometry
    lv_arc_set_rotation(selector_arc, start_angle); // LVGL rotation is clockwise from 3 o'clock
    lv_arc_set_bg_angles(selector_arc, 0, angle_range);

    // Dots

    selector_dots = (lv_obj_t **)malloc(dot_amount * sizeof(lv_obj_t *));
    if (!selector_dots)
    {
        return;
    }

    lv_coord_t screen_width = lv_obj_get_width(screen);
    lv_coord_t screen_height = lv_obj_get_height(screen);
    lv_coord_t center_x = screen_width / 2;
    lv_coord_t center_y = screen_height / 2;

    float radius = (width - arc_width) / 2.0f; // Center dots within the arc thickness

    for (uint8_t i = 0; i < dot_amount; i++)
    {

        float angle = (start_angle + i * angle_step) * M_PI / 180.0;

        int x = center_x + radius * cos(angle);
        int y = center_y + radius * sin(angle);

        uint8_t diameter = 8;
        lv_obj_t *circle = lvDrawCircle(diameter, screen);
        lv_obj_set_pos(circle, x - diameter / 2, y - diameter / 2); // Adjust position to account for the circle's diameter

        if (i == current_index_)
            lv_obj_set_style_bg_color(circle, active_dot_color, LV_PART_MAIN);
        else
            lv_obj_set_style_bg_color(circle, inactive_color, LV_PART_MAIN);

        selector_dots[i] = circle;
    }
}
void AngleSelectorApp::updateSelectorVisual_(uint8_t selected_index)
{
    // Assumes mutex_ is held by caller
    if (!selector_dots)
        return;

    uint8_t dot_amount = PRESET_COUNT_;
    for (uint8_t i = 0; i < dot_amount; i++)
    {
        lv_obj_set_style_bg_color(
            selector_dots[i],
            i == selected_index ? active_dot_color : inactive_color,
            LV_PART_MAIN);
    }
}

void AngleSelectorApp::updatePresetImage_(uint8_t idx)
{
    // Assumes mutex_ is held by caller when called from UI update paths
    if (!img_preset_)
        return;

    // Map 0..PRESET_COUNT_-1 to the compiled-in neuro preset images
    switch (idx % PRESET_COUNT_)
    {
    case 0:
        lv_img_set_src(img_preset_, &neuro_preset_angle_1_p);
        break;
    case 1:
        lv_img_set_src(img_preset_, &neuro_preset_angle_2_p);
        break;
    case 2:
        lv_img_set_src(img_preset_, &neuro_preset_angle_3_p);
        break;
    default:
        lv_img_set_src(img_preset_, &neuro_preset_angle_4_p);
        break;
    }
}