from __future__ import annotations

# Stand-alone NiceGUI prototype for the SmartKnob UI wireframe.
# No SmartKnob libraries are used; this only mimics the layout and behavior.

from nicegui import app, ui
import random
import time
from typing import Callable, Optional
import copy
# global callbacks to refresh parts of the UI (set inside index())
_refresh_status: Optional[Callable[[], None]] = None
_refresh_state_box: Optional[Callable[[], None]] = None
_refresh_value_inputs: Optional[Callable[[], None]] = None
_refresh_mc_list: Optional[Callable[[], None]] = None
_refresh_component_tiles: Optional[Callable[[], None]] = None
# preset list refreshers by category (filled inside index)
_refresh_preset_lists: dict[str, Callable[[], None]] = {}
# right column status chip to mirror header styling
_status_chip_right = None
_refresh_preset_lists: dict[str, Callable[[], None]] = {}
_status_chip_right = None  # consistent status chip in State panel
_refresh_drawer_btn: Optional[Callable[[], None]] = None  # updates mini drawer toggle icon
# refreshers for preset lists by category (filled in index())
_refresh_preset_lists: dict[str, Callable[[], None]] = {}
# right column status chip to mirror header styling
_status_chip_right = None

# ---------------------------
# Storage helpers (per user)
# ---------------------------

def init_user_storage() -> dict:
    u = app.storage.user  # Observable per-user storage (reactive dict)
    u.setdefault('connected', False)
    u.setdefault('selected_component', 'Multiple choice')  # or 'Toggle'
    u.setdefault('general_detent', 0.5)
    u.setdefault('general_bg', '#FFFFFF')
    u.setdefault('mc_values', [
        {'id': 1, 'name': 'RAO',  'detent': 0.5, 'background': '#FFFFFF'},
        {'id': 2, 'name': 'Cran', 'detent': 0.5, 'background': '#FFFFFF'},
        {'id': 3, 'name': 'LAO',  'detent': 0.5, 'background': '#FFFFFF'},
    ])
    # name of selected multiple choice entry
    u.setdefault('mc_selected', 'Cran')
    u.setdefault('nonce', 0.0)
    u.setdefault('right_drawer_open', False)

    # preset storage (mock)
    u.setdefault('presets_by_category', {
        'Procedure Angles': ['Default Angles'],
        'Exposure suggestions': ['Default Exposure'],
    })
    u.setdefault('preset_catalog', {
        'Default Angles': [
            {'id': 1, 'name': 'RAO', 'detent': 0.5, 'background': '#FFFFFF'},
            {'id': 2, 'name': 'Cran', 'detent': 0.5, 'background': '#FFFFFF'},
            {'id': 3, 'name': 'LAO', 'detent': 0.5, 'background': '#FFFFFF'},
        ],
        'Default Exposure': [
            {'id': 1, 'name': 'Low', 'detent': 0.3, 'background': '#E8F5E9'},
            {'id': 2, 'name': 'Medium', 'detent': 0.5, 'background': '#FFFDE7'},
            {'id': 3, 'name': 'High', 'detent': 0.7, 'background': '#FFEBEE'},
        ],
    })
    u.setdefault('preset_selected', {
        'Procedure Angles': None,
        'Exposure suggestions': None,
    })
    return u


def get_selected_value(u: dict) -> dict:
    for v in u['mc_values']:
        if v['name'] == u['mc_selected']:
            return v
    return u['mc_values'][0] if u['mc_values'] else {'id': 0, 'name': '', 'detent': 0.0, 'background': '#FFFFFF'}


# ---------------------------
# Page
# ---------------------------

