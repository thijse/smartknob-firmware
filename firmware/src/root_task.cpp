#include "root_task.h"
#include "app_config.h"
#include "semaphore_guard.h"
#include "util.h"

// TODO: check if all ONBOARDING and HAS case switches can be remove

QueueHandle_t trigger_motor_calibration_;
uint8_t trigger_motor_calibration_event_;

// this is global function because we don't have better design yet
void delete_me_TriggerMotorCalibration()
{
    uint8_t trigger = 1;
    xQueueSendToBack(trigger_motor_calibration_, &trigger, 0);
}

RootTask::RootTask(
    const uint8_t task_core,
    Configuration *configuration,
    MotorTask &motor_task,
    DisplayTask *display_task,
    LedRingTask *led_ring_task,
    SensorsTask *sensors_task,
    ResetTask *reset_task, FreeRTOSAdapter *free_rtos_adapter, SerialProtocolPlaintext *serial_protocol_plaintext, SerialProtocolProtobuf *serial_protocol_protobuf) : Task("RootTask", 1024 * 24, ESP_TASK_MAIN_PRIO, task_core),
                                                                                                                                                                       //  stream_(),
                                                                                                                                                                       configuration_(configuration),
                                                                                                                                                                       motor_task_(motor_task),
                                                                                                                                                                       display_task_(display_task),
                                                                                                                                                                       led_ring_task_(led_ring_task),
                                                                                                                                                                       sensors_task_(sensors_task),
                                                                                                                                                                       reset_task_(reset_task),
                                                                                                                                                                       free_rtos_adapter_(free_rtos_adapter),
                                                                                                                                                                       serial_protocol_plaintext_(serial_protocol_plaintext),
                                                                                                                                                                       serial_protocol_protobuf_(serial_protocol_protobuf),
                                                                                                                                                                       auto_broadcast_enabled_(false),
                                                                                                                                                                       position_change_threshold_(0.1f),
                                                                                                                                                                       max_broadcast_interval_(100),
                                                                                                                                                                       last_broadcast_time_(0),
                                                                                                                                                                       component_manager_(nullptr),
                                                                                                                                                                       component_mode_(false)
{
#if SK_DISPLAY
    assert(display_task != nullptr);
#endif

    trigger_motor_calibration_ = xQueueCreate(1, sizeof(uint8_t *));
    assert(trigger_motor_calibration_ != NULL);

    app_sync_queue_ = xQueueCreate(2, sizeof(cJSON *));
    assert(app_sync_queue_ != NULL);

    knob_state_queue_ = xQueueCreate(1, sizeof(PB_SmartKnobState));
    assert(knob_state_queue_ != NULL);

    sensors_status_queue_ = xQueueCreate(100, sizeof(SensorsState));
    assert(sensors_status_queue_ != NULL);

    mutex_ = xSemaphoreCreateMutex();
    assert(mutex_ != NULL);
}

RootTask::~RootTask()
{
    // Clean up component manager
    if (component_manager_)
    {
        delete component_manager_;
        component_manager_ = nullptr;
    }

    vSemaphoreDelete(mutex_);
}

