# SmartKnob Protobuf Documentation

## Overview

SmartKnob uses Protocol Buffers (protobuf) for communication between the Python client and C++ firmware. The protobuf system evolved through multiple phases to support the component-based remote configuration architecture, where Python clients can dynamically create and configure interactive components (toggles, sliders, etc.) rather than using fixed firmware apps.

## Development Evolution

The SmartKnob protobuf system evolved through several phases:

### Phase 7: Foundation (Completed ✅)

- **7.2.1**: Initial `generate_protobuf.py` implementation
- **7.2.2**: Established nanopb and Google protobuf include paths
- **7.2.3**: Fixed relative import issues in generated files
- **7.2.4**: Auto-generation of `proto_gen/__init__.py`
- **7.2.5**: Comprehensive documentation and workflow

### Phase 9: Component Architecture (Completed ✅)

- **9.1.1**: Component-based protocol design (`AppComponent`, `ComponentType`, `ToggleConfig`)
- **9.1.2**: Extended protobuf with component messages in `ToSmartknob.payload`
- **9.1.3**: **Unified protobuf generation** - the current recommended approach
- **9.1.4**: Documented protocol messages and haptic behavior
- **9.1.5**: Verified cross-platform message generation

### Architecture Transformation

```text
Traditional Architecture:
Python → SmartKnobConfig (motor behavior only)
Fixed Apps: [LightDimmer] [Climate] [Blinds] [Switch]

Component Architecture:
Python → AppComponent (complete UI + behavior + haptics)
Dynamic Components: [ToggleComponent] [ContinuousComponent] [MultiChoiceComponent]
                         ↑                    ↑                      ↑
                    Configurable         Configurable           Configurable
```

## Architecture

```text
┌─────────────────┐    Serial + Protobuf    ┌─────────────────┐
│   Python Client │ ◄─────────────────────► │  C++ Firmware   │
│                 │                         │                 │
│ - smartknob_pb2 │                         │ - smartknob.pb.h│
│ - settings_pb2  │                         │ - settings.pb.h │
└─────────────────┘                         └─────────────────┘
```

**Communication Stack:**

- **Transport**: Serial over USB-C
- **Framing**: COBS (Consistent Overhead Byte Stuffing)
- **Validation**: CRC32 checksums
- **Protocol**: Protocol Buffers (protobuf)

## Protocol Files

### Core Protocol Definitions

**Location**: `proto/`

- **`smartknob.proto`**: Main communication protocol
  - App control messages
  - Component management (ToggleComponent, etc.)
  - Knob state and commands
  - System status messages

- **`settings.proto`**: Configuration and settings
  - Motor configuration
  - Display settings
  - App-specific configurations

### Generated Files

**Python Output** (`smartknob-connection2/smartknob/proto_gen/`):

```text
smartknob_pb2.py    # Main protocol classes
settings_pb2.py     # Settings classes
nanopb_pb2.py       # Nanopb metadata (optional)
__init__.py         # Module initialization
```

**C++ Output** (`firmware/src/proto/proto_gen/`):

```text
smartknob.pb.h/.pb.c    # Main protocol (nanopb)
settings.pb.h/.pb.c     # Settings protocol (nanopb)
```

## Setup Requirements

### 1. Initialize Git Submodules

**CRITICAL FIRST STEP** - Required for C++ generation:

```bash
git submodule update --init --recursive
```

This downloads the nanopb submodule to `proto/thirdparty/nanopb/`.

### 2. Install Python Dependencies

```bash
# In virtual environment
pip install grpcio-tools>=1.50.0

# Or install all connection2 requirements
cd smartknob-connection2
pip install -r requirements.txt
```

### 3. Verify Setup

Check that required tools are available:

```bash
# Check protoc (system protobuf compiler)
protoc --version

# Check nanopb submodule
ls proto/thirdparty/nanopb/generator/nanopb_generator.py
```

## Generation Scripts

SmartKnob provides three different protobuf generation approaches:

### Option 1: Unified Generator (Recommended)

**Location**: Repository root  
**Development Phase**: Task 9.1.3 (Component Architecture)

```bash
python regenerate_protobuf_unified.py
```

**Features:**

- ✅ Generates both Python and C++ in one command
- ✅ Dependency checking with helpful error messages  
- ✅ Component message validation (AppComponent, ToggleConfig, etc.)
- ✅ Backup management
- ✅ Simple, no arguments needed
- ✅ **Current recommended approach** from project roadmap

