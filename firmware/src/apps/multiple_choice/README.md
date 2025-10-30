# MultipleChoice App

A selector app migrated from the Component architecture to the stable App architecture.

## Purpose

Displays a list of hardcoded options that can be selected by rotating the knob. Shows the current selection in large text with a position indicator.

## Migration from Component

This app was migrated from `component_multiple_choice` to eliminate crashes and instability in the Component system. Key differences:

### What Changed

- **Base Class**: `Component` → `App`
- **Configuration**: Protobuf (`PB_AppComponent`) → Hardcoded constants
- **Constructor**: `configure(PB_AppComponent)` → `(mutex, app_id, friendly_name, entity_id)`
- **Options Storage**: `cfg.options[]` → `static const char* OPTIONS_[]`
- **Config Access**: `getConfig()` calls → Direct member access

### What Stayed the Same

- ✅ Three-label UI (title, option, position)
- ✅ Safe text handling with bounds checking
- ✅ JSON state emission on selection change
- ✅ Motor detent configuration
- ✅ Display update logic

### What Was Removed

- ❌ `component_config_` member
- ❌ `configure()` method
- ❌ `getConfig()` accessor
- ❌ Protobuf union field handling
- ❌ Component base class dependencies

### What Was Added

- ✅ `navigationNext()` → `DONT_NAVIGATE`
- ✅ `navigationBack()` → `MENU`
- ✅ `handleNavigation()` override
- ✅ App icons (`big_icon`, `small_icon`)
- ✅ App slug constant

## Features

- **5 Hardcoded Options**: "Option A" through "Option E"
- **Detent Selector**: Smooth rotation with tactile feedback at each option
- **Visual Feedback**: Large centered text + position counter (e.g., "3/5")
- **State Updates**: Emits JSON with selected index and text
- **Menu Navigation**: Long press returns to menu

## Implementation Details

### Hardcoded Options

```cpp
static const char* const OPTIONS_[5] = {
    "Option A",
    "Option B", 
    "Option C",
    "Option D",
    "Option E"
};
```

### Motor Configuration

```cpp
motor_config = {
    .min_position = 0,
    .max_position = 4,                // 5 options (0-4)
    .position_width_radians = 12° * π/180,
    .detent_strength_unit = 1.5,      // Medium tactile feedback
    .endstop_strength_unit = 1.5,     // Medium endstop resistance
    .snap_point = 0.5,                // Center snap
    .led_hue = 200,                   // Blue/cyan
};
```

### State Updates

JSON format emitted on selection change:

```json
{
  "selected_index": 2,
  "selected_text": "Option C"
}
```

### Navigation

- **SHORT press**: No action (stay in app)
- **LONG press**: Return to menu

### UI Layout

```
┌─────────────────────────────┐
│     Multi Choice            │  ← Title (friendly_name)
│    ● ○ ○ ○ ○                │  ← Selector arc with dots (top)
│                             │
│        Option C             │  ← Large centered text
│                             │
│                             │
└─────────────────────────────┘
```

### Visual Selector

- **Partial Ring Arc**: Semi-circular arc at the top with evenly spaced dots
- **Active Dot**: White dot indicates current selection
- **Inactive Dots**: Gray dots show other options
- **Arc Styling**: Subtle gray arc background, 10° spacing between dots

## Usage

### Adding to Demo Apps

Already registered in `demo_apps.cpp`:

```cpp
loadApp(app_position++, "multiple_choice", "selector.demo", 
        "Multi Choice", "multichoice_entity");
```

### Remote Selection (Python)

```python
# Select by string app_id
await conn.select_app_by_id("selector.demo")

# Monitor selection changes
def on_message(msg):
    if msg.WhichOneof("payload") == "smartknob_state":
        state = msg.smartknob_state
        if state.config.id == b"selector.demo":
            print(f"Position: {int(state.current_position)}")
```

### CLI Tool

```bash
# Select and monitor the app
python ./cli/select_multichoice_app.py

# Monitor for 60 seconds
python ./cli/select_multichoice_app.py --duration 60
```

## Files

- `multiple_choice.h` - Header file with class definition
- `multiple_choice.cpp` - Implementation
- `README.md` - This file

## App Slug

`APP_SLUG_MULTIPLE_CHOICE = "multiple_choice"`

## Comparison: Component vs App

| Aspect | Component | App (Current) |
|--------|-----------|---------------|
| **Stability** | ❌ Crashes reported | ✅ Stable architecture |
| **Configuration** | Protobuf runtime | Hardcoded constants |
| **Base Class** | `Component` | `App` |
| **Options** | Dynamic from proto | Static array |
| **Constructor** | `configure(config)` | `(mutex, id, name, entity)` |
| **Complexity** | High (union fields) | Low (direct access) |
| **Menu Navigation** | N/A | ✅ Long press support |

## Future Enhancements

- [ ] Create custom selector icons (instead of settings placeholder)
- [ ] Add configurable LED colors per option
- [ ] Support configurable option lists (via settings file)
- [ ] Add option descriptions (subtitle text)
- [ ] Implement wrap-around mode (optional)
- [ ] Add press-to-confirm mode (select on button press)

## Testing Checklist

- [x] Compiles without errors
- [x] Registered in demo apps
- [x] Python CLI tool created
- [ ] Test on hardware: selection changes
- [ ] Test on hardware: boundary conditions (first/last option)
- [ ] Test on hardware: long press menu navigation
- [ ] Verify no memory leaks (run for extended period)
- [ ] Verify no crashes (stress test with rapid rotation)