void RootTask::run()
{
    uint8_t task_started_at = millis();

    // Build version and timestamp for debugging
    LOGI("=== SMARTKNOB FIRMWARE STARTUP ===");
    LOGI("Build date: %s %s", __DATE__, __TIME__);
    LOGI("Component system enabled: ComponentManager integration");
    LOGI("RootTask: Starting run() method at %d ms", task_started_at);

    // Verify ComponentManager was created successfully now that logging is available
    if (component_manager_ == nullptr)
    {
        LOGE("RootTask: ComponentManager creation failed!");
    }
    else
    {
        LOGI("RootTask: ComponentManager created successfully");
    }

    motor_task_.addListener(knob_state_queue_);

    serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_settings_tag, [this](PB_ToSmartknob to_smartknob)
                                                   { configuration_->setSettings(to_smartknob.payload.settings); });

    serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_strain_calibration_tag, [this](PB_ToSmartknob to_smartknob)
                                                   { sensors_task_->factoryStrainCalibrationCallback(to_smartknob.payload.strain_calibration.calibration_weight); });

    serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_request_state_tag, [this](PB_ToSmartknob to_smartknob)
                                                   { sendCurrentKnobState(); });

    // Component system protocol handler
    serial_protocol_protobuf_->registerTagCallback(PB_ToSmartknob_app_component_tag, [this](PB_ToSmartknob to_smartknob)
                                                   {
                                                       LOGI("RootTask: Received app_component message");
                                                       bool success = component_manager_->createComponent(to_smartknob.payload.app_component);
                                                       if (success)
                                                       {
                                                           // Switch to component mode and activate the new component
                                                           component_mode_ = true;
                                                           if (component_manager_->setActiveComponent(to_smartknob.payload.app_component.component_id)) {
                                                               // setActiveComponent now calls render() internally (like Apps::setActive)
                                                               component_manager_->triggerMotorConfigUpdate();  // Like DisplayTask::enableDemo
                                                           }
                                                           LOGI("RootTask: Switched to component mode, activated '%s'", to_smartknob.payload.app_component.component_id);
                                                       }
                                                       else
                                                       {
                                                           LOGE("RootTask: Failed to create component '%s'", to_smartknob.payload.app_component.component_id);
                                                       }
                                                       // Send acknowledgment (TODO: implement proper ack sending)
                                                   });

    serial_protocol_protobuf_->registerCommandCallback(PB_SmartKnobCommand_MOTOR_CALIBRATE, [this]()
                                                       { motor_task_.runCalibration(); });

    auto callbackGetKnobInfo = [this]()
    {
        LOGI("=== GET_KNOB_INFO CALLBACK START ===");
        PB_Knob knob = {};

        LOGI("Setting MAC and IP addresses...");
        strlcpy(knob.mac_address, "00:00:00:00:00:00", sizeof(knob.mac_address));
        strlcpy(knob.ip_address, "0.0.0.0", sizeof(knob.ip_address));
        LOGI("Serial-only mode: MAC=%s, IP=%s", knob.mac_address, knob.ip_address);

        LOGI("Getting configuration...");
        const PB_PersistentConfiguration config = configuration_->get();
        LOGI("Configuration retrieved successfully");

        if (config.version != 0)
        {
            LOGI("Setting persistent config (version %u)", config.version);
            knob.has_persistent_config = true;
            knob.persistent_config = config;
        }
        else
        {
            LOGI("No persistent config available");
            knob.has_persistent_config = false;
        }

        LOGI("Getting settings...");
        knob.has_settings = true;
        knob.settings = configuration_->getSettings();
        LOGI("Settings retrieved successfully");

        LOGI("Calling sendKnobInfo...");
        serial_protocol_protobuf_->sendKnobInfo(knob);
        LOGI("=== GET_KNOB_INFO CALLBACK END ===");
    };
    serial_protocol_protobuf_->registerCommandCallback(PB_SmartKnobCommand_GET_KNOB_INFO, callbackGetKnobInfo);

    serial_protocol_plaintext_->registerKeyHandler('c', [this]()
                                                   { motor_task_.runCalibration(); });
    serial_protocol_plaintext_->registerKeyHandler('w', [this]()
                                                   { sensors_task_->weightMeasurementCallback(); });
    serial_protocol_plaintext_->registerKeyHandler('y', [this]()
                                                   { sensors_task_->factoryStrainCalibrationCallback((float)CALIBRATION_WEIGHT); });
    auto callbackSetProtocol = [this]()
    {
        LOGI("=== DEBUG: SWITCHING TO PROTOBUF MODE ===");
        free_rtos_adapter_->setProtocol(serial_protocol_protobuf_);
    };
    serial_protocol_plaintext_->registerKeyHandler('q', callbackSetProtocol);
    serial_protocol_plaintext_->registerKeyHandler(0, callbackSetProtocol); // Switches to protobuf protocol on protobuf message from configurator

    MotorNotifier motor_notifier = MotorNotifier([this](PB_SmartKnobConfig config)
                                                 { applyConfig(config, false); });

    os_config_notifier_.setCallback([this](OSMode os_mode)
                                    {
        this->configuration_->loadOSConfiguration();
        OSConfiguration *os_config = this->configuration_->getOSConfiguration();

        os_config->mode = os_mode;
        LOGI("OS mode set to %d", os_config->mode);

        this->configuration_->saveOSConfigurationInMemory(*os_config);

        // With simplified OSMode, always enable demo
        display_task_->enableDemo(); });

    // waiting for config to be loaded
    bool is_configuration_loaded = false;
    while (!is_configuration_loaded)
    {
        LOGV(LOG_LEVEL_DEBUG, "Waiting for configuration");
        xSemaphoreTake(mutex_, portMAX_DELAY);
        is_configuration_loaded = configuration_ != nullptr;
        xSemaphoreGive(mutex_);
        vTaskDelay(pdMS_TO_TICKS(50));
    }

    display_task_->getErrorHandlingFlow()->setMotorNotifier(&motor_notifier);
    display_task_->getApps()->setMotorNotifier(&motor_notifier);
    display_task_->getApps()->setOSConfigNotifier(&os_config_notifier_);

    // Initialize component manager with App-based architecture
    component_manager_ = new ComponentManager(mutex_);
    component_manager_->setMotorNotifier(&motor_notifier); 
    
    // TODO: move playhaptic to notifier? or other interface to just pass "possible" motor commands not entire object/class.
    reset_task_->setMotorTask(&motor_task_);

    configuration_->loadOSConfiguration();

    // In serial-only mode, always go directly to demo mode
    os_config_notifier_.setOSMode(OSMode::RUNNING);
    display_task_->enableDemo();

    // Enable auto-broadcasting with default settings
    enableAutoBroadcast(true);
    setMaxBroadcastRate(10);
    setPositionChangeThreshold(0.1f);

    motor_notifier.loopTick();

    EntityStateUpdate entity_state_update_to_send;

    // Value between [0, 65536] for brightness when not engaging with knob
    bool isCurrentSubPositionSet = false;
    float currentSubPosition;
    Event wifi_event;

    AppState app_state = {};

    // Debug counter for periodic logging
    uint32_t debug_counter = 0;

    while (1)
    {
        debug_counter++;

        // Periodic debug message every 10 seconds (assuming 10ms loop delay)
        if (debug_counter % 1000 == 0)
        {
            // LOGI("=== DEBUG: Main loop running, count=%u ===", debug_counter);
        }
        if (xQueueReceive(trigger_motor_calibration_, &trigger_motor_calibration_event_, 0) == pdTRUE)
        {
            app_state.screen_state.awake_until = millis() + app_state.screen_state.awake_until;
            app_state.screen_state.has_been_engaged = true;
            motor_task_.runCalibration();
        }
        if (xQueueReceive(sensors_status_queue_, &latest_sensors_state_, 0) == pdTRUE)
        {
            app_state.proximiti_state.RangeMilliMeter = latest_sensors_state_.proximity.RangeMilliMeter;
            app_state.proximiti_state.RangeStatus = latest_sensors_state_.proximity.RangeStatus;

            // wake up the screen
            // RangeStatus is usually 0,2,4. We want to caputure the level of confidence 0 and 2.
            // Add motor encoder detection? or disable motor if not "enaged detected presence"
            if (app_state.proximiti_state.RangeStatus < 3 && app_state.proximiti_state.RangeMilliMeter < 200)
            {
                app_state.screen_state.has_been_engaged = true;
                if (app_state.screen_state.awake_until < millis() + KNOB_ENGAGED_TIMEOUT_NONE_PHYSICAL) // If half of the time of the last interaction has passed, reset allow for engage to be detected again.
                {
                    app_state.screen_state.awake_until = millis() + KNOB_ENGAGED_TIMEOUT_NONE_PHYSICAL;
                }
            }
        }

        // Network connectivity removed for serial-only mode

        if (xQueueReceive(app_sync_queue_, &apps_, 0) == pdTRUE)
        {
            // Does nothing currently. MQTT functionality removed for serial-only mode
        }

        if (xQueueReceive(knob_state_queue_, &latest_state_, 0) == pdTRUE)
        {

            // The following is a smoothing filter (rounding) on the sub position unit (to avoid flakiness).
            float roundedNewPosition = round(latest_state_.sub_position_unit * 3) / 3.0;
            // This if is used to understand if we have touched the knob since last state.
            if (isCurrentSubPositionSet)
            {
                if (currentSubPosition != roundedNewPosition)
                {
                    // We set a flag on the object Screen State.
                    //  Todo: this property should be at app state and not screen state
                    app_state.screen_state.has_been_engaged = true;
                    if (app_state.screen_state.awake_until < millis() + max((KNOB_ENGAGED_TIMEOUT_PHYSICAL / 2), settings_.screen.timeout)) // If half of the time of the last interaction has passed, reset allow for engage to be detected again.
                    {
                        app_state.screen_state.awake_until = millis() + max((KNOB_ENGAGED_TIMEOUT_PHYSICAL / 2), settings_.screen.timeout); // stay awake for 4 seconds after last interaction
                    }
                }
            }
            isCurrentSubPositionSet = true;
            currentSubPosition = roundedNewPosition;
            app_state.motor_state = latest_state_;
            app_state.os_mode_state = configuration_->getOSConfiguration()->mode;

            // COMPONENT SYSTEM INTEGRATION: Check if we have an active component
            if (component_manager_ && component_manager_->getActiveComponent())
            {
                // Route input to ComponentManager using Apps-like interface
                entity_state_update_to_send = component_manager_->update(app_state);

                // Components now handle their own haptics via App inheritance
                // Log component activity for debugging
                static uint32_t component_log_counter = 0;
                if (++component_log_counter % 100 == 0)
                { // Log every second (10ms * 100)
                    LOGI("Component mode active: pos=%.3f", latest_state_.sub_position_unit);
                }
            }
            else
            {
                // Traditional app system (fallback when no component is active)
                entity_state_update_to_send = display_task_->getApps()->update(app_state);
            }

#if SK_ALS
            if (settings_.screen.dim)
            {
                // We are multiplying the current luminosity of the enviroment (0,1 range)
                // by the MIN LCD Brightness. This is for the case where we are not engaging with the knob.
                // If it's very dark around the knob we are dimming this to 0, otherwise we dim it in a range
                // [0, MIN_LCD_BRIGHTNESS]
                uint16_t targetLuminosity = static_cast<uint16_t>(round(latest_sensors_state_.illumination.lux_adj * settings_.screen.min_bright));
                if (app_state.screen_state.has_been_engaged == false &&
                    abs(app_state.screen_state.brightness - targetLuminosity) > 500 && // is the change substantial?
                    millis() > app_state.screen_state.awake_until)
                {
                    if ((app_state.screen_state.brightness < targetLuminosity))
                    {
                        app_state.screen_state.brightness = (targetLuminosity);
                    }
                    else
                    {
                        // TODO: I don't like this decay function. It's too slow for delta too small
                        app_state.screen_state.brightness = app_state.screen_state.brightness - ((app_state.screen_state.brightness - targetLuminosity) / 8);
                    }
                }
                else if (app_state.screen_state.has_been_engaged == false && (abs(app_state.screen_state.brightness - targetLuminosity) <= 500))
                {
                    // in case we have very little variation of light, and the screen is not engaged, make sure we stay on a stable luminosity value
                    app_state.screen_state.brightness = (targetLuminosity);
                }
            }
            else
            {
                app_state.screen_state.brightness = settings_.screen.max_bright;
            }

#endif
#if !SK_ALS
            if (app_state.screen_state.has_been_engaged == false)
            {
                app_state.screen_state.brightness = settings_.screen.max_bright;
            }
#endif

            // MQTT functionality removed for serial-only mode

            if (entity_state_update_to_send.play_haptic)
            {
                motor_task_.playHaptic(true, false);
            }

            // NEW: Check for automatic broadcasting
            if (auto_broadcast_enabled_)
            {
                checkAndBroadcastState();
            }

            publish(app_state);
            publishState();
        }

        // current_protocol_->loop();

        motor_notifier.loopTick();
        os_config_notifier_.loopTick();

        updateHardware(&app_state);

        if (app_state.screen_state.has_been_engaged == true)
        {
            if (app_state.screen_state.brightness != settings_.screen.max_bright)
            {
                app_state.screen_state.brightness = settings_.screen.max_bright;
                sensors_task_->strainPowerUp();
            }

            if (millis() > app_state.screen_state.awake_until)
            {
                app_state.screen_state.has_been_engaged = false;
                sensors_task_->strainPowerDown();
            }
        }

        delay(10);
    }
}