@ui.page('/')
def index() -> None:
    global _refresh_status, _refresh_state_box, _refresh_value_inputs, _refresh_mc_list, _refresh_component_tiles, _refresh_preset_lists, _status_chip_right
    u = init_user_storage()

    # ---------------------------
    # Right drawer with tabs
    # ---------------------------
    # Removed floating drawer toggle; use header button instead to reduce clutter

    # use only the header button to toggle the drawer (no floating chevron)
    with ui.right_drawer(value=u['right_drawer_open']).classes('bg-grey-1') as right_drawer:
        right_drawer.bind_value(app.storage.user, 'right_drawer_open')
        with ui.tabs().props('inline-labels') as drawer_tabs:
            t_proto = ui.tab('protobuf messages')
            t_raw = ui.tab('Raw logging')
        with ui.tab_panels(drawer_tabs).classes('w-96'):
            with ui.tab_panel(t_proto):
                ui.label('protobuf messages').classes('text-caption text-grey-7')
                proto_log = ui.log(max_lines=1000).classes('h-[500px]')
            with ui.tab_panel(t_raw):
                ui.label('raw logging').classes('text-caption text-grey-7')
                raw_log = ui.log(max_lines=1000).classes('h-[500px]')

    # ---------------------------
    # Header (top bar)
    # ---------------------------
    with ui.header().classes('items-center justify-between'):
        with ui.row().classes('items-center gap-2'):
            ui.button('Connect', on_click=lambda: do_connect(u)).props('unelevated')
            ui.button('Disconnect', on_click=lambda: do_disconnect(u)).props('unelevated')
            ui.separator().props('vertical').classes('mx-1')
            ui.button('Reset', on_click=lambda: do_reset(u)).props('unelevated color=negative')
        with ui.row().classes('items-center gap-2'):
            status = ui.chip('Disconnected').classes('text-white').props('color=negative')
            def refresh_status():
                if u['connected']:
                    status.set_text('Connected'); status.props('color=positive')
                    if _status_chip_right is not None:
                        _status_chip_right.set_text('Connected'); _status_chip_right.props('color=positive')
                else:
                    status.set_text('Disconnected'); status.props('color=negative')
                    if _status_chip_right is not None:
                        _status_chip_right.set_text('Disconnected'); _status_chip_right.props('color=negative')
            refresh_status()
            _refresh_status = refresh_status
            ui.button('protobuf / logging', on_click=lambda: toggle_drawer(u)).props('outline')

    # ---------------------------
    # Components selection (full width)
    # ---------------------------
    with ui.card().classes('w-full'):
        ui.label('Components').classes('text-subtitle1 font-semibold')
        ui.separator()
        # compact floating drawer toggle to replace previous chevron (less clumsy)
        drawer_btn = ui.button('', on_click=lambda: toggle_drawer(u)) \
            .props('round fab-mini color=primary icon=chevron_right').classes('fixed right-3 top-1/2 -translate-y-1/2 z-40')
        def refresh_drawer_button():
            # show chevron direction based on drawer state
            drawer_btn.props('icon=chevron_left' if u['right_drawer_open'] else 'icon=chevron_right')
        _refresh_drawer_btn = refresh_drawer_button
        tiles_row = ui.row().classes('w-full items-stretch gap-4')

        def render_component_tiles():
            tiles_row.clear()
            with tiles_row:
                def tile(label: str, icon: str):
                    selected = (u['selected_component'] == label)
                    with ui.card().classes(
                        f'w-80 h-40 cursor-pointer items-center justify-center bg-grey-1 {"border-2 border-primary" if selected else "border"}'
                    ).on('click', lambda e, name=label: set_component(u, name)):
                        ui.icon(icon).classes('text-4xl')
                        ui.label(label).classes('text-subtitle1')
                tile('Toggle', 'toggle_on')
                tile('Multiple choice', 'format_list_bulleted')
        render_component_tiles()
        _refresh_component_tiles = render_component_tiles

    # ---------------------------
    # Main 3-column layout
    # ---------------------------
    with ui.row().classes('w-full items-start q-gutter-md px-3 py-2 flex-nowrap justify-between min-h-[calc(100vh-240px)]'):

        # 1) LEFT COLUMN
        with ui.column().classes('basis-1/3 min-w-[320px] max-w-[520px] flex-1 gap-3'):

            # Presets
            with ui.card().classes('h-[calc(100vh-320px)] overflow-y-auto'):
                presets_title = ui.label(f'Presets – {u["selected_component"]}').classes('text-subtitle1 font-semibold')
                presets_title.bind_text_from(app.storage.user, 'selected_component', lambda v: f'Presets – {v}')
                ui.separator()
                with ui.tabs().props('inline-labels') as presets_tabs:
                    tab_proc = ui.tab('Procedure Angles')
                    tab_exp = ui.tab('Exposure suggestions')

                def render_preset_list(category: str):
                    container = ui.column().classes('w-full gap-1 max-h-64 overflow-y-auto')

                    def fill():
                        container.clear()
                        names = app.storage.user.get('presets_by_category', {}).get(category, [])
                        sel = app.storage.user.get('preset_selected', {}).get(category)
                        with container:
                            for name in names:
                                selected = (sel == name)
                                btn = ui.button(
                                    name,
                                    on_click=lambda e, n=name: on_select_preset(u, category, n),
                                ).props('outline').classes('w-full justify-start')
                                if selected:
                                    btn.classes('bg-grey-3')
                            with ui.row().classes('items-center gap-2 pt-2'):
                                new_name = ui.input(placeholder='New preset name').props('dense').classes('flex-1')
                                ui.button(
                                    'Add from current',
                                    on_click=lambda: (add_preset(u, category, new_name.value), _refresh_preset_lists.get(category, lambda: None)()),
                                ).props('unelevated')
                                ui.button(
                                    'Delete selected',
                                    on_click=lambda: (delete_preset(u, category), _refresh_preset_lists.get(category, lambda: None)()),
                                ).props('outline color=negative')
                    fill()
                    _refresh_preset_lists[category] = fill

                with ui.tab_panels(presets_tabs).classes('w-full'):
                    with ui.tab_panel(tab_proc):
                        render_preset_list('Procedure Angles')
                    with ui.tab_panel(tab_exp):
                        render_preset_list('Exposure suggestions')

        # 2) MIDDLE COLUMN
        with ui.column().classes('basis-1/3 min-w-[320px] max-w-[520px] flex-1 gap-3'):
            with ui.card().classes('h-[calc(100vh-320px)] overflow-y-auto'):
                ui.label('Settings').classes('text-subtitle1 font-semibold')
                ui.separator()

                # General settings
                ui.label('General settings').classes('text-body1 font-semibold')
                with ui.row().classes('items-center gap-3'):
                    ui.label('Detent')
                    detent_slider = ui.slider(min=0.0, max=1.0, step=0.01, value=u['general_detent'])
                    detent_slider.classes('w-48')
                    detent_slider.bind_value(app.storage.user, 'general_detent')
                    ui.label().bind_text_from(app.storage.user, 'general_detent', lambda v: f'{float(v):.2f}')
                with ui.row().classes('items-center gap-3'):
                    ui.label('Background')
                    bg_input = ui.input(value=u['general_bg']).props('type=color dense')
                    bg_input.bind_value(app.storage.user, 'general_bg')

                ui.separator().classes('my-2')

                # Multiple choice values
                ui.label('Multiple choice values').classes('text-body1 font-semibold')

                # Render list of multiple choice values as buttons (scrollable when needed)
                mc_container = ui.column().classes('w-full gap-1 max-h-64 overflow-y-auto')

                def render_mc_list():
                    mc_container.clear()
                    with mc_container:
                        for v in u['mc_values']:
                            is_sel = (v['name'] == u['mc_selected'])
                            btn = ui.button(
                                v['name'],
                                on_click=lambda e, vv=v: on_mc_select(u, vv['name']),
                            ).props('outline').classes('w-full justify-start')
                            if is_sel:
                                btn.classes('bg-grey-3')
                render_mc_list()
                _refresh_mc_list = render_mc_list

                with ui.row().classes('gap-2 pt-2'):
                    # Add dialog
                    with ui.dialog() as add_dialog, ui.card().classes('w-96'):
                        ui.label('Add value').classes('text-subtitle1')
                        name_new = ui.input(label='Name').props('dense outlined')
                        detent_new = ui.slider(min=0.0, max=1.0, step=0.01, value=0.5)
                        bg_new = ui.input(label='Background').props('type=color dense outlined')
                        with ui.row().classes('justify-end gap-2 pt-2'):
                            ui.button('Cancel', on_click=add_dialog.close).props('flat')
                            ui.button('Create', on_click=lambda: (add_mc_value(u, name_new.value, detent_new.value, bg_new.value), add_dialog.close())).props('unelevated color=primary')

                    ui.button('Add value', on_click=add_dialog.open).props('unelevated')
                    ui.button('Delete selected', on_click=lambda: delete_selected_mc_value(u)).props('outline color=negative')

                ui.separator().classes('my-2')

                # Value settings, bound to selected MC entry
                ui.label('Value settings').classes('text-body1 font-semibold')

                selected = get_selected_value(u)
                name_input = ui.input(
                    label='Name',
                    value=selected['name'],
                    on_change=lambda e: update_selected_value(u, 'name', e.value),
                ).props('dense outlined')
                detent_number = ui.number(
                    label='Detent',
                    value=float(selected['detent']),
                    step=0.01,
                    min=0,
                    max=1,
                    on_change=lambda e: update_selected_value(
                        u, 'detent', float(e.value) if e.value is not None else 0.0
                    ),
                ).props('dense outlined')
                bg_value = ui.input(
                    label='Background',
                    value=selected['background'],
                    on_change=lambda e: update_selected_value(u, 'background', e.value),
                ).props('type=color dense outlined')

                def refresh_value_inputs():
                    s = get_selected_value(u)
                    name_input.value = s['name']
                    detent_number.value = float(s['detent'])
                    bg_value.value = s['background']
                # expose so other handlers can call it
                _refresh_value_inputs = refresh_value_inputs

        # 3) RIGHT COLUMN
        with ui.column().classes('basis-1/3 min-w-[320px] max-w-[520px] flex-1 gap-3'):
            with ui.card().classes('h-[calc(100vh-320px)] overflow-y-auto'):
                ui.label('State').classes('text-subtitle1 font-semibold')
                ui.separator()
                with ui.row().classes('items-center justify-between w-full'):
                    ui.button('Send component', on_click=lambda: send_component(u, proto_log, raw_log)).props('unelevated color=primary')
                    # status chip consistent with header
                    status_chip_r = ui.chip('Disconnected').classes('text-white').props('color=negative')
                    # store global reference for updates in connect/disconnect/reset
                    global _status_chip_right
                    _status_chip_right = status_chip_r
                    # initial styling (text bound, color via helper)
                    status_chip_r.bind_text_from(app.storage.user, 'connected', lambda v: 'Connected' if v else 'Disconnected')

                ui.separator().classes('my-2')

                # live info box, clear label/value distinction
                with ui.card().classes('bg-blue-1 w-full'):
                    def pair_row(lbl: str, val: str):
                        with ui.row().classes('items-center justify-between w-full'):
                            ui.label(lbl).classes('text-grey-7')
                            return ui.label(val).classes('font-medium')
                    _v_value = pair_row('Value', get_selected_value(u)['name'])
                    _v_id = pair_row('ID', str(get_selected_value(u)['id']))
                    _v_nonce = pair_row('Nonce', str(u['nonce']))

                    def refresh_state_box():
                        s = get_selected_value(u)
                        _v_value.set_text(s['name'])
                        _v_id.set_text(str(s['id']))
                        _v_nonce.set_text(str(u['nonce']))
                    _refresh_state_box = refresh_state_box

    # Initial refresh of dependent UI elements
    if _refresh_status:
        _refresh_status()
    if _refresh_state_box:
        _refresh_state_box()
    if _refresh_value_inputs:
        _refresh_value_inputs()
    if _refresh_mc_list:
        _refresh_mc_list()
    if _refresh_component_tiles:
        _refresh_component_tiles()
    if _refresh_drawer_btn:
        _refresh_drawer_btn()


