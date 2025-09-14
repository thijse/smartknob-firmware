# Audit-only repository cleanup report
Scope
- Full workspace scan focusing on: orphaned/unreferenced files, obsolete/stale code, generated artifacts, large logs/binaries, CI/config drift, and test compatibility.
- Evidence cites are clickable to exact code or file locations.

Key findings by category

1) Orphaned or likely-unreferenced code/assets
- Old LVGL font assets (unused)
  - Legacy fonts under [firmware/src/assets/fonts/OLD](firmware/src/assets/fonts/OLD):
    - [kode_mono_16.c](firmware/src/assets/fonts/OLD/kode_mono_16.c:909), [kode_mono_20.c](firmware/src/assets/fonts/OLD/kode_mono_20.c:1173), [kode_mono_40.c](firmware/src/assets/fonts/OLD/kode_mono_40.c:3042)
    - [nds12_10px.c](firmware/src/assets/fonts/OLD/nds12_10px.c:1181), [nds12_14px.c](firmware/src/assets/fonts/OLD/nds12_14px.c:1742), [nds12_20px.c](firmware/src/assets/fonts/OLD/nds12_20px.c:2480)
    - [EIGHTTWOXC_48px.c](firmware/src/assets/fonts/OLD/EIGHTTWOXC_48px.c:3992)
  - The current font set used by LVGL is declared in [LV_FONT_CUSTOM_DECLARE](firmware/src/display/lv_conf.h:380) and references AktivGrotesk and RobotoMono font families (e.g., [roboto_semi_bold_mono_16pt](firmware/src/display/lv_conf.h:392), [aktivgrotesk_regular_12pt_8bpp_subpixel](firmware/src/display/lv_conf.h:385)), with active usage throughout UI code (e.g., [component_multiple_choice.cpp](firmware/src/components/multipleChoice/component_multiple_choice.cpp:106), [climate.cpp](firmware/src/apps/climate/climate.cpp:49), [stopwatch.cpp](firmware/src/apps/stopwatch/stopwatch.cpp:68)). No references were found to the OLD font symbols outside their own files. Recommendation: mark as deprecated and consider archival relocation.

- Hue color wheel image likely unused
  - Image defined in [hue_wheel.c](firmware/src/assets/images/hue_wheel.c:509).
  - No LVGL declaration or usage in code was found; the only other hit is a member variable name in [hue.h](firmware/src/apps/light_dimmer/pages/hue.h:14), not an image symbol usage. Recommendation: mark as unused; retain for possible future use, or move to an archive assets folder.

- Page manager stub translation unit with odd filename
  - [ page_manager.cpp](firmware/src/display/ page_manager.cpp:1) contains only a single include of the header. The primary implementation is header-only templates: [BasePage](firmware/src/display/page_manager.h:7), [PageManager<T>](firmware/src/display/page_manager.h:53). Recommendation: classify this stub as redundant; the leading-space filename suggests it may have been accidentally created.

- Potential filename anomaly in fonts
  - [aktivgrotesk_regular_12pt _8bpp.c](firmware/src/assets/fonts/AktivGrotesk/aktivgrotesk_regular_12pt _8bpp.c:1) contains an extra space before “_8bpp” in the filename. Symbols appear consistent with [LV_FONT_CUSTOM_DECLARE](firmware/src/display/lv_conf.h:380), but the file naming is irregular. Recommendation: keep as-is for now; consider normalizing filename in a future non-breaking change.

2) Obsolete/stale or archived code
- Archived firmware features not compiled
  - [firmware/not_reimplemented](firmware/not_reimplemented): [3d_printer_chamber.*](firmware/not_reimplemented/3d_printing_chamber/3d_printer_chamber.cpp:1), [music.*](firmware/not_reimplemented/music/music.cpp:1). These are not under [src_dir](platformio.ini:13) and thus not built. Recommendation: explicitly mark folder as archived/experimental to avoid confusion.

- Legacy PlatformIO environment
  - [env:seedlabs_legacy](platformio.ini:184) defines older pin mappings and reduced features. Recommendation: keep but document as deprecated; ensure CI doesn’t attempt to build it unless explicitly intended.

3) Generated or binary artifacts checked-in or present in tree
- Zipped archives in firmware sources
  - [apps.zip](firmware/src/apps.zip), [components.zip](firmware/src/components.zip). No code/build references located; presence within src is atypical. Recommendation: classify as “historical artifacts”; move to an archive folder in a future non-destructive reorg.

