Controls_

[Button](https://nicegui.io/documentation/button)[_link_](https://nicegui.io/documentation/section_controls#button)

This element is based on Quasar's [QBtn](https://quasar.dev/vue-components/button) component.

The color parameter accepts a Quasar color, a Tailwind color, or a CSS color. If a Quasar color is used, the button will be styled according to the Quasar theme including the color of the text. Note that there are colors like "red" being both a Quasar color and a CSS color. In such cases the Quasar color will be used.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the label of the button</td></tr><tr class="field"><th class="field-name">on_click:</th><td class="field-body">callback which is invoked when button is pressed</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">the color of the button (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: 'primary')</td></tr><tr class="field"><th class="field-name">icon:</th><td class="field-body">the name of an icon to be displayed on the button (default: <cite>None</cite>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.button('Click me!', on_click=lambda: ui.notify('You clicked me!'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Click me!

See [more...](https://nicegui.io/documentation/button)

[Button Group](https://nicegui.io/documentation/button_group)[_link_](https://nicegui.io/documentation/section_controls#button_group)

This element is based on Quasar's [QBtnGroup](https://quasar.dev/vue-components/button-group) component. You must use the same design props on both the parent button group and the children buttons.

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.button_group():     ui.button('One', on_click=lambda: ui.notify('You clicked Button 1!'))     ui.button('Two', on_click=lambda: ui.notify('You clicked Button 2!'))     ui.button('Three', on_click=lambda: ui.notify('You clicked Button 3!'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

OneTwoThree

See [more...](https://nicegui.io/documentation/button_group)

[Dropdown Button](https://nicegui.io/documentation/button_dropdown)[_link_](https://nicegui.io/documentation/section_controls#dropdown_button)

This element is based on Quasar's [QBtnDropDown](https://quasar.dev/vue-components/button-dropdown) component.

The color parameter accepts a Quasar color, a Tailwind color, or a CSS color. If a Quasar color is used, the button will be styled according to the Quasar theme including the color of the text. Note that there are colors like "red" being both a Quasar color and a CSS color. In such cases the Quasar color will be used.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the label of the button</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">if the dropdown is open or not (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">on_value_change:</th></tr><tr class="field"><td> </td><td class="field-body">callback which is invoked when the dropdown is opened or closed</td></tr><tr class="field"><th class="field-name">on_click:</th><td class="field-body">callback which is invoked when button is pressed</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">the color of the button (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: 'primary')</td></tr><tr class="field"><th class="field-name">icon:</th><td class="field-body">the name of an icon to be displayed on the button (default: <cite>None</cite>)</td></tr><tr class="field"><th class="field-name">auto_close:</th><td class="field-body">whether the dropdown should close automatically when an item is clicked (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name">split:</th><td class="field-body">whether to split the dropdown icon into a separate button (default: <cite>False</cite>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.dropdown_button('Open me!', auto_close=True):     ui.item('Item 1', on_click=lambda: ui.notify('You clicked item 1'))     ui.item('Item 2', on_click=lambda: ui.notify('You clicked item 2'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Open me!_arrow\_drop\_down_

See [more...](https://nicegui.io/documentation/button_dropdown)

[Floating Action Button (FAB)](https://nicegui.io/documentation/fab)[_link_](https://nicegui.io/documentation/section_controls#floating_action_button_\(fab\))

A floating action button that can be used to trigger an action. This element is based on Quasar's [QFab](https://quasar.dev/vue-components/floating-action-button#qfab-api) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">icon:</th><td class="field-body">icon to be displayed on the FAB</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">whether the FAB is already opened (default: <tt class="docutils literal">False</tt>)</td></tr><tr class="field"><th class="field-name">label:</th><td class="field-body">optional label for the FAB</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">background color of the FAB (default: "primary")</td></tr><tr class="field"><th class="field-name">direction:</th><td class="field-body">direction of the FAB ("up", "down", "left", "right", default: "right")</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.fab('navigation', label='Transport'):     ui.fab_action('train', on_click=lambda: ui.notify('Train'))     ui.fab_action('sailing', on_click=lambda: ui.notify('Boat'))     ui.fab_action('rocket', on_click=lambda: ui.notify('Rocket'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

_navigation__close_

Transport

_train__sailing__rocket_

See [more...](https://nicegui.io/documentation/fab)

[Badge](https://nicegui.io/documentation/badge)[_link_](https://nicegui.io/documentation/section_controls#badge)

A badge element wrapping Quasar's [QBadge](https://quasar.dev/vue-components/badge) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the initial value of the text field</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">the color name for component (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: "primary")</td></tr><tr class="field"><th class="field-name">text_color:</th><td class="field-body">text color (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: <cite>None</cite>)</td></tr><tr class="field"><th class="field-name">outline:</th><td class="field-body">use 'outline' design (colored text and borders only) (default: False)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.button('Click me!', on_click=lambda: badge.set_text(int(badge.text) + 1)):     badge = ui.badge('0', color='red').props('floating')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Click me!

0

See [more...](https://nicegui.io/documentation/badge)

[Chip](https://nicegui.io/documentation/chip)[_link_](https://nicegui.io/documentation/section_controls#chip)

A chip element wrapping Quasar's [QChip](https://quasar.dev/vue-components/chip) component. It can be clickable, selectable and removable.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the initial value of the text field (default: "")</td></tr><tr class="field"><th class="field-name">icon:</th><td class="field-body">the name of an icon to be displayed on the chip (default: <cite>None</cite>)</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">the color name for component (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: "primary")</td></tr><tr class="field"><th class="field-name">text_color:</th><td class="field-body">text color (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: <cite>None</cite>)</td></tr><tr class="field"><th class="field-name">on_click:</th><td class="field-body">callback which is invoked when chip is clicked. Makes the chip clickable if set</td></tr><tr class="field"><th class="field-name">selectable:</th><td class="field-body">whether the chip is selectable (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name">selected:</th><td class="field-body">whether the chip is selected (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">on_selection_change:</th></tr><tr class="field"><td> </td><td class="field-body">callback which is invoked when the chip's selection state is changed</td></tr><tr class="field"><th class="field-name">removable:</th><td class="field-body">whether the chip is removable. Shows a small "x" button if True (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">on_value_change:</th></tr><tr class="field"><td> </td><td class="field-body">callback which is invoked when the chip is removed or unremoved</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.row().classes('gap-1'):     ui.chip('Click me', icon='ads_click', on_click=lambda: ui.notify('Clicked'))     ui.chip('Selectable', selectable=True, icon='bookmark', color='orange')     ui.chip('Removable', removable=True, icon='label', color='indigo-3')     ui.chip('Styled', icon='star', color='green').props('outline square')     ui.chip('Disabled', icon='block', color='red').set_enabled(False)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

_ads\_click_

Click me

_bookmark_

Selectable

_label_

Removable

_cancel_

_star_

Styled

_block_

Disabled

See [more...](https://nicegui.io/documentation/chip)

[Toggle](https://nicegui.io/documentation/toggle)[_link_](https://nicegui.io/documentation/section_controls#toggle)

This element is based on Quasar's [QBtnToggle](https://quasar.dev/vue-components/button-toggle) component.

The options can be specified as a list of values, or as a dictionary mapping values to labels. After manipulating the options, call update() to update the options in the UI.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">options:</th><td class="field-body">a list ['value1', ...] or dictionary <cite>{'value1':'label1', ...}</cite> specifying the options</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when selection changes</td></tr><tr class="field"><th class="field-name">clearable:</th><td class="field-body">whether the toggle can be cleared by clicking the selected option</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  toggle1 = ui.toggle([1, 2, 3], value=1) toggle2 = ui.toggle({1: 'A', 2: 'B', 3: 'C'}).bind_value(toggle1, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

123

ABC

See [more...](https://nicegui.io/documentation/toggle)

[Radio Selection](https://nicegui.io/documentation/radio)[_link_](https://nicegui.io/documentation/section_controls#radio_selection)

This element is based on Quasar's [QRadio](https://quasar.dev/vue-components/radio) component.

The options can be specified as a list of values, or as a dictionary mapping values to labels. After manipulating the options, call update() to update the options in the UI.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">options:</th><td class="field-body">a list ['value1', ...] or dictionary <cite>{'value1':'label1', ...}</cite> specifying the options</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when selection changes</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  radio1 = ui.radio([1, 2, 3], value=1).props('inline') radio2 = ui.radio({1: 'A', 2: 'B', 3: 'C'}).props('inline').bind_value(radio1, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

1

2

3

A

B

C

See [more...](https://nicegui.io/documentation/radio)

[Dropdown Selection](https://nicegui.io/documentation/select)[_link_](https://nicegui.io/documentation/section_controls#dropdown_selection)

This element is based on Quasar's [QSelect](https://quasar.dev/vue-components/select) component.

The options can be specified as a list of values, or as a dictionary mapping values to labels. After manipulating the options, call update() to update the options in the UI.

If with\_input is True, an input field is shown to filter the options.

If new\_value\_mode is not None, it implies with\_input=True and the user can enter new values in the input field. See [Quasar's documentation](https://quasar.dev/vue-components/select#the-new-value-mode-prop) for details. Note that this mode is ineffective when setting the value property programmatically.

You can use the validation parameter to define a dictionary of validation rules, e.g. {'Too long!': lambda value: len(value) < 3}. The key of the first rule that fails will be displayed as an error message. Alternatively, you can pass a callable that returns an optional error message. To disable the automatic validation on every value change, you can use the without\_auto\_validation method.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">options:</th><td class="field-body">a list ['value1', ...] or dictionary <cite>{'value1':'label1', ...}</cite> specifying the options</td></tr><tr class="field"><th class="field-name">label:</th><td class="field-body">the label to display above the selection</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when selection changes</td></tr><tr class="field"><th class="field-name">with_input:</th><td class="field-body">whether to show an input field to filter the options</td></tr><tr class="field"><th class="field-name">new_value_mode:</th><td class="field-body">handle new values from user input (default: None, i.e. no new values)</td></tr><tr class="field"><th class="field-name">multiple:</th><td class="field-body">whether to allow multiple selections</td></tr><tr class="field"><th class="field-name">clearable:</th><td class="field-body">whether to add a button to clear the selection</td></tr><tr class="field"><th class="field-name">validation:</th><td class="field-body">dictionary of validation rules or a callable that returns an optional error message (default: None for no validation)</td></tr><tr class="field"><th class="field-name">key_generator:</th><td class="field-body">a callback or iterator to generate a dictionary key for new values</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  select1 = ui.select([1, 2, 3], value=1) select2 = ui.select({1: 'One', 2: 'Two', 3: 'Three'}).bind_value(select1, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

1

_arrow\_drop\_down_

One

_arrow\_drop\_down_

See [more...](https://nicegui.io/documentation/select)

[Input Chips](https://nicegui.io/documentation/input_chips)[_link_](https://nicegui.io/documentation/section_controls#input_chips)

An input field that manages a collection of values as visual "chips" or tags. Users can type to add new chips and remove existing ones by clicking or using keyboard shortcuts.

This element is based on Quasar's [QSelect](https://quasar.dev/vue-components/select) component. Unlike a traditional dropdown selection, this variant focuses on free-form text input with chips, making it ideal for tags, keywords, or any list of user-defined values.

You can use the validation parameter to define a dictionary of validation rules, e.g. {'Too long!': lambda value: len(value) < 3}. The key of the first rule that fails will be displayed as an error message. Alternatively, you can pass a callable that returns an optional error message. To disable the automatic validation on every value change, you can use the without\_auto\_validation method.

_Added in version 2.22.0_

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">label:</th><td class="field-body">the label to display above the selection</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when selection changes</td></tr><tr class="field"><th class="field-name">new_value_mode:</th><td class="field-body">handle new values from user input (default: "toggle")</td></tr><tr class="field"><th class="field-name">clearable:</th><td class="field-body">whether to add a button to clear the selection</td></tr><tr class="field"><th class="field-name">validation:</th><td class="field-body">dictionary of validation rules or a callable that returns an optional error message (default: None for no validation)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.input_chips('My favorite chips', value=['Pringles', 'Doritos', "Lay's"])  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Pringles

_cancel_

Doritos

_cancel_

Lay's

_cancel_

My favorite chips

See [more...](https://nicegui.io/documentation/input_chips)

[Checkbox](https://nicegui.io/documentation/checkbox)[_link_](https://nicegui.io/documentation/section_controls#checkbox)

This element is based on Quasar's [QCheckbox](https://quasar.dev/vue-components/checkbox) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the label to display next to the checkbox</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">whether it should be checked initially (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when value changes</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  checkbox = ui.checkbox('check me') ui.label('Check!').bind_visibility_from(checkbox, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

check me

Check!

See [more...](https://nicegui.io/documentation/checkbox)

[Switch](https://nicegui.io/documentation/switch)[_link_](https://nicegui.io/documentation/section_controls#switch)

This element is based on Quasar's [QToggle](https://quasar.dev/vue-components/toggle) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the label to display next to the switch</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">whether it should be active initially (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback which is invoked when state is changed by the user</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  switch = ui.switch('switch me') ui.label('Switch!').bind_visibility_from(switch, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

switch me

Switch!

See [more...](https://nicegui.io/documentation/switch)

[Slider](https://nicegui.io/documentation/slider)[_link_](https://nicegui.io/documentation/section_controls#slider)

This element is based on Quasar's [QSlider](https://quasar.dev/vue-components/slider) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">min:</th><td class="field-body">lower bound of the slider</td></tr><tr class="field"><th class="field-name">max:</th><td class="field-body">upper bound of the slider</td></tr><tr class="field"><th class="field-name">step:</th><td class="field-body">step size</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">initial value to set position of the slider</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback which is invoked when the user releases the slider</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  slider = ui.slider(min=0, max=100, value=50) ui.label().bind_text_from(slider, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

50

See [more...](https://nicegui.io/documentation/slider)

[Range](https://nicegui.io/documentation/range)[_link_](https://nicegui.io/documentation/section_controls#range)

This element is based on Quasar's [QRange](https://quasar.dev/vue-components/range) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">min:</th><td class="field-body">lower bound of the range</td></tr><tr class="field"><th class="field-name">max:</th><td class="field-body">upper bound of the range</td></tr><tr class="field"><th class="field-name">step:</th><td class="field-body">step size</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">initial value to set min and max position of the range</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback which is invoked when the user releases the range</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  min_max_range = ui.range(min=0, max=100, value={'min': 20, 'max': 80}) ui.label().bind_text_from(min_max_range, 'value',                           backward=lambda v: f'min: {v["min"]}, max: {v["max"]}')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

min: 20, max: 80

See [more...](https://nicegui.io/documentation/range)

[Rating](https://nicegui.io/documentation/rating)[_link_](https://nicegui.io/documentation/section_controls#rating)

This element is based on Quasar's [QRating](https://quasar.dev/vue-components/rating) component.

_Added in version 2.12.0_

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">initial value (default: <tt class="docutils literal">None</tt>)</td></tr><tr class="field"><th class="field-name">max:</th><td class="field-body">maximum rating, number of icons (default: 5)</td></tr><tr class="field"><th class="field-name">icon:</th><td class="field-body">name of icons to be displayed (default: star)</td></tr><tr class="field"><th class="field-name">icon_selected:</th><td class="field-body">name of an icon to be displayed when selected (default: same as <tt class="docutils literal">icon</tt>)</td></tr><tr class="field"><th class="field-name">icon_half:</th><td class="field-body">name of an icon to be displayed when half-selected (default: same as <tt class="docutils literal">icon</tt>)</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">color(s) of the icons (Quasar, Tailwind, or CSS colors or <tt class="docutils literal">None</tt>, default: "primary")</td></tr><tr class="field"><th class="field-name">size:</th><td class="field-body">size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl), examples: 16px, 2rem</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when selection changes</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.rating(value=4)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

_grade_

_grade_

_grade_

_grade_

_grade_

See [more...](https://nicegui.io/documentation/rating)

[Joystick](https://nicegui.io/documentation/joystick)[_link_](https://nicegui.io/documentation/section_controls#joystick)

Create a joystick based on [nipple.js](https://yoannmoi.net/nipplejs/).

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">on_start:</th><td class="field-body">callback for when the user touches the joystick</td></tr><tr class="field"><th class="field-name">on_move:</th><td class="field-body">callback for when the user moves the joystick</td></tr><tr class="field"><th class="field-name">on_end:</th><td class="field-body">callback for when the user releases the joystick</td></tr><tr class="field"><th class="field-name">throttle:</th><td class="field-body">throttle interval in seconds for the move event (default: 0.05)</td></tr><tr class="field"><th class="field-name">options:</th><td class="field-body">arguments like <cite>color</cite> which should be passed to the <a class="reference external" href="https://github.com/yoannmoinet/nipplejs#options">underlying nipple.js library</a></td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.joystick(     color='blue', size=50,     on_move=lambda e: coordinates.set_text(f'{e.x:.3f}, {e.y:.3f}'),     on_end=lambda _: coordinates.set_text('0, 0'), ).classes('bg-slate-300') coordinates = ui.label('0, 0')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

0, 0

See [more...](https://nicegui.io/documentation/joystick)

[Text Input](https://nicegui.io/documentation/input)[_link_](https://nicegui.io/documentation/section_controls#text_input)

This element is based on Quasar's [QInput](https://quasar.dev/vue-components/input) component.

The on\_change event is called on every keystroke and the value updates accordingly. If you want to wait until the user confirms the input, you can register a custom event callback, e.g. ui.input(...).on('keydown.enter', ...) or ui.input(...).on('blur', ...).

You can use the validation parameter to define a dictionary of validation rules, e.g. {'Too long!': lambda value: len(value) < 3}. The key of the first rule that fails will be displayed as an error message. Alternatively, you can pass a callable that returns an optional error message. To disable the automatic validation on every value change, you can use the without\_auto\_validation method.

Note about styling the input: Quasar's QInput component is a wrapper around a native input element. This means that you cannot style the input directly, but you can use the input-class and input-style props to style the native input element. See the "Style" props section on the [QInput](https://quasar.dev/vue-components/input) documentation for more details.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">label:</th><td class="field-body">displayed label for the text input</td></tr><tr class="field"><th class="field-name">placeholder:</th><td class="field-body">text to show if no value is entered</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the current value of the text input</td></tr><tr class="field"><th class="field-name">password:</th><td class="field-body">whether to hide the input (default: False)</td></tr><tr class="field"><th class="field-name" colspan="2">password_toggle_button:</th></tr><tr class="field"><td> </td><td class="field-body">whether to show a button to toggle the password visibility (default: False)</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when the value changes</td></tr><tr class="field"><th class="field-name">autocomplete:</th><td class="field-body">optional list of strings for autocompletion</td></tr><tr class="field"><th class="field-name">validation:</th><td class="field-body">dictionary of validation rules or a callable that returns an optional error message (default: None for no validation)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.input(label='Text', placeholder='start typing',          on_change=lambda e: result.set_text('you typed: ' + e.value),          validation={'Input too long': lambda value: len(value) < 20}) result = ui.label()  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Text

See [more...](https://nicegui.io/documentation/input)

[Textarea](https://nicegui.io/documentation/textarea)[_link_](https://nicegui.io/documentation/section_controls#textarea)

This element is based on Quasar's [QInput](https://quasar.dev/vue-components/input) component. The type is set to textarea to create a multi-line text input.

You can use the validation parameter to define a dictionary of validation rules, e.g. {'Too long!': lambda value: len(value) < 3}. The key of the first rule that fails will be displayed as an error message. Alternatively, you can pass a callable that returns an optional error message. To disable the automatic validation on every value change, you can use the without\_auto\_validation method.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">label:</th><td class="field-body">displayed name for the textarea</td></tr><tr class="field"><th class="field-name">placeholder:</th><td class="field-body">text to show if no value is entered</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value of the field</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when the value changes</td></tr><tr class="field"><th class="field-name">validation:</th><td class="field-body">dictionary of validation rules or a callable that returns an optional error message (default: None for no validation)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.textarea(label='Text', placeholder='start typing',             on_change=lambda e: result.set_text('you typed: ' + e.value)) result = ui.label()  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Text

See [more...](https://nicegui.io/documentation/textarea)

[CodeMirror](https://nicegui.io/documentation/codemirror)[_link_](https://nicegui.io/documentation/section_controls#codemirror)

An element to create a code editor using [CodeMirror](https://codemirror.net/).

It supports syntax highlighting for over 140 languages, more than 30 themes, line numbers, code folding, (limited) auto-completion, and more.

Supported languages and themes:

- Languages: A list of supported languages can be found in the [@codemirror/language-data](https://github.com/codemirror/language-data/blob/main/src/language-data.ts) package.
- Themes: A list can be found in the [@uiw/codemirror-themes-all](https://github.com/uiwjs/react-codemirror/tree/master/themes/all) package.

At runtime, the methods supported\_languages and supported\_themes can be used to get supported languages and themes.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">initial value of the editor (default: "")</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to be executed when the value changes (default: <cite>None</cite>)</td></tr><tr class="field"><th class="field-name">language:</th><td class="field-body">initial language of the editor (case-insensitive, default: <cite>None</cite>)</td></tr><tr class="field"><th class="field-name">theme:</th><td class="field-body">initial theme of the editor (default: "basicLight")</td></tr><tr class="field"><th class="field-name">indent:</th><td class="field-body">string to use for indentation (any string consisting entirely of the same whitespace character, default: " ")</td></tr><tr class="field"><th class="field-name">line_wrapping:</th><td class="field-body">whether to wrap lines (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">highlight_whitespace:</th></tr><tr class="field"><td> </td><td class="field-body">whether to highlight whitespace (default: <cite>False</cite>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  editor = ui.codemirror('print("Edit me!")', language='Python').classes('h-32') ui.select(editor.supported_languages, label='Language', clearable=True) \     .classes('w-32').bind_value(editor, 'language') ui.select(editor.supported_themes, label='Theme') \     .classes('w-32').bind_value(editor, 'theme')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

9

1

›

print("Edit me!")

Python

Language

_cancel_

_arrow\_drop\_down_

basicLight

Theme

_arrow\_drop\_down_

See [more...](https://nicegui.io/documentation/codemirror)

[Number Input](https://nicegui.io/documentation/number)[_link_](https://nicegui.io/documentation/section_controls#number_input)

This element is based on Quasar's [QInput](https://quasar.dev/vue-components/input) component.

You can use the validation parameter to define a dictionary of validation rules, e.g. {'Too small!': lambda value: value > 3}. The key of the first rule that fails will be displayed as an error message. Alternatively, you can pass a callable that returns an optional error message. To disable the automatic validation on every value change, you can use the without\_auto\_validation method.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">label:</th><td class="field-body">displayed name for the number input</td></tr><tr class="field"><th class="field-name">placeholder:</th><td class="field-body">text to show if no value is entered</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value of the field</td></tr><tr class="field"><th class="field-name">min:</th><td class="field-body">the minimum value allowed</td></tr><tr class="field"><th class="field-name">max:</th><td class="field-body">the maximum value allowed</td></tr><tr class="field"><th class="field-name">precision:</th><td class="field-body">the number of decimal places allowed (default: no limit, negative: decimal places before the dot)</td></tr><tr class="field"><th class="field-name">step:</th><td class="field-body">the step size for the stepper buttons</td></tr><tr class="field"><th class="field-name">prefix:</th><td class="field-body">a prefix to prepend to the displayed value</td></tr><tr class="field"><th class="field-name">suffix:</th><td class="field-body">a suffix to append to the displayed value</td></tr><tr class="field"><th class="field-name">format:</th><td class="field-body">a string like "%.2f" to format the displayed value</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when the value changes</td></tr><tr class="field"><th class="field-name">validation:</th><td class="field-body">dictionary of validation rules or a callable that returns an optional error message (default: None for no validation)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.number(label='Number', value=3.1415927, format='%.2f',           on_change=lambda e: result.set_text(f'you entered: {e.value}')) result = ui.label()  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Number

See [more...](https://nicegui.io/documentation/number)

[Knob](https://nicegui.io/documentation/knob)[_link_](https://nicegui.io/documentation/section_controls#knob)

This element is based on Quasar's [QKnob](https://quasar.dev/vue-components/knob) component. The element is used to take a number input from the user through mouse/touch panning.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value (default: 0.0)</td></tr><tr class="field"><th class="field-name">min:</th><td class="field-body">the minimum value (default: 0.0)</td></tr><tr class="field"><th class="field-name">max:</th><td class="field-body">the maximum value (default: 1.0)</td></tr><tr class="field"><th class="field-name">step:</th><td class="field-body">the step size (default: 0.01)</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">knob color (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: "primary")</td></tr><tr class="field"><th class="field-name">center_color:</th><td class="field-body">color name for the center part of the component, examples: primary, teal-10</td></tr><tr class="field"><th class="field-name">track_color:</th><td class="field-body">color name for the track of the component, examples: primary, teal-10</td></tr><tr class="field"><th class="field-name">size:</th><td class="field-body">size in CSS units, including unit name or standard size name (xs|sm|md|lg|xl), examples: 16px, 2rem</td></tr><tr class="field"><th class="field-name">show_value:</th><td class="field-body">whether to show the value as text</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when the value changes</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  knob = ui.knob(0.3, show_value=True)  with ui.knob(color='orange', track_color='grey-2').bind_value(knob, 'value'):     ui.icon('volume_up')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

0.3

_volume\_up_

See [more...](https://nicegui.io/documentation/knob)

[Color Input](https://nicegui.io/documentation/color_input)[_link_](https://nicegui.io/documentation/section_controls#color_input)

This element extends Quasar's [QInput](https://quasar.dev/vue-components/input) component with a color picker.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">label:</th><td class="field-body">displayed label for the color input</td></tr><tr class="field"><th class="field-name">placeholder:</th><td class="field-body">text to show if no color is selected</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">the current color value</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when the value changes</td></tr><tr class="field"><th class="field-name">preview:</th><td class="field-body">change button background to selected color (default: False)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  label = ui.label('Change my color!') ui.color_input(label='Color', value='#000000',                on_change=lambda e: label.style(f'color:{e.value}'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Change my color!

Color

_colorize_

See [more...](https://nicegui.io/documentation/color_input)

[Color Picker](https://nicegui.io/documentation/color_picker)[_link_](https://nicegui.io/documentation/section_controls#color_picker)

This element is based on Quasar's [QMenu](https://quasar.dev/vue-components/menu) and [QColor](https://quasar.dev/vue-components/color-picker) components.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">on_pick:</th><td class="field-body">callback to execute when a color is picked</td></tr><tr class="field"><th class="field-name">value:</th><td class="field-body">whether the menu is already opened (default: <cite>False</cite>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.button(icon='colorize') as button:     ui.color_picker(on_pick=lambda e: button.classes(f'!bg-[{e.color}]'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

_colorize_

See [more...](https://nicegui.io/documentation/color_picker)

[Date Input](https://nicegui.io/documentation/date)[_link_](https://nicegui.io/documentation/section_controls#date_input)

This element is based on Quasar's [QDate](https://quasar.dev/vue-components/date) component. The date is a string in the format defined by the mask parameter.

You can also use the range or multiple props to select a range of dates or multiple dates:

ui.date({'from': '2023-01-01', 'to': '2023-01-05'}).props('range')
ui.date(\['2023-01-01', '2023-01-02', '2023-01-03'\]).props('multiple')
ui.date(\[{'from': '2023-01-01', 'to': '2023-01-05'}, '2023-01-07'\]).props('multiple range')

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial date</td></tr><tr class="field"><th class="field-name">mask:</th><td class="field-body">the format of the date string (default: 'YYYY-MM-DD')</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when changing the date</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.date(value='2023-01-01', on_change=lambda e: result.set_text(e.value)) result = ui.label()  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

2023

Sun, Jan 1

_chevron\_left_

January

_chevron\_right_

_chevron\_left_

2023

_chevron\_right_

Sun

Mon

Tue

Wed

Thu

Fri

Sat

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

See [more...](https://nicegui.io/documentation/date)

[Time Input](https://nicegui.io/documentation/time)[_link_](https://nicegui.io/documentation/section_controls#time_input)

This element is based on Quasar's [QTime](https://quasar.dev/vue-components/time) component. The time is a string in the format defined by the mask parameter.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial time</td></tr><tr class="field"><th class="field-name">mask:</th><td class="field-body">the format of the time string (default: 'HH:mm')</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to execute when changing the time</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.time(value='12:00', on_change=lambda e: result.set_text(e.value)) result = ui.label()  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

12

:

00

AM

PM

12

1

2

3

4

5

6

7

8

9

10

11

See [more...](https://nicegui.io/documentation/time)

[File Upload](https://nicegui.io/documentation/upload)[_link_](https://nicegui.io/documentation/section_controls#file_upload)

Based on Quasar's [QUploader](https://quasar.dev/vue-components/uploader) component.

Upload event handlers are called in the following order:

1. on\_begin\_upload: The client begins uploading one or more files to the server.
2. on\_upload: The upload of an individual file is complete.
3. on\_multi\_upload: The upload of all selected files is complete.

The following event handler is already called during the file selection process:

- on\_rejected: One or more files have been rejected.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">multiple:</th><td class="field-body">allow uploading multiple files at once (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name">max_file_size:</th><td class="field-body">maximum file size in bytes (default: <cite>0</cite>)</td></tr><tr class="field"><th class="field-name">max_total_size:</th><td class="field-body">maximum total size of all files in bytes (default: <cite>0</cite>)</td></tr><tr class="field"><th class="field-name">max_files:</th><td class="field-body">maximum number of files (default: <cite>0</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">on_begin_upload:</th></tr><tr class="field"><td> </td><td class="field-body">callback to execute when upload begins (<em>added in version 2.14.0</em>)</td></tr><tr class="field"><th class="field-name">on_upload:</th><td class="field-body">callback to execute for each uploaded file</td></tr><tr class="field"><th class="field-name" colspan="2">on_multi_upload:</th></tr><tr class="field"><td> </td><td class="field-body">callback to execute after multiple files have been uploaded</td></tr><tr class="field"><th class="field-name">on_rejected:</th><td class="field-body">callback to execute when one or more files have been rejected during file selection</td></tr><tr class="field"><th class="field-name">label:</th><td class="field-body">label for the uploader (default: <cite>''</cite>)</td></tr><tr class="field"><th class="field-name">auto_upload:</th><td class="field-body">automatically upload files when they are selected (default: <cite>False</cite>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.upload(on_upload=lambda e: ui.notify(f'Uploaded {e.name}')).classes('max-w-full')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

0.0B / 0.00%

_add\_box_

See [more...](https://nicegui.io/documentation/upload)

[](https://nicegui.io/imprint_privacy)
