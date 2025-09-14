
## 📝 Task & Subtask Summary (Reorganized)

### Phase 3 – Clean Individ### Phase 8 – Final Cleanup 🚧

8.1 Remove all conditional compilation blocks related to HASS/network.
8.2a Stepwise remove all the different HASSapp and DemoApp flows, keeping only DemoApp
8.2b Rename DemoApp to App (if not already used, otherwise something like CustomApp)
8.3c Remove all unused mode switching (os_config->mode)
     ONBOARDING, DEMO, HASS would only become CUSTOMAPP, if we would like to keep the whole mode concept.
            
8.2 Delete obsolete HASS files (hass\_apps.cpp/.h, hass\_flow\.cpp/.h).
8.3 Remove unused Arduino libraries (WiFi, MQTT, HTTPClient, PubSubClient, etc.).
8.4 Clean up unused includes and dead dependencies.

### Phase 9 – Component-Based Remote Configuration 🚧

### 9.1 Protocol & Infrastructure ✅

* 9.1.1 ✅ Design component-based protocol (AppComponent, ComponentType, ToggleConfig).
* 9.1.2 ✅ Extend protobuf with component messages in ToSmartknob payload.
* 9.1.3 ✅ Implement unified protobuf generation (Python + C++/nanopb).
* 9.1.4 ✅ Document protocol messages and haptic behavior (snap_point_bias).
* 9.1.5 ✅ Verify cross-platform message generation and consistency.

### 9.2 Toggle Component Implementation

* 9.2.1 Create Component base class hierarchy (Component extends App).
* 9.2.2 Implement ToggleComponent with full ToggleConfig support.
* 9.2.3 Add protocol handler for AppComponent messages in root_task.cpp.
* 9.2.4 Create ComponentManager for component lifecycle management.
* 9.2.5 Implement remote toggle creation and configuration via Python.
* 9.2.6 Add asymmetric haptic feedback using snap_point_bias.
* 9.2.7 Create Python test client for toggle component validation.

### 9.3 Continuous Component (Slider/Dimmer)

* 9.3.1 Design ContinuousConfig message (min/max value, step size, units).
* 9.3.2 Implement ContinuousComponent for sliders and dimmers.
* 9.3.3 Add smooth detent behavior for continuous ranges.
* 9.3.4 Implement value-to-position mapping and display formatting.
* 9.3.5 Add Python examples for light dimmers and temperature controls.

### 9.4 Multi-Choice Component (Selector)

* 9.4.1 Design MultiChoiceConfig message (options array, wrap-around).
* 9.4.2 Implement MultiChoiceComponent for option selection.
* 9.4.3 Add dynamic detent positioning based on option count.
* 9.4.4 Implement choice-specific visual feedback and labeling.
* 9.4.5 Add Python examples for mode selectors and menu systems.

### 9.5 Component System Integration

* 9.5.1 Integrate ComponentManager with existing App framework.
* 9.5.2 Add component persistence and state management.
* 9.5.3 Implement component discovery and enumeration.
* 9.5.4 Create unified display system for all component types.
* 9.5.5 Add error handling and validation for malformed configs.

### 9.6 Advanced Component Features

* 9.6.1 Add component state broadcasting (value changes to Python).
* 9.6.2 Implement component templates and presets.
* 9.6.3 Add visual theming support (colors, fonts, layouts).
* 9.6.4 Create component composition (multiple components per app).
* 9.6.5 Add component authentication and access control.

3.1 Remove all `updateStateFromHASS()` methods (switch, light\_dimmer, climate, blinds).
3.2 Wrap HA-specific code in `#ifndef SERIAL_ONLY_MODE`.
3.3 Refactor DemoApps to inherit directly from Apps instead of HassApps.

### Phase 4 – Remove Network Infrastructure ✅

4.1 Wrap all WiFi/MQTT references with conditional compilation.
4.2 Disable network tasks in `SERIAL_ONLY_MODE` without deleting them.
4.3 Wrap remaining `#include <WiFi.h>` references in error handling code.

### Phase 5 – Simplify Architecture ✅

5.1 Reduce OSMode enum to ONBOARDING, DEMO, and UNSET.
5.2 Remove conditional HASS mode handling.
5.3 Verify architecture stability with serial-only mode.