# ---------------------------
# Actions / Handlers
# ---------------------------

def toggle_drawer(u: dict) -> None:
    u['right_drawer_open'] = not u['right_drawer_open']
    try:
        if _refresh_drawer_btn:
            _refresh_drawer_btn()
    except Exception:
        pass


def do_connect(u: dict) -> None:
    u['connected'] = True
    # update chips
    try:
        if _refresh_status:
            _refresh_status()
        if _status_chip_right is not None:
            if u['connected']:
                _status_chip_right.set_text('Connected'); _status_chip_right.props('color=positive')
            else:
                _status_chip_right.set_text('Disconnected'); _status_chip_right.props('color=negative')
    except Exception:
        pass


def do_disconnect(u: dict) -> None:
    u['connected'] = False
    try:
        if _refresh_status:
            _refresh_status()
        if _status_chip_right is not None:
            if u['connected']:
                _status_chip_right.set_text('Connected'); _status_chip_right.props('color=positive')
            else:
                _status_chip_right.set_text('Disconnected'); _status_chip_right.props('color=negative')
    except Exception:
        pass


def do_reset(u: dict) -> None:
    # reset to defaults similar to init
    u['general_detent'] = 0.5
    u['general_bg'] = '#FFFFFF'
    u['selected_component'] = 'Multiple choice'
    u['mc_values'] = [
        {'id': 1, 'name': 'RAO',  'detent': 0.5, 'background': '#FFFFFF'},
        {'id': 2, 'name': 'Cran', 'detent': 0.5, 'background': '#FFFFFF'},
        {'id': 3, 'name': 'LAO',  'detent': 0.5, 'background': '#FFFFFF'},
    ]
    u['mc_selected'] = 'Cran'
    u['nonce'] = 0.0
    try:
        if _refresh_value_inputs:
            _refresh_value_inputs()
        if _refresh_state_box:
            _refresh_state_box()
        if _refresh_status:
            _refresh_status()
        if _refresh_mc_list:
            _refresh_mc_list()
        if _status_chip_right is not None:
            if u['connected']:
                _status_chip_right.set_text('Connected'); _status_chip_right.props('color=positive')
            else:
                _status_chip_right.set_text('Disconnected'); _status_chip_right.props('color=negative')
    except Exception:
        pass


