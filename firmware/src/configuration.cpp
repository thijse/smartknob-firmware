#include <FFat.h>

#include "pb_decode.h"
#include "pb_encode.h"

#include "proto/proto_gen/smartknob.pb.h"
#include "semaphore_guard.h"

#include "app_config.h"
#include "configuration.h"

Configuration::Configuration()
{
    mutex_ = xSemaphoreCreateMutex();
    assert(mutex_ != NULL);
}

Configuration::~Configuration()
{
    vSemaphoreDelete(mutex_);
}

const char *Configuration::getKnobId()
{
    return "SERIAL_KNOB";
}

bool Configuration::loadFromDisk()
{
    SemaphoreGuard lock(mutex_);
    FatGuard fatGuard;
    if (!fatGuard.mounted_)
    {
        return false;
    }

    File f = FFat.open(CONFIG_PATH);
    if (!f)
    {
        LOGV(LOG_LEVEL_WARNING, "Failed to read config file");
        return false;
    }

    size_t read = f.readBytes((char *)pb_stream_buffer_, sizeof(pb_stream_buffer_));
    f.close();

    pb_istream_t stream = pb_istream_from_buffer(pb_stream_buffer_, read);
    if (!pb_decode(&stream, PB_PersistentConfiguration_fields, &pb_buffer_))
    {
        char buf_[200];
        snprintf(buf_, sizeof(buf_), "Decoding config failed: %s", PB_GET_ERROR(&stream));
        LOGE(buf_);
        pb_buffer_ = {};
        return false;
    }

    if (pb_buffer_.version != PERSISTENT_CONFIGURATION_VERSION)
    {
        LOGE("Invalid config version. Expected %u, received %u", PERSISTENT_CONFIGURATION_VERSION, pb_buffer_.version);
        pb_buffer_ = {};
        return false;
    }
    loaded_ = true;

    LOGV(LOG_LEVEL_DEBUG, "Motor calibration: calib=%u, pole_pairs=%u, zero_offset=%.2f, cw=%u",
         pb_buffer_.motor.calibrated,
         pb_buffer_.motor.pole_pairs,
         pb_buffer_.motor.zero_electrical_offset,
         pb_buffer_.motor.direction_cw);

    return true;
}

bool Configuration::saveToDisk()
{
    {
        SemaphoreGuard lock(mutex_);

        pb_ostream_t stream = pb_ostream_from_buffer(pb_stream_buffer_, sizeof(pb_stream_buffer_));
        pb_buffer_.version = PERSISTENT_CONFIGURATION_VERSION;
        if (!pb_encode(&stream, PB_PersistentConfiguration_fields, &pb_buffer_))
        {
            char buf_[200];
            snprintf(buf_, sizeof(buf_), "Encoding failed: %s", PB_GET_ERROR(&stream));
            LOGE(buf_);
            return false;
        }

        FatGuard fatGuard;
        if (!fatGuard.mounted_)
        {
            return false;
        }

        File f = FFat.open(CONFIG_PATH, FILE_WRITE);
        if (!f)
        {
            LOGV(LOG_LEVEL_WARNING, "Failed to read config file");
            return false;
        }

        size_t written = f.write(pb_stream_buffer_, stream.bytes_written);
        f.close();

        LOGD("Saved config. Wrote %d bytes", written);

        if (written != stream.bytes_written)
        {
            LOGE("Failed to write all bytes to file");
            return false;
        }
    }

    if (shared_events_queue != NULL)
    {
        Event event;
        event.type = SK_CONFIGURATION_SAVED;
        publishEvent(event);
    }

    return true;
}

bool Configuration::loadSettingsFromDisk()
{
    SemaphoreGuard lock(mutex_);
    FatGuard fatGuard;
    if (!fatGuard.mounted_)
    {
        return false;
    }

    File f = FFat.open(SETTINGS_PATH);
    if (!f)
    {
        LOGV(LOG_LEVEL_WARNING, "Failed to read settings file");
        return false;
    }

    size_t read = f.readBytes((char *)settings_stream_buffer_, sizeof(settings_stream_buffer_));
    f.close();

    pb_istream_t stream = pb_istream_from_buffer(settings_stream_buffer_, read);
    if (!pb_decode(&stream, SETTINGS_Settings_fields, &settings_buffer_))
    {
        char buf_[200];
        snprintf(buf_, sizeof(buf_), "Decoding settings failed: %s", PB_GET_ERROR(&stream));
        LOGE(buf_);
        settings_buffer_ = {};
        return false;
    }

    if (settings_buffer_.protocol_version != SETTINGS_VERSION)
    {
        char buf_[200];
        snprintf(buf_, sizeof(buf_), "Invalid config version. Expected %u, received %u", SETTINGS_VERSION, settings_buffer_.protocol_version);
        LOGE(buf_);
        settings_buffer_ = {};
        return false;
    }
    settings_loaded_ = true;

    return true;
}