### Phase 6 – Full Code Review ✅

6.1 Audit all conditional compilation blocks (`#ifndef SERIAL_ONLY_MODE`).
6.2 Verify all HASS/network code properly wrapped.
6.3 Document code slated for permanent removal in Phase 8.
6.4 Confirm no dead code paths or missing conditionals remain.

### Phase 7 – Communication Test (tools) 


### 7.1 Connection & Protocol Testing

* 7.1.1 Test serial connection setup and protobuf communication.
* 7.1.2 Implement auto-discovery of SmartKnob devices (USB VID/PID).
* 7.1.3 Add protocol validation in discovery (send 'q', check protobuf frames).
* 7.1.4 Remove all hardcoded COM9 references.

### 7.2 Protobuf Workflow ✅

* 7.2.1 Implement `generate_protobuf.py` for Python-side regeneration.
* 7.2.2 Ensure correct include paths for nanopb and Google protobuf.
* 7.2.3 Fix import issues in generated files (relative imports).
* 7.2.4 Auto-update `proto_gen/__init__.py` after generation.
* 7.2.5 Document regeneration process in README.

### 7.3 Python Connection Library ✅

* 7.3.1 Create clean project structure with `protocol.py`, `connection.py`, and `proto_gen/`.
* 7.3.2 Add essential tests (`test_connection.py`, `test_protocol_audit.py`, `test_device_discovery.py`).
* 7.3.3 Add examples (`basic_monitoring.py`, `two_way_communication.py`).

### 7.4 Real-Time State Communication ✅

* 7.4.1 ✅ Implement `RequestState` callback in firmware (`root_task.cpp`).
* 7.4.2 ✅ Add `sendCurrentKnobState()` in firmware for state responses.
* 7.4.3 ✅ Extend protocol with `sendKnobState()` method.
* 7.4.4 ✅ Verify `RequestState` produces `SmartKnobState` responses.
* 7.4.5 ✅ Implement Python test via `two_way_communication.py --request-state`.
* 7.4.6 ✅ Establish callback/response pattern for future message types.
* 7.4.7 ✅ Document RequestState behavior in protocol docs.
* 7.4.8 ✅ **BONUS:** Performance optimization - achieved 10Hz sustainable rate.
* 7.4.9 ✅ **BONUS:** Debug logging cleanup - eliminated 6 messages per request.

### 7.5 Automatic State Broadcasting &  Rate Limiting

* 7.5.1 Implement firmware change detection system for position changes.
* 7.5.2 Add DoEvery/FreeRTOS rate limiting (10Hz max) for automatic broadcasts.
* 7.5.3 Integrate automatic broadcasting with main loop in `root_task.cpp`.
* 7.5.4 Add configuration interface for broadcast settings (threshold, rate).
* 7.5.5 Enhance Python tools with `--polling` flag for optional RequestState.
* 7.5.6 Optional: Extend protocol with AutoBroadcastConfig message.
* 7.5.7 Performance testing: validate 50%+ reduction in serial traffic.
* 7.5.8 Document event-driven architecture and configuration options.

### Phase 8 – Final Cleanup

8.1 Remove all conditional compilation blocks related to HASS/network.
8.2a Stepwise remove all the different HASSapp and DemoApp flows, keeping only DemoApp
8.2b Rename DemoApp to App (if not already used, otherwise something like CustomApp)
8.3c Remove all unused mode switching (os_config->mode)
     ONBOARDING, DEMO, HASS would only become CUSTOMAPP, if we would like to keep the whole mode concept.
            
8.2 Delete obsolete HASS files (hass\_apps.cpp/.h, hass\_flow\.cpp/.h).
8.3 Remove unused Arduino libraries (WiFi, MQTT, HTTPClient, PubSubClient, etc.).
8.4 Clean up unused includes and dead dependencies.

### Phase 10 – CI/CD

* command line based PlatformIO build
* command line based python build
* Both automatic protobuf generation
* CI in Github

### Phase 11 – More configurable SmartKnob - Advanced

11.1 Storage of dynamic Apps on device in EEPROM
11.2 On the fly sending of upcoming detents from client side