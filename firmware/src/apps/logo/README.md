# Logo App

A simple SmartKnob app that displays a static logo image.

## Purpose
Displays a centered logo on the SmartKnob screen with locked motor position (no rotation). Useful for branding, splash screens, or static information display.

## Features
- **Static Display**: Shows a centered logo image
- **Locked Motor**: Motor is configured to resist rotation (locked position)
- **Menu Navigation**: Long press returns to menu
- **Minimal Interaction**: Short press does nothing (stays in app)

## Implementation Details

### Motor Configuration
```cpp
motor_config = {
    .position = 0,
    .max_position = 0,        // Locked (no rotation)
    .detent_strength_unit = 10,  // Strong resistance
    .endstop_strength_unit = 10,
    .led_hue = 200,           // Blue/cyan LED color
};
```

### Navigation
- **SHORT press**: No action (DONT_NAVIGATE)
- **LONG press**: Return to menu (MENU)

### Icons
Currently using placeholder `x80_settings` and `x40_settings` icons.
**TODO**: Create dedicated logo-specific icons (80x80 and 40x40).

### Image Asset
- Main logo: `logo_image` (168x168, RGB565 format)
- Generated from: `logo_image.c`

## Usage

### Adding to Demo Apps
Already registered in `demo_apps.cpp`:
```cpp
loadApp(app_position++, "logo", "logo.display", "Logo Display", "logo_entity");
```

### Remote Selection (Python)
```python
# Select by string app_id
await conn.select_app_by_id("logo.display")

# Select by numeric position (depends on order in demo_apps.cpp)
await conn.select_app(6)  # Check actual position
```

### CLI Tool
```bash
python ./cli/select_app.py --app-id logo.display
```

## Files
- `logo.h` - Header file with class definition
- `logo.cpp` - Implementation
- `logo_image.c` - Generated image data (168x168 logo)
- `README.md` - This file

## App Slug
`APP_SLUG_LOGO = "logo"`

## Future Enhancements
- [ ] Create custom logo icons for menu display
- [ ] Add configurable LED colors
- [ ] Support multiple logo images (switchable)
- [ ] Add fade-in animation on load
