#pragma once
#include "apps.h"
#include "notify/os_config_notifier/os_config_notifier.h"

class CustomApps : public Apps
{
public:
    CustomApps(SemaphoreHandle_t mutex);
    void handleNavigationEvent(NavigationEvent event);
    void setOSConfigNotifier(OSConfigNotifier *os_config_notifier);

private:
    OSConfigNotifier *os_config_notifier;
};
