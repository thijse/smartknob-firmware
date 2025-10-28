#pragma once

#include "../app.h"

// LogoApp: Just shows a simple logo

class LogoApp : public App
{
public:
    // Constructor: copies identifiers, sets icons, initializes motor_config, and builds UI.
    LogoApp(SemaphoreHandle_t mutex, char *app_id_, char *friendly_name_, char *entity_id_);

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

    lv_obj_t *img_preset_ = nullptr;
};