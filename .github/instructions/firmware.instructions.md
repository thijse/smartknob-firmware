---
applyTo: 'firmware/**'
---

# SmartKnob - Firmware Development Quick Guide

Audience and scope
- Windows-first onboarding; concise steps to build, flash, and extend firmware.
- For deeper design details, see docs/Firmware/*.

What you will build
- A PlatformIO firmware that renders LVGL UI pages, integrates motor haptics, and exchanges protobuf-over-serial messages with a Python backend.

Build and upload (PlatformIO, VSCode)
- Open the repository in VSCode with PlatformIO extension installed.
- Ask the user to connect the SmartKnob via USB-C.
- potentially the desired environment in platformio.ini, although the default is usually correct.
  - Run the platformio code:
     platformio.exe run
  - Upload the firmware:
     platformio.exe run --target upload
    - Monitor serial output:
        platformio.exe device monitor (  - Monitor serial output:   platformio.exe device monitor (although debugging in combination with interaction likely goes better via Python backend protocol.py, either via the protobuf log messages or raw bytestream callback).)
- Alternatively ask the user to use PlatformIO toolbar:
  - Build
  - Upload
  - Monitor (serial logs)
- Boot mode tip: hold BOOT and EN/RST, then release EN/RST if upload is not detected.

Orientation: runtime architecture
- Entrypoint wires tasks and enables demo apps: [setup()](firmware/src/main.cpp:71)
- Display task (LVGL and screen mutex ownership): [DisplayTask::run()](firmware/src/display_task.cpp:50)
- Root orchestrates state, navigation, motor updates: [RootTask::run()](firmware/src/root_task.cpp:75)
- Motor FOC loop and haptics publisher: [MotorTask::run()](firmware/src/motor_foc/motor_task.cpp:40)

Apps system (classic, on-device UI)
- Registry and menu:
  - Apps container: [class Apps](firmware/src/apps/apps.h:19)
  - Add/activate apps: [Apps::add()](firmware/src/apps/apps.cpp:8), [Apps::setActive()](firmware/src/apps/apps.cpp:44)
  - Menu composition and activation: [Apps::updateMenu()](firmware/src/apps/apps.cpp:130)
- Update flow and routing:
  - Root forwards AppState to Apps: [Apps::update()](firmware/src/apps/apps.cpp:20)
  - Guard: state is delivered only when motor_state.config.id equals active app_id: [Apps::update()](firmware/src/apps/apps.cpp:29)
- Navigation dispatch and haptics:
  - Button events routed: [Apps::handleNavigationEvent()](firmware/src/apps/apps.cpp:186)
  - Motor config refresh requested after navigation: [Apps::handleNavigationEvent()](firmware/src/apps/apps.cpp:227)

Selecting apps at runtime
- Select by numeric id (0..N): [Apps::setActive()](firmware/src/apps/apps.cpp:44)
- Select by string app_id: [Apps::setActiveByAppId()](firmware/src/apps/apps.cpp:252)

  - Build UI under the shared LVGL mutex (screen per app).
  - Process knob state and emit JSON/state deltas when meaningful changes occur.
  - Update the app-specific motor_config and trigger requests.
  - App registry: [Apps::add()](firmware/src/apps/apps.cpp:8), menu: [Apps::updateMenu()](firmware/src/apps/apps.cpp:130)


# Important: Changing Firmware Configuration

  - State update routing: [Apps::update()](firmware/src/apps/apps.cpp:20)



- Regenerate C++ nanopb outputs (firmware only):
  - python [regenerate_protobuf.py](smartknob-connection/regenerate_protobuf.py:19) --cpp
- Advanced generator (targets and paths):
  - [generate_protobuf.py](smartknob-connection/protobuf/generate_protobuf.py:83)

Troubleshooting (concise)
- Haptics not updating: request a motor config update after state/navigation changes; see [Apps::handleNavigationEvent()](firmware/src/apps/apps.cpp:227).

See also
- Install and build: .github/instructions/install_and_build.instructions.md
- Backend quick guide: .github/instructions/backend.instructions.md
- Deep-dive: docs/Firmware/apps_architecture.md, docs/Firmware/configuration.md, docs/Firmware/motor_control.md, docs/Firmware/protobuf.md

Notes
- Paths and examples standardize on smartknob-connection for host-side code references.
- Historical references to smartknob-connection2 may exist in legacy docs; use smartknob-connection for new work.