void RootTask::updateHardware(AppState *app_state)
{
    static bool pressed;
#if SK_STRAIN

    if (configuration_loaded_)
    {
        switch (latest_sensors_state_.strain.virtual_button_code)
        {

        case VIRTUAL_BUTTON_SHORT_PRESSED:
            if (last_strain_pressed_played_ != VIRTUAL_BUTTON_SHORT_PRESSED)
            {
                app_state->screen_state.has_been_engaged = true;
                if (app_state->screen_state.awake_until < millis() + max((KNOB_ENGAGED_TIMEOUT_PHYSICAL / 2), settings_.screen.timeout)) // If half of the time of the last interaction has passed, reset allow for engage to be detected again.
                {
                    app_state->screen_state.awake_until = millis() + max((KNOB_ENGAGED_TIMEOUT_PHYSICAL), settings_.screen.timeout); // stay awake for 4 seconds after last interaction
                }

                LOGD("Handling short press");
                motor_task_.playHaptic(true, false);
                last_strain_pressed_played_ = VIRTUAL_BUTTON_SHORT_PRESSED;
            }
            /* code */
            break;
        case VIRTUAL_BUTTON_LONG_PRESSED:
            if (last_strain_pressed_played_ != VIRTUAL_BUTTON_LONG_PRESSED)
            {
                app_state->screen_state.has_been_engaged = true;
                if (app_state->screen_state.awake_until < millis() + max((KNOB_ENGAGED_TIMEOUT_PHYSICAL / 2), settings_.screen.timeout)) // If half of the time of the last interaction has passed, reset allow for engage to be detected again.
                {
                    app_state->screen_state.awake_until = millis() + max((KNOB_ENGAGED_TIMEOUT_PHYSICAL), settings_.screen.timeout); // stay awake for 4 seconds after last interaction
                }

                LOGD("Handling long press");

                motor_task_.playHaptic(true, true);
                last_strain_pressed_played_ = VIRTUAL_BUTTON_LONG_PRESSED;
                NavigationEvent event = NavigationEvent::LONG;

                //! GET ACTIVE FLOW? SO WE DONT HAVE DIFFERENT
                // display_task_->getActiveFlow()->handleNavigationEvent(event);
                switch (display_task_->getErrorHandlingFlow()->getErrorType())
                {
                case NO_ERROR:
                    // With simplified OSMode, always handle navigation
                    display_task_->getApps()->handleNavigationEvent(event);
                    break;
                // Network error handling removed for serial-only mode
                default:
                    break;
                }
            }
            break;
        case VIRTUAL_BUTTON_SHORT_RELEASED:
            if (last_strain_pressed_played_ != VIRTUAL_BUTTON_SHORT_RELEASED)
            {
                LOGD("Handling short press released");

                motor_task_.playHaptic(false, false);
                last_strain_pressed_played_ = VIRTUAL_BUTTON_SHORT_RELEASED;
                NavigationEvent event = NavigationEvent::SHORT;
                switch (display_task_->getErrorHandlingFlow()->getErrorType())
                {
                case NO_ERROR:
                    // With simplified OSMode, always handle navigation
                    display_task_->getApps()->handleNavigationEvent(event);
                    break;
                // Network error handling removed for serial-only mode
                default:
                    break;
                }
            }
            break;
        case VIRTUAL_BUTTON_LONG_RELEASED:

            if (last_strain_pressed_played_ != VIRTUAL_BUTTON_LONG_RELEASED)
            {
                LOGD("Handling long press released");

                motor_task_.playHaptic(false, false);
                last_strain_pressed_played_ = VIRTUAL_BUTTON_LONG_RELEASED;
            }
            break;
        default:
            last_strain_pressed_played_ = VIRTUAL_BUTTON_IDLE;
            break;
        }
    }

#endif

#if SK_DISPLAY
    if (app_state->screen_state.brightness != brightness)
    {
        // TODO: brightness scale factor should be configurable (depends on reflectivity of surface)
#if SK_ALS
        brightness = app_state->screen_state.brightness;
#endif

        display_task_->setBrightness(brightness); // TODO: apply gamma correction
    }

#endif

    if (led_ring_task_ != nullptr)
    {
        EffectSettings effect_settings;
        // THERE ARE 3 potential range of the display
        // 1- Engaged
        // 2- Not Engaged and enviroment brightness is high
        // 3- Not engaged and enviroment brightness is low
        // The following code is coreographing the different led states as :
        // if 1: led ring is fully on
        // if 2: led ring is fully off.
        // if 3: we have 1 led on as beacon (also refered as lighthouse in other part of the code).
        if (settings_.led_ring.enabled == false)
        {
            effect_settings.effect_type = EffectType::LEDS_OFF;
        }
        else if (brightness > settings_.screen.min_bright || !settings_.led_ring.dim)
        {
            // case 1. Fade to brightness
            effect_settings.effect_type = EffectType::TO_BRIGHTNESS;
            effect_settings.effect_start_pixel = 0;
            effect_settings.effect_end_pixel = NUM_LEDS;
            effect_settings.effect_accent_pixel = 0;
            effect_settings.effect_main_color = settings_.led_ring.color;
            effect_settings.effect_accent_color = settings_.led_ring.beacon.color;
            effect_settings.effect_brightness = settings_.led_ring.max_bright;
        }
        else if (brightness == settings_.screen.min_bright)
        {

            // case 2. Fade to brightness
            effect_settings.effect_type = EffectType::TO_BRIGHTNESS;
            effect_settings.effect_start_pixel = 0;
            effect_settings.effect_end_pixel = NUM_LEDS;
            effect_settings.effect_accent_pixel = 0;
            effect_settings.effect_main_color = settings_.led_ring.color;
            effect_settings.effect_accent_color = settings_.led_ring.beacon.color;
            effect_settings.effect_brightness = settings_.led_ring.min_bright;
        }
        else
        {
            if (settings_.led_ring.beacon.enabled)
            {
                // case 3 - Beacon
                effect_settings.effect_type = EffectType::LIGHT_HOUSE;
                effect_settings.effect_start_pixel = 0;
                effect_settings.effect_end_pixel = NUM_LEDS;
                effect_settings.effect_accent_pixel = 0;
                effect_settings.effect_main_color = settings_.led_ring.beacon.color;
                effect_settings.effect_accent_color = settings_.led_ring.color;
                effect_settings.effect_brightness = settings_.led_ring.beacon.brightness;

                effect_settings.led_ring_settings = settings_.led_ring;
            }
            else
            {
                effect_settings.effect_type = EffectType ::LEDS_OFF;
            }
        }
        led_ring_task_->setEffect(effect_settings);
    }
}

