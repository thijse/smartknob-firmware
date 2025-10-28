---
applyTo: '/**'
---

# SmartKnob - Quick Install and Build Guide

## Audience and scope
- Windows-first onboarding with Python 3.11+, VSCode + PlatformIO.
- Concise getting-started for AI and humans; deeper topics linked into docs.
- Canonical Python library path: smartknob-connection (legacy references to smartknob-connection2 are deprecated).

## Table of Contents
- Prerequisites
- Documentation bootstrapping
- Installation process
- Firmware build and upload
- Python backend setup
- Protobuf regeneration
- Best practices
- Available documentation
- Mermaid overview

## Prerequisites
- Windows 11, VSCode with PlatformIO extension installed.
- Python 3.11+ on PATH.
- Git with submodules initialized:
  - Run: git submodule update --init --recursive
- Protocol buffers compiler (protoc). See docs/PythonClient/PROTOCOL.md for platform-specific install notes.
- USB drivers for ESP32-S3 or CH340 as applicable.

## Documentation bootstrapping
- The .github/instructions directory contains the main onboarding documentation; .kilocode/rules contains hardlinks to the same files.
- install_and_build.instructions.md is the starting point and links to the firmware and backend instructions, which in turn link into docs for details.

## Installation process

### Firmware build and upload (PlatformIO, VSCode)
Build and upload (PlatformIO, VSCode)
- Open the repository in VSCode with PlatformIO extension installed.
- Ask the user to connect the SmartKnob via USB-C.
- potentially the desired environment in platformio.ini, although the default is usually correct.
  - Run the platformio code: platformio.exe run
  - Upload the firmware:     platformio.exe run --target upload
  - Monitor serial output:   platformio.exe device monitor (although debugging in combination with interaction likely goes better via Python backend protocol.py, either via the protobuf log messages or raw bytestream callback).
- Alternatively ask the user to use PlatformIO toolbar
- Boot mode tip: hold BOOT and EN/RST, then release EN/RST if upload is not detected.

### Python backend setup
- Create and activate a virtual environment:
  - Windows:
    - cd smartknob-connection
    - .\venv\Scripts\activate
    - if does not exist: python -m venv venv
    
- Install dependencies (assuming smartknob-connection is the current directory):
  - pip install -r /requirements.txt
- Generate protobuf bindings(assuming smartknob-connection is the current directory):
  - python regenerate_protobuf.py

### Protobuf regeneration
- Canonical proto sources live under proto/.
- Use the unified generator for Python and firmware nanopb outputs:
  - python regenerate_protobuf.py --python        # Python only
  - python regenerate_protobuf.py --cpp           # Firmware only
  - python regenerate_protobuf.py --all           # Both
- Advanced targets and options: protobuf/generate_protobuf.py and docs/Firmware/protobuf.md.

### Best practices for backend usage
- Use async with AnyIO for connection and read loop:
  - Start connection with SmartKnobConnection.start and run SmartKnobConnection.start_read_loop in an anyio task group.
- Configure callbacks:
  - SmartKnobConnection.set_message_callback to consume FromSmartKnob messages.
  - SmartKnobConnection.set_raw_data_callback to capture raw framed bytes for debugging.
- Reset behavior on ESP32:
  - Reset-at-close is determined during open; DTR/RTS state at open time governs subsequent reset on close.
  - After the first connection, the device may be immune to resets until idle; plan resets accordingly.

## Available documentation
- Firmware apps architecture: docs/Firmware/apps_architecture.md
- Firmware configuration and motor control: docs/Firmware/configuration.md, docs/Firmware/motor_control.md
- Firmware protobuf integration: docs/Firmware/protobuf.md
- Python client docs: docs/PythonClient/PROTOCOL.md, docs/PythonClient/IMPLEMENTATION.md, docs/PythonClient/TROUBLESHOOTING.md

## Cross-links
- Backend (Python) instructions: .github/instructions/backend.instructions.md
- Firmware (C++/Arduino/PlatformIO) instructions: .github/instructions/firmware.instructions.md

##Mermaid overview
```mermaid
flowchart LR
Host --> Protocol
Protocol --> Firmware
Firmware --> Apps
Apps --> Motor
Motor --> Root
Root --> Display
```

## Notes
- Paths and examples in this guide standardize on smartknob-connection.
- Older documents or scripts may reference smartknob-connection2; prefer the updated paths when following this guide.