bool Configuration::saveSettingsToDisk()
{
    SemaphoreGuard lock(mutex_);

    pb_ostream_t stream = pb_ostream_from_buffer(settings_stream_buffer_, sizeof(settings_stream_buffer_));
    settings_buffer_.protocol_version = SETTINGS_VERSION;
    if (!pb_encode(&stream, SETTINGS_Settings_fields, &settings_buffer_))
    {
        char buf_[200];
        snprintf(buf_, sizeof(buf_), "Encoding failed: %s", PB_GET_ERROR(&stream));
        LOGE(buf_);
        return false;
    }

    FatGuard fatGuard;
    if (!fatGuard.mounted_)
    {
        return false;
    }

    File f = FFat.open(SETTINGS_PATH, FILE_WRITE);
    if (!f)
    {
        LOGV(LOG_LEVEL_WARNING, "Failed to read settings file");
        return false;
    }

    size_t written = f.write(settings_stream_buffer_, stream.bytes_written);
    f.close();

    LOGD("Saved settings. Wrote %d bytes", written);

    if (written != stream.bytes_written)
    {
        LOGE("Failed to write all bytes to settings file");
        return false;
    }

    return true;
}

bool Configuration::setSettings(SETTINGS_Settings &settings)
{
    {
        SemaphoreGuard lock(mutex_);
        settings_buffer_ = settings;

        if (shared_events_queue != NULL)
        {
            Event event;
            event.type = SK_SETTINGS_CHANGED;
            publishEvent(event);
        }
    }
    return saveSettingsToDisk();
}

SETTINGS_Settings Configuration::getSettings()
{
    if (!settings_loaded_)
    {
        if (!loadSettingsFromDisk())
        {
            SemaphoreGuard lock(mutex_);
            LOGD("Settings couldnt load from disk, loading default settings instead.");
            settings_buffer_ = default_settings;
            settings_loaded_ = true;
            return settings_buffer_;
        }
    }
    return settings_buffer_;
}

bool Configuration::resetToDefaults()
{
    EEPROM.put(OS_MODE_EEPROM_POS, OSMode::ONBOARDING);
    EEPROM.commit();
    return true;
}

bool Configuration::saveOSConfigurationInMemory(OSConfiguration os_config)
{

    this->os_config.mode = os_config.mode;
    return true;
}

bool Configuration::saveOSConfiguration(OSConfiguration os_config)
{
    {
        SemaphoreGuard lock(mutex_);
        EEPROM.put(OS_MODE_EEPROM_POS, os_config.mode);
    }

    return EEPROM.commit();
}

bool Configuration::loadOSConfiguration()
{
    // boot mode
    EEPROM.get(OS_MODE_EEPROM_POS, os_config.mode);

    if (os_config.mode > OSMode::DEMO)
    {
        os_config.mode = OSMode::ONBOARDING;
    }

    if (os_config.mode < 0)
    {
        os_config.mode = OSMode::ONBOARDING;
    }

    return true;
}

bool Configuration::saveFactoryStrainCalibration(float strain_scale)
{
    {
        SemaphoreGuard lock(mutex_);
        pb_buffer_.strain_scale = strain_scale;
    }
    return saveToDisk();
}

OSConfiguration *Configuration::getOSConfiguration()
{
    // Force demo mode when in serial-only mode
    os_config.mode = OSMode::DEMO;
    return &os_config;
}

PB_PersistentConfiguration Configuration::get()
{
    SemaphoreGuard lock(mutex_);
    if (!loaded_)
    {
        return PB_PersistentConfiguration();
    }
    return pb_buffer_;
}

bool Configuration::setMotorCalibrationAndSave(PB_MotorCalibration &motor_calibration)
{
    {
        SemaphoreGuard lock(mutex_);
        pb_buffer_.motor = motor_calibration;
        pb_buffer_.has_motor = true;
    }
    return saveToDisk();
}

void Configuration::setSharedEventsQueue(QueueHandle_t shared_events_queue)
{
    this->shared_events_queue = shared_events_queue;
}

void Configuration::publishEvent(Event event)
{
    event.sent_at = millis();
    xQueueSendToBack(shared_events_queue, &event, 0);
}