def set_component(u: dict, name: str) -> None:
    u['selected_component'] = name
    if _refresh_component_tiles:
        _refresh_component_tiles()


def on_mc_select(u: dict, name: str) -> None:
    if not name:
        return
    u['mc_selected'] = name
    try:
        if _refresh_value_inputs:
            _refresh_value_inputs()
        if _refresh_state_box:
            _refresh_state_box()
        if _refresh_mc_list:
            _refresh_mc_list()
    except Exception:
        pass


def update_selected_value(u: dict, key: str, value) -> None:
    # write into the selected dictionary
    for v in u['mc_values']:
        if v['name'] == u['mc_selected']:
            v[key] = value
            # if the name changed, keep selection by new name
            if key == 'name':
                u['mc_selected'] = value
            break
    try:
        if _refresh_state_box:
            _refresh_state_box()  # keep state panel in sync
        if _refresh_mc_list:
            _refresh_mc_list()
    except Exception:
        pass


def add_mc_value(u: dict, name: str, detent: float, background: str) -> None:
    """Append a new multiple choice value and select it."""
    name = (name or '').strip()
    if not name:
        return
    next_id = max([v['id'] for v in u.get('mc_values', [])] + [0]) + 1
    u['mc_values'].append({
        'id': next_id,
        'name': name,
        'detent': float(detent) if detent is not None else 0.0,
        'background': background or '#FFFFFF',
    })
    u['mc_selected'] = name
    if _refresh_mc_list:
        _refresh_mc_list()
    if _refresh_value_inputs:
        _refresh_value_inputs()
    if _refresh_state_box:
        _refresh_state_box()


