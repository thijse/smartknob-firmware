#include "onboarding_flow.h"
#include <semaphore_guard.h>

OnboardingFlow::OnboardingFlow(SemaphoreHandle_t mutex) : mutex_(mutex)
{
    root_level_motor_config = PB_SmartKnobConfig{
        0,
        0,
        0,
        0,
        ONBOARDING_FLOW_PAGE_COUNT - 1,
        35 * PI / 180,
        2,
        1,
        0.55,
        "ONBOARDING",
        0,
        {},
        0,
        20,
    };

    blocked_motor_config = PB_SmartKnobConfig{
        0,
        0,
        0,
        0,
        0,
        55 * PI / 180,
        0.01,
        0.6,
        1.1,
        "ONBOARDING",
        0,
        {},
        0,
        90,
    };

    page_mgr = new OnboardingPageManager(main_screen, mutex);

#ifdef RELEASE_VERSION
    sprintf(firmware_version, "%s", RELEASE_VERSION);
#else
    sprintf(firmware_version, "%s", "DEV");
#endif
}

OnboardingFlowPages getPageEnum(uint8_t screen)
{
    if (screen >= 0 && screen <= ONBOARDING_FLOW_PAGE_COUNT - 1)
    {
        return static_cast<OnboardingFlowPages>(screen);
    }
    return WELCOME_PAGE; // TODO handle error here instead of returning WELCOME_PAGE
}

void OnboardingFlow::render()
{
    root_level_motor_config.position = current_position;
    motor_notifier->requestUpdate(root_level_motor_config); // Prevents state after moving back from submenus to be reset to page 0, i.e. moves user to correct page on the onboarding menu.

    active_sub_menu = NONE;
    page_mgr->show(getPageEnum(current_position));

    {
        SemaphoreGuard lock(mutex_);
        lv_scr_load(main_screen);
    }
}

void OnboardingFlow::handleNavigationEvent(NavigationEvent event)
{
    if (active_sub_menu == NONE)
    {
        switch (event)
        {
        case NavigationEvent::SHORT:
            switch (getPageEnum(current_position))
            {
            case WELCOME_PAGE: // No submenus available for welcome page nor about page.
            case ABOUT_PAGE:
                break;
            case DEMO_PAGE:
                os_config_notifier->setOSMode(OSMode::RUNNING);
                break;
            default:
                LOGE("Unhandled navigation event");
                break;
            }
        }
    }
}

EntityStateUpdate OnboardingFlow::update(AppState state)
{
    return updateStateFromKnob(state.motor_state);
}

EntityStateUpdate OnboardingFlow::updateStateFromKnob(PB_SmartKnobState state)
{
    if (current_position != state.current_position)
    {
        current_position = state.current_position;
        page_mgr->show(getPageEnum(current_position));
    }

    EntityStateUpdate new_state;
    return new_state;
}

void OnboardingFlow::setMotorNotifier(MotorNotifier *motor_notifier)
{
    this->motor_notifier = motor_notifier;
}

void OnboardingFlow::triggerMotorConfigUpdate()
{
    if (this->motor_notifier != nullptr)
    {
        motor_notifier->requestUpdate(root_level_motor_config);
    }
    else
    {
        LOGW("Motor_notifier is not set");
    }
}

void OnboardingFlow::setOSConfigNotifier(OSConfigNotifier *os_config_notifier)
{
    this->os_config_notifier = os_config_notifier;
}
