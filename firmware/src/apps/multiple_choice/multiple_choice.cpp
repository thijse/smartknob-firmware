#include "multiple_choice.h"
#include "cJSON.h"
#include <cstring>
#include <logging.h>
#include <math.h>
#include <assert.h>

// Define multiple option lists (7 medical device lists)
const char *const MultipleChoiceApp::OPTION_LISTS_[MultipleChoiceApp::NUM_LISTS_][MultipleChoiceApp::MAX_OPTIONS_PER_LIST_] = {
    // List 0 - Move to access
    {"Move C-arm", "no", nullptr},

    // List 1 - Autofollow
    {"On", "Off", nullptr, nullptr},

    // List 2 - Unpark biplane
    {"yes", "no", nullptr, nullptr},

    // List 3 - Next step
    {"3DRA", "Park biplane", nullptr, nullptr},

    // List 4 - Confirm Isocenter
    {"Confirm", "Cancel", nullptr, nullptr},

    // List 5 - Update Mask
    {"Yes", "No", nullptr, nullptr},

    // List 6 - Launch iMed
    {"Launch", "Cancel", nullptr, nullptr}};

// List titles
const char *const MultipleChoiceApp::LIST_TITLES_[MultipleChoiceApp::NUM_LISTS_] = {
    "Move to access",
    "Autofollow",
    "Unpark biplane",
    "Next step",
    "Confirm Isocenter",
    "Update Mask",
    "Launch iMed"};

// Number of options in each list
const uint8_t MultipleChoiceApp::LIST_OPTION_COUNTS_[MultipleChoiceApp::NUM_LISTS_] = {
    2, // Move to access
    2, // Autofollow
    2, // Unpark biplane
    2, // Next step
    2, // Confirm Isocenter
    2, // Update Mask
    2  // Launch iMed
};

MultipleChoiceApp::MultipleChoiceApp(SemaphoreHandle_t mutex, char *app_id_, char *friendly_name_, char *entity_id_)
    : App(mutex)
{
    LOGI("MultipleChoiceApp: Constructor START for '%s'", friendly_name_);

    // Copy identifiers
    sprintf(app_id, "%s", app_id_);
    sprintf(friendly_name, "%s", friendly_name_);
    sprintf(entity_id, "%s", entity_id_);

    LOGI("MultipleChoiceApp: Identifiers copied");

    // Set icons (using settings icons as placeholder)
    LV_IMG_DECLARE(x80_settings);
    LV_IMG_DECLARE(x40_settings);
    big_icon = x80_settings;
    small_icon = x40_settings;

    LOGI("MultipleChoiceApp: Icons set");

    // Initialize state
    current_position = 0;
    last_position = -1; // Force initial update

    // Configure motor as bounded detent selector
    // Note: max_position will be updated in setSubIndex() based on actual list size
    motor_config = PB_SmartKnobConfig{
        .position = 0,
        .sub_position_unit = 0,
        .position_nonce = 0,
        .min_position = 0,
        .max_position = LIST_OPTION_COUNTS_[0] - 1, // Default to first list
        .position_width_radians = 12.0 * PI / 180,
        .detent_strength_unit = 1.5f,
        .endstop_strength_unit = 1.5f,
        .snap_point = 0.5,
        .detent_positions_count = 0,
        .detent_positions = {},
        .snap_point_bias = 0,
        .led_hue = 200, // Blue/cyan
    };
    strncpy(motor_config.id, app_id, sizeof(motor_config.id) - 1);

    LOGI("MultipleChoiceApp: Motor config set");

    // Build UI
    initScreen();

    LOGI("MultipleChoiceApp: Constructor COMPLETE for '%s'", friendly_name);
}