def delete_selected_mc_value(u: dict) -> None:
    """Remove the currently selected multiple choice value (keeps at least one)."""
    vals = u.get('mc_values', [])
    if not vals or len(vals) <= 1:
        return
    sel = u.get('mc_selected')
    u['mc_values'] = [v for v in vals if v['name'] != sel]
    if u['mc_values']:
        u['mc_selected'] = u['mc_values'][0]['name']
    else:
        u['mc_selected'] = ''
    if _refresh_mc_list:
        _refresh_mc_list()
    if _refresh_value_inputs:
        _refresh_value_inputs()
    if _refresh_state_box:
        _refresh_state_box()


def apply_preset(u: dict, preset_name: str) -> None:
    """Apply a preset by name to the Multiple choice values."""
    catalog = u.get('preset_catalog', {})
    if preset_name not in catalog:
        return
    u['mc_values'] = copy.deepcopy(catalog[preset_name])
    u['mc_selected'] = u['mc_values'][0]['name'] if u['mc_values'] else ''
    if _refresh_value_inputs:
        _refresh_value_inputs()
    if _refresh_state_box:
        _refresh_state_box()
    if _refresh_mc_list:
        _refresh_mc_list()

def add_preset(u: dict, category: str, name: str) -> None:
    """Add a new preset (by copying current MC values) to the given category."""
    name = (name or '').strip()
    if not name:
        return
    catalog = u.setdefault('preset_catalog', {})
    catalog[name] = copy.deepcopy(u.get('mc_values', []))
    by_cat = u.setdefault('presets_by_category', {})
    by_cat.setdefault(category, [])
    if name not in by_cat[category]:
        by_cat[category].append(name)