void RootTask::loadConfiguration()
{
    SemaphoreGuard lock(mutex_);
    if (!configuration_loaded_)
    {
        if (configuration_ != nullptr)
        {
            configuration_value_ = configuration_->get();

            settings_ = configuration_->getSettings();

            configuration_->loadOSConfiguration();

            configuration_loaded_ = true;
        }
    }
}

QueueHandle_t RootTask::getSensorsStateQueue()
{
    return sensors_status_queue_;
}

QueueHandle_t RootTask::getAppSyncQueue()
{
    return app_sync_queue_;
}

void RootTask::addListener(QueueHandle_t queue)
{
    listeners_.push_back(queue);
}

void RootTask::publish(const AppState &state)
{
    for (auto listener : listeners_)
    {
        xQueueOverwrite(listener, &state);
    }
}

void RootTask::publishState()
{
    // Apply local state before publishing to serial
    latest_state_.press_nonce = press_count_;
    // current_protocol_->handleState(latest_state_);
}

void RootTask::applyConfig(PB_SmartKnobConfig config, bool from_remote)
{
    remote_controlled_ = from_remote;
    latest_config_ = config;
    motor_task_.setConfig(config);
}

void RootTask::sendCurrentKnobState()
{
    // Use existing latest_state_ and apply current press_nonce
    PB_SmartKnobState state = latest_state_;
    state.press_nonce = press_count_;

    // Send via protocol
    if (serial_protocol_protobuf_)
    {
        serial_protocol_protobuf_->sendKnobState(state);
    }
}

