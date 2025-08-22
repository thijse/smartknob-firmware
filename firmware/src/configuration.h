#pragma once

#include <logging.h>
#include <FFat.h>
#include <PacketSerial.h>

#include "app_config.h"

#include "proto/proto_gen/smartknob.pb.h"

#include "EEPROM.h"
#include "./events/events.h"

static const char *CONFIG_PATH = "/config.pb";
static const char *SETTINGS_PATH = "/settings.pb";

// OS configurations
static const uint16_t OS_MODE_LENGTH = 1;
static const uint16_t OS_CONFIG_TOTAL_LENGTH = 50;

// OS config EEPROM positions
static const uint16_t OS_MODE_EEPROM_POS = 0;

// EEPROM size, verify when adding new fiels that size is still big enough
static const uint16_t EEPROM_SIZE = 512;

const uint32_t PERSISTENT_CONFIGURATION_VERSION = 2;
const uint32_t SETTINGS_VERSION = 1;

struct OSConfiguration
{
    OSMode mode = RUNNING;
};

static const SETTINGS_Settings default_settings =
    {
        .has_screen = true,
        .screen = {
            .dim = true,
            .max_bright = 65535,
            .min_bright = 19661,
            .timeout = 30000,
        },
        .has_led_ring = true,
        .led_ring = {
            .enabled = true,
            .dim = true,
            .max_bright = 65535,
            .min_bright = 19661,
            .color = 16754176,
            .has_beacon = true,
            .beacon = {
                .enabled = true,
                .brightness = 19661,
                .color = 16754176,
            },
        },
};

class Configuration
{
public:
    Configuration();
    ~Configuration();

    bool loadFromDisk();
    bool saveToDisk();
    bool resetToDefaults();
    PB_PersistentConfiguration get();

    bool loadSettingsFromDisk();
    bool saveSettingsToDisk();
    bool setSettings(SETTINGS_Settings &settings);
    // bool resetSettingsToDefaults();
    SETTINGS_Settings getSettings();

    bool setMotorCalibrationAndSave(PB_MotorCalibration &motor_calibration);

    bool saveOSConfiguration(OSConfiguration os_config);
    bool saveOSConfigurationInMemory(OSConfiguration os_config);
    bool loadOSConfiguration();
    bool saveFactoryStrainCalibration(float strain_scale);
    OSConfiguration *getOSConfiguration();
    const char *getKnobId();

    void setSharedEventsQueue(QueueHandle_t shared_event_queue);
    void publishEvent(Event event);

private:
    SemaphoreHandle_t mutex_;

    QueueHandle_t shared_events_queue;

    bool loaded_ = false;
    PB_PersistentConfiguration pb_buffer_ = {};

    bool settings_loaded_ = false;
    SETTINGS_Settings settings_buffer_ = default_settings;

    OSConfiguration os_config;

    uint8_t pb_stream_buffer_[PB_PersistentConfiguration_size];
    uint8_t settings_stream_buffer_[SETTINGS_Settings_size];

    std::string knob_id;
};
class FatGuard
{
public:
    FatGuard()
    {
        if (!FFat.begin(true))
        {
            LOGV(LOG_LEVEL_ERROR, "Failed to mount FFat");
            return;
        }
        LOGV(LOG_LEVEL_DEBUG, "Mounted FFat");
        mounted_ = true;
    }
    ~FatGuard()
    {
        if (mounted_)
        {
            FFat.end();
            LOGV(LOG_LEVEL_DEBUG, "Unmounted FFat");
        }
    }
    FatGuard(FatGuard const &) = delete;
    FatGuard &operator=(FatGuard const &) = delete;

    bool mounted_ = false;
};