**Why This Script?** This is the deliverable from Task 9.1.3 "Implement unified protobuf generation" and represents the evolution toward the component-based architecture.

### Option 2: Full-Featured Generator

**Location**: `smartknob-connection2/protobuf/`  
**Development Phase**: Task 7.2.1 (Foundation)

```bash
cd smartknob-connection2
python protobuf/generate_protobuf.py [--python|--cpp|--all]
```

**Features:**

- ✅ Most comprehensive error handling and documentation
- ✅ Flexible generation options
- ✅ Advanced backup system with cleanup
- ✅ File comparison and change detection
- ✅ Extensive troubleshooting documentation

**When to Use**: Advanced development, debugging generation issues, or when you need detailed control over the generation process.

**Arguments:**

- `--python`: Generate Python files only (default)
- `--cpp`: Generate C++ nanopb files only
- `--all`: Generate both Python and C++ files

### Option 3: Convenience Wrapper

**Location**: `smartknob-connection2/`

```bash
cd smartknob-connection2
python regenerate_protobuf.py [args...]
```

**Features:**

- ✅ Simple wrapper around Option 2
- ✅ Can be run from anywhere in smartknob-connection2
- ✅ Forwards all arguments to main generator

## Usage Examples

### Quick Start

```bash
# 1. First time setup
git submodule update --init --recursive
pip install grpcio-tools

# 2. Generate protobuf files
python regenerate_protobuf_unified.py
```

### Development Workflow

```bash
# After modifying .proto files
python regenerate_protobuf_unified.py

# Build and test firmware
cd firmware
platformio run
platformio upload

# Test Python client
cd ../smartknob-connection2
python examples/test_component_messages.py
```

### Selective Generation

```bash
# Python only (for client development)
cd smartknob-connection2
python regenerate_protobuf.py --python

# C++ only (for firmware development)  
python regenerate_protobuf.py --cpp

# Both with comparison
python regenerate_protobuf.py --all
```

## Component Protocol

The protobuf system is central to SmartKnob's **component-based remote configuration** architecture. Instead of fixed firmware apps, Python clients can dynamically create and configure interactive components.

### Remote Configuration Flow

```text
Python Client                 SmartKnob Firmware
     │                              │
     ├─ AppComponent msg ──────────→ │ ComponentManager
     │  ├─ component_id             │ ├─ Create/Update Component
     │  ├─ ComponentType            │ ├─ Apply Configuration  
     │  └─ ToggleConfig             │ └─ Set as Active
     │                              │
     ├─ Visual Updates ←──────────── │ Component.render()
     └─ State Changes ←───────────── │ Component.updateState()
```

### Control Architecture

**Traditional Apps** (Legacy):

- **Navigation**: UI-based menu system
- **Configuration**: Hardcoded in firmware
- **Activation**: MQTT/Home Assistant integration

**Component System** (Current):

- **Navigation**: Protobuf-controlled (no UI menu needed)
- **Configuration**: Dynamic via `AppComponent` messages
- **Activation**: Direct Python client commands

### Creating New Components

When adding new component types, update `smartknob.proto`:

```protobuf
// Add to ComponentType enum
enum ComponentType {
    TOGGLE = 0;
    YOUR_COMPONENT = 1;  // Add here
}

// Add configuration message
message YourComponentConfig {
    // Your config fields
    bool enabled = 1;
    int32 value = 2;
}

// Add to ComponentConfig oneof
message ComponentConfig {
    oneof config {
        ToggleConfig toggle_config = 1;
        YourComponentConfig your_config = 2;  // Add here
    }
}
```

### Python Client Usage

```python
from smartknob.proto_gen import smartknob_pb2

# Create component message
component_msg = smartknob_pb2.AppComponent()
component_msg.component_id = 1
component_msg.component_type = smartknob_pb2.ComponentType.TOGGLE

# Configure component
component_msg.config.toggle_config.position_0 = "OFF"
component_msg.config.toggle_config.position_1 = "ON"

# Send to SmartKnob
knob.send_app_component(component_msg)
```

### C++ Firmware Usage

```cpp
#include "smartknob.pb.h"

// Handle component creation
void handle_app_component(const PB_AppComponent& component) {
    if (component.component_type == PB_ComponentType_TOGGLE) {
        auto toggle_config = component.config.toggle_config;
        // Create ToggleComponent with config
        create_toggle_component(component.component_id, toggle_config);
    }
}
```

