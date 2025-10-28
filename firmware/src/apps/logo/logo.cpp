#include "logo.h"
#include "cJSON.h"
#include <cstring>
#include <logging.h>
#include <math.h>
#include <assert.h>

// External images for logo
LV_IMG_DECLARE(logo_image);
// TODO: Create dedicated logo icons, using settings icons as placeholder
LV_IMG_DECLARE(x80_settings);
LV_IMG_DECLARE(x40_settings);

LogoApp::LogoApp(SemaphoreHandle_t mutex, char *app_id_, char *friendly_name_, char *entity_id_)
    : App(mutex)
{
    // Identifiers
    sprintf(app_id, "%s", app_id_);
    sprintf(friendly_name, "%s", friendly_name_);
    sprintf(entity_id, "%s", entity_id_);

    // Icons - using settings icon as placeholder (TODO: create logo-specific icons)
    big_icon = x80_settings;
    small_icon = x40_settings;

    // Motor config for locked/static display (no rotation allowed)
    motor_config = PB_SmartKnobConfig{
        .position = 0,
        .sub_position_unit = 0,
        .position_nonce = 0,
        .min_position = 0,
        .max_position = 0, // Locked position
        .position_width_radians = 25 * PI / 180,
        .detent_strength_unit = 1,
        .endstop_strength_unit = 1,
        .snap_point = 1.1,
        .detent_positions_count = 0,
        .detent_positions = {},
        .snap_point_bias = 0,
        .led_hue = 200, // Blue/cyan color for logo
    };
    strncpy(motor_config.id, app_id, sizeof(motor_config.id) - 1);

    // Build UI and set initial labels
    initScreen();
}

void LogoApp::initScreen()
{
    SemaphoreGuard lock(mutex_);
    // Black background (consistent with App ctor)
    lv_obj_set_style_bg_color(screen, LV_COLOR_MAKE(0x00, 0x00, 0x00), 0);

    // Preset image widget (shows 168x168 preset illustration) - create first to render under others
    img_preset_ = lv_img_create(screen);
    lv_obj_align(img_preset_, LV_ALIGN_CENTER, 0, 0); // place below the text lines
    lv_img_set_src(img_preset_, &logo_image);
}

EntityStateUpdate LogoApp::updateStateFromKnob(PB_SmartKnobState state)
{
    EntityStateUpdate new_state;

    return new_state;
}

int8_t LogoApp::navigationNext()
{
    // SHORT press: no-op; do not navigate away
    return DONT_NAVIGATE;
}

int8_t LogoApp::navigationBack()
{
    // LONG press: return to Menu
    return MENU;
}

void LogoApp::handleNavigation(NavigationEvent event)
{
    // No additional behavior needed for v1; Apps handles setActive(MENU) when navigationBack()==MENU
    switch (event)
    {
    case NavigationEvent::LONG:
        break;
    case NavigationEvent::SHORT:
    default:
        break;
    }
}
