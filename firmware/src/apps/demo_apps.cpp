#include "demo_apps.h"

DemoApps::DemoApps(SemaphoreHandle_t mutex) : Apps(mutex)
{
    // Initialize demo apps directly
    clear();
    uint16_t app_position = 0;

    // Load demo apps
    loadApp(app_position++, "climate", "climate.climate", "Climate", "climate");
    loadApp(app_position++, "blinds", "blinds.blinds", "Blinds", "blinds");
    loadApp(app_position++, "stopwatch", "light.ceiling1", "Ceiling1", "stopwatch");
    loadApp(app_position++, "switch", "light.ceiling", "Ceiling", "ceiling_light_entity_id");
    loadApp(app_position++, "light_dimmer", "light.workbench", "Workbench", "workbench_light_entity_id");

    // Add settings app
    SettingsApp *settings_app = new SettingsApp(screen_mutex_);
    settings_app->setOSConfigNotifier(os_config_notifier_);
    add(app_position, settings_app);

    updateMenu();
    menu->setMenuName("Demo");
}

void DemoApps::handleNavigationEvent(NavigationEvent event)
{
    switch (event)
    {
    case NavigationEvent::LONG:
        if (active_id == MENU)
        {
#if !SERIAL_ONLY_MODE
            os_config_notifier->setOSMode(ONBOARDING);
            return;
#else
            // In serial-only mode, don't allow going back to onboarding
            // Long press in menu does nothing
            return;
#endif
        }
        break;
    }
    Apps::handleNavigationEvent(event);
}

void DemoApps::setOSConfigNotifier(OSConfigNotifier *os_config_notifier)
{
    this->os_config_notifier = os_config_notifier;
}