- Large logs and binary archives in repository root
  - Example device log: [smartknob_raw_20250902_232303.log](smartknob_raw_20250902_232303.log)
  - Binary archive: [smartknob-connection.7z](smartknob-connection.7z)
  - Recommendation: classify as artifacts; consider relocating to a top-level /artifacts or /logs folder in a future reorg and optionally ignore via .gitignore patterns in a non-destructive change.

- Extensive client-side logs in Python client
  - Numerous logs at [smartknob-connection2](smartknob-connection2): e.g., [smartknob_multiple_choice_20250901_124341.log](smartknob-connection2/smartknob_multiple_choice_20250901_124341.log). Recommendation: similar archival strategy; consider a /smartknob-connection2/logs folder (exists) and ignoring *.log.

- Local virtual environment (likely)
  - Evidence of a checked-in or present venv under [smartknob-connection2/venv](smartknob-connection2/venv/Lib/site-packages/pygments/lexers/_mapping.py:555). Recommendation: treat as local environment artifact; add to ignore if not intentionally tracked.

4) CI/config drift and quality-of-life issues
- GitHub Actions path filters likely incorrect for nanopb
  - [pio.yml](.github/workflows/pio.yml:6) includes 'thirdparty/nanopb/**' at repo root; actual submodule path is under [proto/thirdparty/nanopb](proto/thirdparty/nanopb/README.md:1). Recommendation: update filters to 'proto/**' and/or 'proto/thirdparty/nanopb/**' in a future change.

- Actions versions are outdated
  - [actions/checkout@v2](.github/workflows/pio.yml:25), [actions/setup-python@v2](.github/workflows/pio.yml:42); similarly in [release.yml](.github/workflows/release.yml:14,42). Recommendation: plan bump to supported major versions (v4/v5) and test.

- Release workflow specifics
  - [release.yml](.github/workflows/release.yml:63) zips .bin/.elf from the GA release environment; ensure any path assumptions match current PIO outputs and the SSH private dependency [git@github.com:SeedLabs-it/skdk-ota-pro.git](platformio.ini:169) is available in CI context (already injected via [SKDK_OTA_PRO_PRIVKEY](.github/workflows/release.yml:19)).

- PlatformIO configuration
  - Default environment [seedlabs_devkit](platformio.ini:19) is active and consistent with board [esp32-s3-devkitc-1-n16r8v](boards/esp32-s3-devkitc-1-n16r8v.json:1). Some commented flags annotated as “not certain why” remain (e.g., [FASTLED masks](platformio.ini:117)); consider revisiting in future tidy-ups.

5) Tests: hardware dependence, artifacts, and structure
- Hardware-dependent tests in Python client
  - Examples include [tests/test_physical_working.py](smartknob-connection2/tests/test_physical_working.py), [tests/test_physical_working_with_raw_logging.py](smartknob-connection2/tests/test_physical_working_with_raw_logging.py), and variants for toggle/multiple choice. These likely require a connected device and generate logs like [tests/smartknob_multiple_choice_20250901_112618.log](smartknob-connection2/tests/smartknob_multiple_choice_20250901_112618.log).
  - Recommendation: mark with pytest markers to skip in CI by default (e.g., “hardware” marker) and separate smoke/unit tests that run on CI.

- Ad-hoc scripts in tests folder
  - [tests/use_toggle_button.py](smartknob-connection2/tests/use_toggle_button.py) appears more like an example/integration script than a unit test. Recommendation: move to examples or e2e/it tests category in a future reorg.

6) Duplications and multi-language protobuf structure
- Protobuf sources and targets
  - Canonical .proto files under [proto](proto/smartknob.proto), [proto](proto/settings.proto).
  - Firmware nanopb outputs at [firmware/src/proto/proto_gen](firmware/src/proto/proto_gen/settings.pb.h:1).
  - Python generated files in [smartknob-connection2/smartknob/proto_gen](smartknob-connection2/smartknob/proto_gen/__init__.py:1).
  - A fallback [nanopb.proto](smartknob-connection2/protobuf/nanopb.proto:1) exists for the Python generator; acceptable duplication for tooling resilience.

