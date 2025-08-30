# SmartKnob Configuration System

This document provides a comprehensive overview of the SmartKnob's configuration system, which manages various settings including motor behavior, UI preferences, network connections, and system modes.

## 1. Overview

The SmartKnob uses several configuration classes to manage different aspects of its behavior:

- **SmartKnobConfig**: Controls the motor behavior, detent simulation, and haptic feedback
- **SETTINGS_Settings**: Manages display and LED ring settings

These configurations are stored persistently in flash memory and loaded on startup.

## 2. SmartKnobConfig

The `SmartKnobConfig` structure is central to the SmartKnob's haptic feedback system, controlling how the knob feels and behaves.

```protobuf
message SmartKnobConfig {
    int32 position = 1;                    // Current integer position of the knob
    float sub_position_unit = 2;           // Current fractional position (0-1)
    uint32 position_nonce = 3;             // Used to force position updates
    int32 min_position = 4;                // Minimum allowed position
    int32 max_position = 5;                // Maximum allowed position
    float position_width_radians = 6;      // Angular width of each position/detent
    float detent_strength_unit = 7;        // Strength of detents (0-1)
    float endstop_strength_unit = 8;       // Strength of endstop torque (0-1)
    float snap_point = 9;                  // Threshold for position change
    string id = 10;                        // Identifier for this configuration
    repeated int32 detent_positions = 11;  // Specific positions with detents
    float snap_point_bias = 12;            // Bias for asymmetric detents
    int32 led_hue = 13;                    // Hue for ring LEDs (0-255)
}
```

### Key Parameters

- **position**: The current integer position of the knob. This is the primary value that applications read.
- **sub_position_unit**: The fractional position within the current detent (0-1). Used for fine control.
- **position_width_radians**: Controls how far the knob must be turned to move between positions. Smaller values create finer control, while larger values create coarser control.
- **detent_strength_unit**: Controls how strong the detents feel (0-1). A value of 0 disables detents completely.
- **endstop_strength_unit**: Controls how strong the endstops feel at min/max positions (0-1).
- **snap_point**: Controls the threshold for position changes, affecting hysteresis. Must be >= 0.5 for stability.
- **detent_positions**: Can be used to create "magnetic" detents at specific positions, with smooth rotation elsewhere.
- **snap_point_bias**: Advanced feature for shifting the snap point away from the center, creating asymmetric detents.
- **led_hue**: Controls the color of the LED ring (0-255).

### Usage in Different Contexts

#### Motor Control

The motor control system uses SmartKnobConfig to determine:

- The current position and allowed range
- The strength and width of detents
- The behavior at endstops
- The snap point for position changes

See [Motor Control System](motor_control.md) for details on how these parameters affect the motor behavior.

#### UI System

The UI system uses SmartKnobConfig to:

- Update the display based on the current position
- Change the motor behavior based on the current app
- Synchronize state between the UI and the motor

See [UI System](ui_system.md) for details on how the UI interacts with SmartKnobConfig.

#### Communication

## 6. SETTINGS_Settings

The `SETTINGS_Settings` structure manages display and LED ring settings.

```protobuf
message SETTINGS_Screen {
    bool dim = 1;
    uint32 max_bright = 2;
    uint32 min_bright = 3;
    uint32 timeout = 4;
}

message SETTINGS_LEDRingBeacon {
    bool enabled = 1;
    uint32 brightness = 2;
    uint32 color = 3;
}

message SETTINGS_LEDRing {
    bool enabled = 1;
    bool dim = 2;
    uint32 max_bright = 3;
    uint32 min_bright = 4;
    uint32 color = 5;
    bool has_beacon = 6;
    SETTINGS_LEDRingBeacon beacon = 7;
}

message SETTINGS_Settings {
    bool has_screen = 1;
    SETTINGS_Screen screen = 2;
    bool has_led_ring = 3;
    SETTINGS_LEDRing led_ring = 4;
}
```

These settings control the behavior of the display and LED ring, including brightness, dimming, and timeouts.

## 7. Configuration Storage and Persistence

The SmartKnob uses several storage mechanisms for configuration:

### Flash Storage

The `Configuration` class manages loading and saving configuration to flash memory using the FFat filesystem.

```cpp
bool loadFromDisk();
bool saveToDisk();
bool resetToDefaults();
```

Configuration is stored in two files:

- `/config.pb`: Stores the persistent configuration (motor calibration, etc.)
- `/settings.pb`: Stores the settings (display, LED ring, etc.)

### EEPROM

Some configuration is stored in EEPROM for faster access:

```cpp
bool saveOSConfiguration(OSConfiguration os_config);
bool loadOSConfiguration();
```

EEPROM is used for:

- WiFi configuration
- MQTT configuration
- OS mode
- Strain calibration

## 8. Configuration Events and Notifications

The SmartKnob uses a notification system to inform tasks about configuration changes:

### Notifiers

- **MotorNotifier**: Notifies the motor task about SmartKnobConfig changes
- **OSConfigNotifier**: Notifies tasks about OS mode changes

Other tasks can subscribe to this queue to receive notifications about configuration changes.

## 9. Best Practices for Configuration

### SmartKnobConfig

When configuring the motor for different applications, consider the following best practices:

1. **Detent Width**:
   
   - Fine control: 1-3 degrees per position (0.017-0.052 radians)
   - Medium control: 5-10 degrees per position (0.087-0.175 radians)
   - Coarse control: 15-30 degrees per position (0.262-0.524 radians)

2. **Detent Strength**:
   
   - Light detents: 0.2-0.4
   - Medium detents: 0.5-0.7
   - Strong detents: 0.8-1.0

3. **Snap Point**:
   
   - Minimal hysteresis: 0.5-0.7
   - Medium hysteresis: 0.8-1.0
   - Strong hysteresis: 1.1-1.5

4. **Endstop Strength**:
   
   - Soft endstops: 0.3-0.5
   - Medium endstops: 0.6-0.8
   - Hard endstops: 0.9-1.0

## 10. Example Configurations

### Volume Control

```cpp
PB_SmartKnobConfig volume_config = {
    .position = 50,                   // Start at 50% volume
    .min_position = 0,                // 0% minimum
    .max_position = 100,              // 100% maximum
    .position_width_radians = 2.0 * PI / 180,  // 2 degrees per step
    .detent_strength_unit = 0.6,      // Medium detents
    .endstop_strength_unit = 1.0,     // Strong endstops
    .snap_point = 0.8,                // Medium hysteresis
};
```

### Menu Navigation

```cpp
PB_SmartKnobConfig menu_config = {
    .position = 0,
    .min_position = 0,
    .max_position = menu_items - 1,
    .position_width_radians = 15.0 * PI / 180,  // 15 degrees per item
    .detent_strength_unit = 0.8,      // Strong detents
    .endstop_strength_unit = 1.0,     // Strong endstops
    .snap_point = 1.0,                // Strong hysteresis
};
```

### Color Picker (Hue)

```cpp
PB_SmartKnobConfig hue_config = {
    .position = 0,
    .min_position = 0,
    .max_position = 359,              // 0-359 degrees of hue
    .position_width_radians = 1.0 * PI / 180,  // 1 degree per step
    .detent_strength_unit = 0.3,      // Light detents
    .endstop_strength_unit = 0.0,     // No endstops (wraps around)
    .snap_point = 0.6,                // Light hysteresis
};
```