## Troubleshooting

### Common Issues

#### nanopb_generator.py not found

```bash
# Solution: Initialize submodules
git submodule update --init --recursive
```

#### grpcio-tools not found

```bash
# Solution: Install Python dependencies
pip install grpcio-tools>=1.50.0
```

#### protoc not found

```bash
# Solution: Install system protobuf compiler
# Ubuntu/Debian:
sudo apt install protobuf-compiler

# macOS:
brew install protobuf

# Windows: Download from Protocol Buffers releases
```

#### Import errors in Python

```bash
# Solution: Regenerate with import fixing
python regenerate_protobuf_unified.py
```

#### Missing component messages

```bash
# Check if messages exist in generated files
grep -r "ComponentType\|AppComponent" smartknob-connection2/smartknob/proto_gen/
grep -r "PB_ComponentType\|PB_AppComponent" firmware/src/proto/proto_gen/
```

### Validation

After generation, verify files contain expected content:

**Python validation:**

```python
from smartknob.proto_gen import smartknob_pb2
print(dir(smartknob_pb2.ComponentType))  # Should show TOGGLE, etc.
```

**C++ validation:**

```cpp
// Check that these compile
#include "smartknob.pb.h"
PB_ComponentType type = PB_ComponentType_TOGGLE;
PB_AppComponent component = PB_AppComponent_init_default;
```

## File Structure

```text
smartknob-firmware/
├── proto/                          # Protocol definitions
│   ├── smartknob.proto            # Main protocol
│   ├── settings.proto             # Settings protocol  
│   └── thirdparty/nanopb/         # nanopb submodule
├── regenerate_protobuf_unified.py # Root unified generator
├── smartknob-connection2/
│   ├── regenerate_protobuf.py     # Convenience wrapper
│   ├── protobuf/
│   │   └── generate_protobuf.py   # Full-featured generator
│   └── smartknob/proto_gen/       # Generated Python files
└── firmware/src/proto/proto_gen/   # Generated C++ files
```

## Best Practices

### Component Development Workflow

1. **Modify protocol**: Edit `.proto` files in `proto/`
2. **Regenerate**: Run unified generator from repository root
3. **Test Python**: Verify client can import and use new messages
4. **Build firmware**: Ensure C++ compilation succeeds
5. **Integration test**: Test end-to-end communication

### Version Control

- **Commit `.proto` files**: Source protocol definitions
- **Commit generated files**: Ensures build reproducibility
- **Include submodule**: Ensure nanopb submodule is properly tracked

### Component Development

1. **Protocol first**: Define messages in `.proto` before implementation
2. **Regenerate early**: Generate files before writing client/firmware code
3. **Validate generation**: Check that expected messages appear in both languages
4. **Test communication**: Verify serialization/deserialization works

## Advanced Usage

### Custom nanopb Options

Add nanopb-specific options to `.proto` files:

```protobuf
import "nanopb.proto";

message LargeMessage {
    // Limit string size for embedded use
    string description = 1 [(nanopb).max_size = 64];
    
    // Fixed-size arrays
    repeated int32 values = 2 [(nanopb).max_count = 10];
}
```

### Multiple Proto Files

When adding new `.proto` files:

1. Place in `proto/` directory
2. Add to generation scripts if needed
3. Update include paths in both Python and C++
4. Regenerate all files to update dependencies

### Cross-Platform Compatibility

- **Byte order**: Protocol Buffers handles endianness automatically
- **Size limits**: Use nanopb options to control memory usage
- **Field numbers**: Never reuse field numbers (breaks compatibility)
- **Enum values**: Never change existing enum values

## Integration with Build Systems

### PlatformIO (Firmware)

Generated files are automatically included in the firmware build:

```ini
# platformio.ini includes proto_gen directory
build_flags = -I src/proto/proto_gen
```

### Python Packaging

Generated files are part of the smartknob package:

```python
# Importable as module
from smartknob.proto_gen import smartknob_pb2, settings_pb2
```

### Continuous Integration

Include protobuf generation in CI workflows:

```bash
# CI validation script
git submodule update --init --recursive
python regenerate_protobuf_unified.py
git diff --exit-code  # Ensure no unexpected changes
```

This documentation covers the complete protobuf workflow for SmartKnob development, from initial setup through advanced usage patterns.