- References/web
  - Separate proto copies exist under the web reference app ([settings.proto](References/smartknob-web/src/proto/settings.proto:1)) which is in [References](References/smartknob-web/README.md:1). As it’s sandboxed in References, keep but note divergence risk; ideally point tooling to the canonical proto.

7) Image assets usage audit highlights
- App icons actively used
  - Climate: [x80_thermostat](firmware/src/apps/climate/climate.cpp:33), [x40_thermostat](firmware/src/apps/climate/climate.cpp:34), plus 20px mode icons [x20_mode_auto](firmware/src/apps/climate/climate.cpp:72), [x20_mode_cool](firmware/src/apps/climate/climate.cpp:73), [x20_mode_heat](firmware/src/apps/climate/climate.cpp:74), [x20_mode_air](firmware/src/apps/climate/climate.cpp:75).
  - Light dimmer: [x80_light_outline](firmware/src/apps/light_dimmer/light_dimmer.cpp:19), [x40_light_outline](firmware/src/apps/light_dimmer/light_dimmer.cpp:20).
  - Stopwatch: [x80_timer](firmware/src/apps/stopwatch/stopwatch.cpp:45), [x40_timer](firmware/src/apps/stopwatch/stopwatch.cpp:46).
  - Switch: [x80_lightbulb_outline](firmware/src/apps/switch/switch.cpp:29), [x40_lightbulb_outline](firmware/src/apps/switch/switch.cpp:30), [x80_lightbulb_filled](firmware/src/apps/switch/switch.cpp:31), [x80_toggle_switch_off](firmware/src/apps/switch/switch.cpp:39), [x80_toggle_switch_on](firmware/src/apps/switch/switch.cpp:42).
  - Settings: [x80_settings](firmware/src/apps/settings/settings.cpp:27), [x40_settings](firmware/src/apps/settings/settings.cpp:28).
  - Blinds: [x80_blind](firmware/src/apps/blinds/blinds.cpp:28), [x40_blind](firmware/src/apps/blinds/blinds.cpp:29).
- Branding image present
  - [logo_main_gradient_transp](firmware/src/assets/images/skdk/logo_main_gradient_transp.c:220) exists; direct usage sites not captured in search. Keep.

Non-destructive recommendations (future actions; audit-only here)
- Orphans and archives
  - Archive OLD fonts and clearly label as deprecated; keep available but out of the default build search path.
  - Move firmware src-embedded zip files ([apps.zip](firmware/src/apps.zip), [components.zip](firmware/src/components.zip)) to an /archives or /artifacts folder.
  - If confirmed unused, relocate [hue_wheel.c](firmware/src/assets/images/hue_wheel.c:509) to an archive assets folder.

- Naming and hygiene
  - Normalize the leading-space filename [ page_manager.cpp](firmware/src/display/ page_manager.cpp:1) and consider removing the no-op TU since [PageManager<T>](firmware/src/display/page_manager.h:53) and [BasePage](firmware/src/display/page_manager.h:7) are header-only.
  - Consider normalizing [aktivgrotesk_regular_12pt _8bpp.c](firmware/src/assets/fonts/AktivGrotesk/aktivgrotesk_regular_12pt _8bpp.c:1) filename.

- CI and automation
  - Fix nanopb path filters in [pio.yml](.github/workflows/pio.yml:6) to include 'proto/**' and 'proto/thirdparty/nanopb/**'.
  - Bump Actions to latest majors and validate.
  - Add pytest markers to segregate hardware-dependent tests; keep example scripts out of test discovery.

- .gitignore proposal (not applied)
  - Add patterns to ignore logs, local envs, and binary archives:
    - *.log, /smartknob-connection2/*.log, /smartknob-connection2/logs/*
    - smartknob-connection2/venv/
    - *.7z, *.zip
  - Keep existing entries like [.pio/](.gitignore:19) and [__pycache__](.gitignore:41).

Inventory summary
- Safe-to-archive candidates: OLD fonts, firmware src zips, hue_wheel image (pending confirmation), page_manager.cpp stub.
- Stale/legacy: not_reimplemented modules, seedlabs_legacy env (retain with deprecation note).
- Artifacts/binaries/logs: repo-root logs and archives, extensive client logs, potential venv.
- CI drift: nanopb path filter mismatch, older actions versions.
- Duplications: acceptable for tooling/web references; document canonical proto source as [proto/*.proto](proto/smartknob.proto:1).