void MultipleChoiceApp::initScreen()
{
    SemaphoreGuard lock(mutex_);
    lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x0b, 0x5e, 0xd7), 0); // 0b5ed7

    LOGI("MultipleChoiceApp: Creating title label");
    // Title label (app name)
    title_label_ = lv_label_create(screen);
    lv_label_set_text(title_label_, friendly_name);
    lv_obj_align(title_label_, LV_ALIGN_TOP_MID, 0, 48);
    lv_obj_set_style_text_font(title_label_, &roboto_semi_bold_mono_16pt, 0);
    lv_obj_set_style_text_color(title_label_, lv_color_white(), 0);

    LOGI("MultipleChoiceApp: Creating option label");
    // Main option label (large centered text)
    option_label_ = lv_label_create(screen);
    lv_obj_center(option_label_);
    lv_obj_set_style_text_font(option_label_, &roboto_regular_mono_40pt, 0);
    lv_obj_set_style_text_color(option_label_, lv_color_white(), 0);
    lv_label_set_long_mode(option_label_, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(option_label_, 200);
    lv_obj_set_style_text_align(option_label_, LV_TEXT_ALIGN_CENTER, 0);

    LOGI("MultipleChoiceApp: Creating selector arc");
    // Partial ring selector (semi-circular bar + dots) at the top
    initSelectorArc_();

    LOGI("MultipleChoiceApp: Calling updateDisplay");
    // Show initial state
    updateDisplay();

    LOGI("MultipleChoiceApp: initScreen COMPLETE");
}

void MultipleChoiceApp::updateDisplay()
{
    // NO SEMAPHOREGUARD, since called with mutex held, this will cause deadlock!

    // Update title to show list title
    if (title_label_ != nullptr)
    {
        if (current_sub_index_ < NUM_LISTS_)
        {
            lv_label_set_text(title_label_, LIST_TITLES_[current_sub_index_]);
        }
        else
        {
            lv_label_set_text(title_label_, friendly_name);
        }
    }

    // Update main option text
    if (option_label_ != nullptr)
    {
        const char *opt_text = get_selected_text();
        lv_label_set_text(option_label_, opt_text);
    }

    // Update selector visual (dots)
    updateSelectorVisual_(current_position);
}

const char *MultipleChoiceApp::get_selected_text() const
{
    // Use current sub-index to select list
    const char *const *options = getCurrentOptions_();

    // Bounds check
    if (current_position < 0 || current_position >= getCurrentOptionsCount_())
    {
        LOGW("get_selected_text bounds error: pos=%d, count=%d",
             current_position, getCurrentOptionsCount_());
        return "ERROR";
    }

    return options[current_position];
}

EntityStateUpdate MultipleChoiceApp::updateStateFromKnob(PB_SmartKnobState state)
{
    EntityStateUpdate new_state;

    // Round position to nearest integer
    int new_position = (int)round(state.current_position);

    // Clamp to current list's valid range
    uint8_t max_pos = getCurrentOptionsCount_() - 1;
    if (new_position < 0)
        new_position = 0;
    if (new_position > max_pos)
        new_position = max_pos;

    // Detect change
    if (new_position != current_position)
    {
        current_position = new_position;

        // Update motor config position
        motor_config.position = current_position;
        motor_config.position_nonce = current_position;

        // Build JSON state with safe text handling
        const char *opt_text = get_selected_text();

        // Escape special JSON characters (quotes, backslashes)
        char json_text[64];
        size_t json_idx = 0;
        for (size_t i = 0; i < strlen(opt_text) && json_idx < sizeof(json_text) - 2; i++)
        {
            char c = opt_text[i];
            if (c == '"' || c == '\\')
            {
                if (json_idx < sizeof(json_text) - 2)
                {
                    json_text[json_idx++] = '\\';
                }
            }
            if (json_idx < sizeof(json_text) - 1)
            {
                json_text[json_idx++] = c;
            }
        }
        json_text[json_idx] = '\0';

        // Get list title (safely)
        const char *list_title = (current_sub_index_ < NUM_LISTS_)
                                     ? LIST_TITLES_[current_sub_index_]
                                     : "Unknown";

        // Populate state update with sub_index and list title included
        sprintf(new_state.app_id, "%s", app_id);
        sprintf(new_state.app_slug, "%s", APP_SLUG_MULTIPLE_CHOICE);
        sprintf(new_state.entity_id, "%s", entity_id);
        sprintf(new_state.state, "{\"list_title\": \"%s\", \"sub_index\": %d, \"selected_index\": %d, \"selected_text\": \"%s\"}",
                list_title, current_sub_index_, current_position, json_text);
        new_state.changed = true;

        LOGD("MultipleChoice state: list='%s', sub=%d, index=%d, text='%s'",
             list_title, current_sub_index_, current_position, opt_text);

        // Update display
        updateDisplay();
    }

    return new_state;
}

