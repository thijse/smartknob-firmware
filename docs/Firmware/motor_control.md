# SmartKnob Motor Control System

This document provides an overview of the SmartKnob's motor control system, which is responsible for creating the haptic feedback and virtual detents that are central to the SmartKnob's functionality.

## 1. Overview

The SmartKnob uses a brushless DC (BLDC) motor with Field-Oriented Control (FOC) to provide precise torque control. This enables the creation of virtual detents, endstops, and other haptic feedback effects that make the knob feel like a mechanical device with physical detents, despite being entirely software-controlled.

Key components of the motor control system:
- BLDC motor (typically a gimbal motor)
- Magnetic position sensor (MT6701, TLV, or MAQ430)
- Motor driver (TMC6300)
- PID controller for torque control
- Configuration parameters for customizing the feel

## 2. Motor Task

The motor control system is implemented in the `MotorTask` class, which runs as a FreeRTOS task. This task is responsible for:

- Initializing the motor and sensor
- Calibrating the motor (determining pole pairs, direction, and zero electrical angle)
- Processing commands from other tasks (configuration changes, haptic feedback requests)
- Running the FOC control loop
- Implementing the detent simulation algorithm
- Publishing the current state to other tasks

## 3. Motor Configuration

The motor behavior is configured through the `SmartKnobConfig` structure, which defines parameters like detent strength, position width, and snap points.

For a detailed explanation of the `SmartKnobConfig` structure and its parameters, see the [Configuration System](configuration.md#2-smartknobconfig) documentation.

The motor control system uses these configuration parameters to determine:
- The current position and allowed range
- The strength and width of detents
- The behavior at endstops
- The snap point for position changes

## 4. Detent Simulation Algorithm

The SmartKnob simulates detents using a PID controller that applies torque based on the angle to the nearest detent center. The algorithm works as follows:

1. Calculate the angle to the current detent center
2. Apply a dead zone adjustment for small angles to prevent jitter
3. Check if the angle exceeds the snap point threshold
4. If the threshold is exceeded, move to the next/previous detent
5. Calculate the torque to apply using the PID controller
6. Apply the torque to the motor

```cpp
// Calculate angle to detent center
float angle_to_detent_center = motor.shaft_angle - current_detent_center;

// Check if we've moved far enough to snap to another detent
float snap_point_radians = config.position_width_radians * config.snap_point;
if (angle_to_detent_center > snap_point_radians && current_position > config.min_position) {
    current_detent_center += config.position_width_radians;
    angle_to_detent_center -= config.position_width_radians;
    current_position--;
} else if (angle_to_detent_center < -snap_point_radians && current_position < config.max_position) {
    current_detent_center -= config.position_width_radians;
    angle_to_detent_center += config.position_width_radians;
    current_position++;
}

// Apply torque based on angle to detent
float torque = motor.PID_velocity(-angle_to_detent_center);
motor.move(torque);
```

## 5. Magnetic Detent Mode

The SmartKnob supports a "magnetic detent" mode where only specific positions have detents, with smooth rotation elsewhere. This is implemented by checking if the current position is in the list of detent positions:

```cpp
if (config.detent_positions_count > 0) {
    bool in_detent = false;
    for (uint8_t i = 0; i < config.detent_positions_count; i++) {
        if (config.detent_positions[i] == current_position) {
            in_detent = true;
            break;
        }
    }
    if (!in_detent) {
        input = 0;  // No torque if not at a detent position
    }
}
```

## 6. Haptic Feedback

In addition to the continuous detent simulation, the SmartKnob can provide discrete haptic feedback for events like button presses. This is implemented by applying a brief pulse of torque in one direction followed by a pulse in the opposite direction:

```cpp
void MotorTask::playHaptic(bool press, bool long_press) {
    // Play a hardcoded haptic "click"
    float strength = press ? 5 : 1.5;
    if (long_press) {
        strength = 20;
    }
    motor.move(strength);
    delay(3);
    motor.move(-strength);
    delay(3);
    motor.move(0);
}
```

## 7. Motor Calibration

The SmartKnob requires motor calibration to determine:
- The direction of rotation relative to the sensor
- The number of pole pairs in the motor
- The zero electrical angle offset

Calibration is performed automatically on first use or can be triggered manually. The calibration process:

1. Determines the direction by rotating the motor and checking the sensor direction
2. Determines pole pairs by rotating a known number of electrical revolutions and measuring mechanical angle
3. Determines zero electrical angle by measuring mechanical angle at electrical zero positions
4. Saves the calibration parameters to persistent storage

## 8. Sensor Integration

The SmartKnob supports several magnetic position sensors:

- **MT6701**: Excellent sensor with SSI interface, low noise, and good response latency
- **TLV493D**: 3D magnetic sensor with I2C interface, but can be noisy and has known issues
- **MAQ430**: SPI-based magnetic sensor

The sensor provides the absolute position of the knob, which is essential for the detent simulation algorithm.

## 9. Idle Correction

To handle small sensor drift or mechanical bias, the SmartKnob implements an idle correction algorithm that slowly adjusts the detent center when the knob is not moving:

```cpp
if (last_idle_start > 0 && 
    millis() - last_idle_start > IDLE_CORRECTION_DELAY_MILLIS && 
    fabsf(motor.shaft_angle - current_detent_center) < IDLE_CORRECTION_MAX_ANGLE_RAD) {
    current_detent_center = motor.shaft_angle * IDLE_CORRECTION_RATE_ALPHA + 
                           current_detent_center * (1 - IDLE_CORRECTION_RATE_ALPHA);
}
```

## 10. Integration with UI System

The motor control system integrates with the UI system through:

1. **Configuration Updates**: The UI system can update the motor configuration to change the feel of the knob based on the current app or context.
2. **State Updates**: The motor task publishes the current position and sub-position to the UI system.
3. **Haptic Feedback**: The UI system can request haptic feedback for events like button presses.

Example of updating motor configuration from an app:

```cpp
void MyApp::handleNavigation(NavigationEvent event) {
    switch (event) {
        case SHORT:
            // Switch to a different configuration with finer control
            motor_config = fine_control_config;
            motor_notifier->requestUpdate(motor_config);
            break;
    }
}
```

## 11. Best Practices for Motor Configuration

For detailed best practices on configuring the motor for different applications, see the [Configuration System - Best Practices](configuration.md#9-best-practices-for-configuration) documentation.

Some motor-specific considerations:

1. **Magnetic Detents**:
   - Use for interfaces where only certain positions should have detents
   - Limit to 5 positions at a time due to protocol limitations
   - Update the list as the user rotates through a larger range

2. **PID Tuning**:
   - Adjust the PID parameters based on the detent width
   - Use lower derivative factors for coarse detents to reduce noise
   - Use higher proportional factors for stronger detents

## 12. Example Configurations

For example configurations for different use cases, see the [Configuration System - Example Configurations](configuration.md#10-example-configurations) documentation.

The motor control system can be configured for a wide range of applications, from fine-grained control for volume or color adjustment to coarse control for menu navigation.