def on_select_preset(u: dict, category: str, name: str) -> None:
    """Select and apply a preset in a given category."""
    sel = u.setdefault('preset_selected', {})
    sel[category] = name
    apply_preset(u, name)

def delete_preset(u: dict, category: str) -> None:
    """Delete the currently selected preset in a category."""
    sel_name = u.setdefault('preset_selected', {}).get(category)
    if not sel_name:
        return
    by_cat = u.setdefault('presets_by_category', {})
    names = by_cat.get(category, [])
    if sel_name in names:
        names.remove(sel_name)
    catalog = u.setdefault('preset_catalog', {})
    if sel_name in catalog:
        del catalog[sel_name]
    # clear selection
    u['preset_selected'][category] = None

def send_component(u: dict, proto_log: ui.log, raw_log: ui.log) -> None:
    # simulate sending and update nonce
    u['nonce'] = round(random.random() * 10, 2)
    ts = time.strftime('%H:%M:%S')
    s = get_selected_value(u)
    raw_log.push(f'[{ts}] send component: {u["selected_component"]}')
    raw_log.push(f'        value="{s["name"]}" id={s["id"]} detent={s["detent"]} bg={s["background"]}')
    proto_log.push(f'[{ts}] simulated protobuf: (component="{u["selected_component"]}", id={s["id"]}, value="{s["name"]}")')
    try:
        if _refresh_state_box:
            _refresh_state_box()
    except Exception:
        pass


# ---------------------------
# Run app
# ---------------------------

if __name__ in {'__main__', '__mp_main__'}:
    # Note: on Windows, use "py Gui\\App\\main.py" (or run the VSCode task).
    # storage_secret is required when using app.storage.user
    # use different port to avoid any stale server on 8080
    ui.run(title='SmartKnob UI Prototype', storage_secret='dev-secret', port=8081)