int8_t MultipleChoiceApp::navigationNext()
{
    // SHORT press: stay in app
    return DONT_NAVIGATE;
}

int8_t MultipleChoiceApp::navigationBack()
{
    // LONG press: return to menu
    return MENU;
}

void MultipleChoiceApp::handleNavigation(NavigationEvent event)
{
    // No additional behavior needed
    switch (event)
    {
    case NavigationEvent::LONG:
        // Handled by navigationBack()
        break;
    case NavigationEvent::SHORT:
        // Handled by navigationNext()
        break;
    default:
        break;
    }
}

// Build partial ring selector with evenly spaced dots (from angle_selector)
void MultipleChoiceApp::initSelectorArc_()
{
    // Assumes mutex_ is held by caller
    selector_arc = lv_arc_create(screen);

    // Geometry angle calculations
    uint8_t dot_amount = getCurrentOptionsCount_();

    float angle_step = (float)10.0f;
    float angle_range = angle_step * (dot_amount - 1);
    float half_angle_range = angle_range / 2.0f;
    uint16_t start_angle = -half_angle_range + top_center_angle;
    uint16_t end_angle = half_angle_range + top_center_angle;

    // Remove knob handle visuals
    lv_obj_remove_style(selector_arc, NULL, LV_PART_KNOB);
    lv_obj_set_size(selector_arc, width, width);

    // Align to center
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
        LOGE("MultipleChoiceApp: Failed to allocate selector dots");
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

        if (i == current_position)
            lv_obj_set_style_bg_color(circle, active_dot_color, LV_PART_MAIN);
        else
            lv_obj_set_style_bg_color(circle, inactive_color, LV_PART_MAIN);

        selector_dots[i] = circle;
    }
}

void MultipleChoiceApp::updateSelectorVisual_(uint8_t selected_index)
{
    // Update dot colors based on selection
    if (!selector_dots)
        return;

    uint8_t dot_amount = getCurrentOptionsCount_();
    for (uint8_t i = 0; i < dot_amount; i++)
    {
        lv_obj_set_style_bg_color(
            selector_dots[i],
            i == selected_index ? active_dot_color : inactive_color,
            LV_PART_MAIN);
    }
}

// Get the current option list based on sub-index
const char *const *MultipleChoiceApp::getCurrentOptions_() const
{
    return OPTION_LISTS_[current_sub_index_];
}

// Get the count of options in current list
uint8_t MultipleChoiceApp::getCurrentOptionsCount_() const
{
    if (current_sub_index_ >= NUM_LISTS_)
    {
        return 0;
    }
    return LIST_OPTION_COUNTS_[current_sub_index_];
}

// Set which option list to display (sub-index support)
void MultipleChoiceApp::setSubIndex(uint8_t sub_index)
{
    LOGI("MultipleChoice: setSubIndex(%d)", sub_index);

    // Clamp to valid range
    if (sub_index >= NUM_LISTS_)
    {
        LOGW("Invalid sub_index %d, clamping to %d", sub_index, NUM_LISTS_ - 1);
        sub_index = NUM_LISTS_ - 1;
    }

    current_sub_index_ = sub_index;
    current_position = 0; // Reset to first option
    last_position = -1;

    // Update motor config bounds
    motor_config.position = 0;
    motor_config.max_position = getCurrentOptionsCount_() - 1;

    // Refresh display
    {
        SemaphoreGuard lock(mutex_);
        updateDisplay();
    }

    // Push updated motor config
    triggerMotorConfigUpdate();
}