// Auto-broadcasting method implementations
void RootTask::enableAutoBroadcast(bool enabled)
{
    auto_broadcast_enabled_ = enabled;
    LOGI("Auto broadcast %s", enabled ? "ENABLED" : "DISABLED");
}

void RootTask::setPositionChangeThreshold(float threshold)
{
    position_change_threshold_ = threshold;
    LOGI("Position change threshold set to %.2f", threshold);
}

void RootTask::setMaxBroadcastRate(uint32_t rate_hz)
{
    max_broadcast_interval_ = 1000 / rate_hz; // Convert Hz to ms
    LOGI("Max broadcast rate set to %u Hz (%u ms interval)", rate_hz, max_broadcast_interval_);
}

bool RootTask::shouldBroadcastState(const PB_SmartKnobState &current_state)
{
    // Check time-based rate limiting
    uint32_t current_time = millis();
    if (current_time - last_broadcast_time_ < max_broadcast_interval_)
    {
        return false; // Too soon since last broadcast
    }

    // Check for meaningful changes
    bool position_changed = abs(current_state.sub_position_unit - last_broadcast_state_.sub_position_unit) >= position_change_threshold_;
    bool press_changed = current_state.press_nonce != last_broadcast_state_.press_nonce;
    bool config_changed = strcmp(current_state.config.id, last_broadcast_state_.config.id) != 0;

    return position_changed || press_changed || config_changed;
}

void RootTask::checkAndBroadcastState()
{
    if (!auto_broadcast_enabled_)
    {
        return;
    }

    if (shouldBroadcastState(latest_state_))
    {
        sendCurrentKnobState();
        last_broadcast_state_ = latest_state_;
        last_broadcast_time_ = millis();
    }
}
