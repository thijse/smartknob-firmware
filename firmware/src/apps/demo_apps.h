#pragma once
#include "apps.h"
#include "notify/os_config_notifier/os_config_notifier.h"

class DemoApps : public Apps
{
public:
    DemoApps(SemaphoreHandle_t mutex);
    void handleNavigationEvent(NavigationEvent event);
    void setOSConfigNotifier(OSConfigNotifier *os_config_notifier);

private:
    OSConfigNotifier *os_config_notifier;
};
