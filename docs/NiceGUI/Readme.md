Reference, Demos and more

_NiceGUI_ Documentation

Overview

[_link_](https://nicegui.io/documentation#overview)

NiceGUI is an open-source Python library to write graphical user interfaces which run in the browser. It has a very gentle learning curve while still offering the option for advanced customizations. NiceGUI follows a backend-first philosophy: It handles all the web development details. You can focus on writing Python code. This makes it ideal for a wide range of projects including short scripts, dashboards, robotics projects, IoT solutions, smart home automation, and machine learning.

How to use this guide

[_link_](https://nicegui.io/documentation#how_to_use_this_guide)

This documentation explains how to use NiceGUI. Each of the tiles covers a NiceGUI topic in detail. It is recommended to start by reading this entire introduction page, then refer to other sections as needed.

Basic concepts

[_link_](https://nicegui.io/documentation#basic_concepts)

NiceGUI provides UI _elements_ such as buttons, sliders, text, images, charts, and more. Your app assembles these components into _pages_. When the user interacts with an item on a page, NiceGUI triggers an _event_ (or _action_). You define code to _handle_ each event, such as what to do when a user clicks a button, modifies a value or operates a slider. Elements can also be bound to a _model_ (data object), which automatically updates the user interface when the model value changes.

Elements are arranged on a page using a "declarative UI" or "code-based UI". That means that you also write structures like grids, cards, tabs, carousels, expansions, menus, and other layout elements directly in code. This concept has been made popular with Flutter and SwiftUI. For readability, NiceGUI utilizes Python's `with ...` statement. This context manager provides a nice way to indent the code to resemble the layout of the UI.

Styling and appearance can be controlled in several ways. Most elements accept optional arguments for common styling and behavior changes, such as button icons or text color. Because NiceGUI is a web framework, you can change almost any appearance of an element with CSS. But elements also provide `.classes` and `.props` methods to apply Tailwind CSS and Quasar properties which are more high-level and simpler to use day-to-day after you get the hang of it.

Actions, Events and Tasks

[_link_](https://nicegui.io/documentation#actions__events_and_tasks)

NiceGUI uses an async/await event loop for concurrency which is resource-efficient and has the great benefit of not having to worry about thread safety. This section shows how to handle user input and other events like timers and keyboard bindings. It also describes helper functions to wrap long-running tasks in asynchronous functions to keep the UI responsive. Keep in mind that all UI updates must happen on the main thread with its event loop.

Implementation

[_link_](https://nicegui.io/documentation#implementation)

NiceGUI is implemented with HTML components served by an HTTP server (FastAPI), even for native windows. If you already know HTML, everything will feel very familiar. If you don't know HTML, that's fine too! NiceGUI abstracts away the details, so you can focus on creating beautiful interfaces without worrying about how they are implemented.

Running NiceGUI Apps

[_link_](https://nicegui.io/documentation#running_nicegui_apps)

There are several options for deploying NiceGUI. By default, NiceGUI runs a server on localhost and runs your app as a private web page on the local machine. When run this way, your app appears in a web browser window. You can also run NiceGUI in a native window separate from a web browser. Or you can run NiceGUI on a server that handles many clients - the website you're reading right now is served from NiceGUI.

After creating your app pages with components, you call `ui.run()` to start the NiceGUI server. Optional parameters to `ui.run` set things like the network address and port the server binds to, whether the app runs in native mode, initial window size, and many other options. The section _Configuration and Deployment_ covers the options to the `ui.run()` function and the FastAPI framework it is based on.

Customization

[_link_](https://nicegui.io/documentation#customization)

If you want more customization in your app, you can use the underlying Tailwind classes and Quasar components to control the style or behavior of your components. You can also extend the available components by subclassing existing NiceGUI components or importing new ones from Quasar. All of this is optional. Out of the box, NiceGUI provides everything you need to make modern, stylish, responsive user interfaces.

Testing

[_link_](https://nicegui.io/documentation#testing)

NiceGUI provides a comprehensive testing framework based on [pytest](https://docs.pytest.org/) which allows you to automate the testing of your user interface. You can utilize the `screen` fixture which starts a real (headless) browser to interact with your application. This is great if you have browser-specific behavior to test.

But most of the time, NiceGUI's newly introduced `user` fixture is more suited: It only simulates the user interaction on a Python level and, hence, is blazing fast. That way the classical [test pyramid](https://martinfowler.com/bliki/TestPyramid.html), where UI tests are considered slow and expensive, does not apply anymore. This can have a huge impact on your development speed, quality and confidence.

---

Map of NiceGUI

[_link_](https://nicegui.io/documentation#map-of-nicegui)

This overview shows the structure of NiceGUI. It is a map of the NiceGUI namespace and its contents. It is not exhaustive, but it gives you a good idea of what is available. An ongoing goal is to make this map more complete and to add missing links to the documentation.

#### `ui`

UI elements and other essentials to run a NiceGUI app.

- [`ui.element`](https://nicegui.io/documentation/element): base class for all UI elements
  - customization:
    - `.props()` and [`.default_props()`](https://nicegui.io/documentation/element#default_props): add Quasar props and regular HTML attributes
    - `.classes()` and [`.default_classes()`](https://nicegui.io/documentation/element#default_classes): add Quasar, Tailwind and custom HTML classes
    - [`.tailwind`](https://nicegui.io/documentation/section_styling_appearance#tailwind_css): convenience API for adding Tailwind classes
    - `.style()` and [`.default_style()`](https://nicegui.io/documentation/element#default_style): add CSS style definitions
    - [`.tooltip()`](https://nicegui.io/documentation/tooltip): add a tooltip to an element
    - [`.mark()`](https://nicegui.io/documentation/element_filter#markers): mark an element for querying with an [ElementFilter](https://nicegui.io/documentation/element_filter)
  - interaction:
    - [`.on()`](https://nicegui.io/documentation/generic_events): add Python and JavaScript event handlers
    - `.update()`: send an update to the client (mostly done automatically)
    - `.run_method()`: run a method on the client side
    - `.get_computed_prop()`: get the value of a property that is computed on the client side
  - hierarchy:
    - `with ...:` nesting elements in a declarative way
    - `__iter__`: an iterator over all child elements
    - `ancestors`: an iterator over the element's parent, grandparent, etc.
    - `descendants`: an iterator over all child elements, grandchildren, etc.
    - `slots`: a dictionary of named slots
    - `add_slot`: fill a new slot with NiceGUI elements or a scoped slot with template strings
    - [`clear`](https://nicegui.io/documentation/section_page_layout#clear_containers): remove all child elements
    - [`move`](https://nicegui.io/documentation/element#move_elements): move an element to a new parent
    - `remove`: remove a child element
    - `delete`: delete an element and all its children
    - `is_deleted`: whether an element has been deleted
- elements:
  - [`ui.aggrid`](https://nicegui.io/documentation/aggrid)
  - [`ui.audio`](https://nicegui.io/documentation/audio)
  - [`ui.avatar`](https://nicegui.io/documentation/avatar)
  - [`ui.badge`](https://nicegui.io/documentation/badge)
  - [`ui.button`](https://nicegui.io/documentation/button)
  - [`ui.button_group`](https://nicegui.io/documentation/button_group)
  - [`ui.card`](https://nicegui.io/documentation/card), `ui.card_actions`, `ui.card_section`
  - [`ui.carousel`](https://nicegui.io/documentation/carousel), `ui.carousel_slide`
  - [`ui.chat_message`](https://nicegui.io/documentation/chat_message)
  - [`ui.checkbox`](https://nicegui.io/documentation/checkbox)
  - [`ui.chip`](https://nicegui.io/documentation/chip)
  - [`ui.circular_progress`](https://nicegui.io/documentation/circular_progress)
  - [`ui.code`](https://nicegui.io/documentation/code)
  - [`ui.codemirror`](https://nicegui.io/documentation/codemirror)
  - [`ui.color_input`](https://nicegui.io/documentation/color_input)
  - [`ui.color_picker`](https://nicegui.io/documentation/color_picker)
  - [`ui.column`](https://nicegui.io/documentation/column)
  - [`ui.context_menu`](https://nicegui.io/documentation/context_menu)
  - [`ui.date`](https://nicegui.io/documentation/date)
  - [`ui.dialog`](https://nicegui.io/documentation/dialog)
  - [`ui.dropdown_button`](https://nicegui.io/documentation/button_dropdown)
  - [`ui.echart`](https://nicegui.io/documentation/echart)
  - [`ui.editor`](https://nicegui.io/documentation/editor)
  - [`ui.expansion`](https://nicegui.io/documentation/expansion)
  - [`ui.fab`](https://nicegui.io/documentation/fab), `ui.fab_action`
  - [`ui.grid`](https://nicegui.io/documentation/grid)
  - [`ui.highchart`](https://nicegui.io/documentation/highchart)
  - [`ui.html`](https://nicegui.io/documentation/html)
  - [`ui.icon`](https://nicegui.io/documentation/icon)
  - [`ui.image`](https://nicegui.io/documentation/image)
  - [`ui.input`](https://nicegui.io/documentation/input)
  - [`ui.input_chips`](https://nicegui.io/documentation/input_chips)
  - [`ui.interactive_image`](https://nicegui.io/documentation/interactive_image)
  - `ui.item`, `ui.item_label`, `ui.item_section`
  - [`ui.joystick`](https://nicegui.io/documentation/joystick)
  - [`ui.json_editor`](https://nicegui.io/documentation/json_editor)
  - [`ui.knob`](https://nicegui.io/documentation/knob)
  - [`ui.label`](https://nicegui.io/documentation/label)
  - [`ui.leaflet`](https://nicegui.io/documentation/leaflet)
  - [`ui.line_plot`](https://nicegui.io/documentation/line_plot)
  - [`ui.linear_progress`](https://nicegui.io/documentation/linear_progress)
  - [`ui.link`](https://nicegui.io/documentation/link), `ui.link_target`
  - [`ui.list`](https://nicegui.io/documentation/list)
  - [`ui.log`](https://nicegui.io/documentation/log)
  - [`ui.markdown`](https://nicegui.io/documentation/markdown)
  - [`ui.matplotlib`](https://nicegui.io/documentation/matplotlib)
  - [`ui.menu`](https://nicegui.io/documentation/menu), `ui.menu_item`
  - [`ui.mermaid`](https://nicegui.io/documentation/mermaid)
  - [`ui.notification`](https://nicegui.io/documentation/notification)
  - [`ui.number`](https://nicegui.io/documentation/number)
  - [`ui.pagination`](https://nicegui.io/documentation/pagination)
  - [`ui.plotly`](https://nicegui.io/documentation/plotly)
  - [`ui.pyplot`](https://nicegui.io/documentation/pyplot)
  - [`ui.radio`](https://nicegui.io/documentation/radio)
  - [`ui.rating`](https://nicegui.io/documentation/rating)
  - [`ui.range`](https://nicegui.io/documentation/range)
  - [`ui.restructured_text`](https://nicegui.io/documentation/restructured_text)
  - [`ui.row`](https://nicegui.io/documentation/row)
  - [`ui.scene`](https://nicegui.io/documentation/scene), [`ui.scene_view`](https://nicegui.io/documentation/scene#scene_view)
  - [`ui.scroll_area`](https://nicegui.io/documentation/scroll_area)
  - [`ui.select`](https://nicegui.io/documentation/select)
  - [`ui.separator`](https://nicegui.io/documentation/separator)
  - [`ui.skeleton`](https://nicegui.io/documentation/skeleton)
  - [`ui.slide_item`](https://nicegui.io/documentation/slide_item)
  - [`ui.slider`](https://nicegui.io/documentation/slider)
  - [`ui.space`](https://nicegui.io/documentation/space)
  - [`ui.spinner`](https://nicegui.io/documentation/spinner)
  - [`ui.splitter`](https://nicegui.io/documentation/splitter)
  - [`ui.stepper`](https://nicegui.io/documentation/stepper), `ui.step`, `ui.stepper_navigation`
  - [`ui.sub_pages`](https://nicegui.io/documentation/sub_pages)
  - [`ui.switch`](https://nicegui.io/documentation/switch)
  - [`ui.tabs`](https://nicegui.io/documentation/tabs), `ui.tab`, `ui.tab_panels`, `ui.tab_panel`
  - [`ui.table`](https://nicegui.io/documentation/table)
  - [`ui.textarea`](https://nicegui.io/documentation/textarea)
  - [`ui.time`](https://nicegui.io/documentation/time)
  - [`ui.timeline`](https://nicegui.io/documentation/timeline), `ui.timeline_entry`
  - [`ui.toggle`](https://nicegui.io/documentation/toggle)
  - [`ui.tooltip`](https://nicegui.io/documentation/tooltip)
  - [`ui.tree`](https://nicegui.io/documentation/tree)
  - [`ui.upload`](https://nicegui.io/documentation/upload)
  - [`ui.video`](https://nicegui.io/documentation/video)
- special layout [elements](https://nicegui.io/documentation/page_layout):
  - `ui.header`
  - `ui.footer`
  - `ui.drawer`, `ui.left_drawer`, `ui.right_drawer`
  - `ui.page_sticky`
- special functions and objects:
  - [`ui.add_body_html`](https://nicegui.io/documentation/section_pages_routing#add_html_to_the_page) and [`ui.add_head_html`](https://nicegui.io/documentation/section_pages_routing#add_html_to_the_page): add HTML to the body and head of the page
  - [`ui.add_css`](https://nicegui.io/documentation/add_style#add_css_style_definitions_to_the_page), [`ui.add_sass`](https://nicegui.io/documentation/add_style#add_sass_style_definitions_to_the_page) and [`ui.add_scss`](https://nicegui.io/documentation/add_style#add_scss_style_definitions_to_the_page): add CSS, SASS and SCSS to the page
  - [`ui.clipboard`](https://nicegui.io/documentation/clipboard): interact with the browser's clipboard
  - [`ui.colors`](https://nicegui.io/documentation/colors): define the main color theme for a page
  - `ui.context`: get the current UI context including the `client` and `request` objects
  - [`ui.dark_mode`](https://nicegui.io/documentation/dark_mode): get and set the dark mode on a page
  - [`ui.download`](https://nicegui.io/documentation/download): download a file to the client
  - [`ui.fullscreen`](https://nicegui.io/documentation/fullscreen): enter, exit and toggle fullscreen mode
  - [`ui.keyboard`](https://nicegui.io/documentation/keyboard): define keyboard event handlers
  - [`ui.navigate`](https://nicegui.io/documentation/navigate): let the browser navigate to another location
  - [`ui.notify`](https://nicegui.io/documentation/notification): show a notification
  - [`ui.on`](https://nicegui.io/documentation/generic_events#custom_events): register an event handler
  - [`ui.page_title`](https://nicegui.io/documentation/page_title): change the current page title
  - [`ui.query`](https://nicegui.io/documentation/query): query HTML elements on the client side to modify props, classes and style definitions
  - [`ui.run`](https://nicegui.io/documentation/run) and `ui.run_with`: run the app (standalone or attached to a FastAPI app)
  - [`ui.run_javascript`](https://nicegui.io/documentation/run#run_custom_javascript_on_the_client_side): run custom JavaScript on the client side (can use `getElement()`, `getHtmlElement()`, and `emitEvent()`)
  - [`ui.teleport`](https://nicegui.io/documentation/teleport): teleport an element to a different location in the HTML DOM
  - [`ui.timer`](https://nicegui.io/documentation/timer): run a function periodically or once after a delay
  - `ui.update`: send updates of multiple elements to the client
- decorators:
  - [`ui.page`](https://nicegui.io/documentation/page): define a page (in contrast to the automatically generated "auto-index page")
  - [`ui.refreshable`](https://nicegui.io/documentation/refreshable), `ui.refreshable_method`: define refreshable UI containers (can use [`ui.state`](https://nicegui.io/documentation/refreshable#refreshable_ui_with_reactive_state))

#### `app`

App-wide storage, mount points and lifecycle hooks.

- [`app.storage`](https://nicegui.io/documentation/storage):
  - `app.storage.tab`: stored in memory on the server, unique per tab
  - `app.storage.client`: stored in memory on the server, unique per client connected to a page
  - `app.storage.user`: stored in a file on the server, unique per browser
  - `app.storage.general`: stored in a file on the server, shared across the entire app
  - `app.storage.browser`: stored in the browser's local storage, unique per browser
- [lifecycle hooks](https://nicegui.io/documentation/section_action_events#events):
  - `app.on_connect()`: called when a client connects
  - `app.on_disconnect()`: called when a client disconnects
  - `app.on_startup()`: called when the app starts
  - `app.on_shutdown()`: called when the app shuts down
  - `app.on_exception()`: called when an exception occurs
  - `app.on_page_exception()`: called when an exception occurs while building a page
- [`app.shutdown()`](https://nicegui.io/documentation/section_action_events#shut_down_nicegui): shut down the app
- static files:
  - [`app.add_static_files()`](https://nicegui.io/documentation/section_pages_routing#add_a_directory_of_static_files), `app.add_static_file()`: serve static files
  - [`app.add_media_files()`](https://nicegui.io/documentation/section_pages_routing#add_directory_of_media_files), `app.add_media_file()`: serve media files (supports streaming)
- [`app.native`](https://nicegui.io/documentation/section_configuration_deployment#native_mode): configure the app when running in native mode

#### `html`

[Pure HTML elements](https://nicegui.io/documentation/html#other_html_elements):

`a`, `abbr`, `acronym`, `address`, `area`, `article`, `aside`, `audio`, `b`, `basefont`, `bdi`, `bdo`, `big`, `blockquote`, `br`, `button`, `canvas`, `caption`, `cite`, `code`, `col`, `colgroup`, `data`, `datalist`, `dd`, `del_`, `details`, `dfn`, `dialog`, `div`, `dl`, `dt`, `em`, `embed`, `fieldset`, `figcaption`, `figure`, `footer`, `form`, `h1`, `header`, `hgroup`, `hr`, `i`, `iframe`, `img`, `input_`, `ins`, `kbd`, `label`, `legend`, `li`, `main`, `map_`, `mark`, `menu`, `meter`, `nav`, `object_`, `ol`, `optgroup`, `option`, `output`, `p`, `param`, `picture`, `pre`, `progress`, `q`, `rp`, `rt`, `ruby`, `s`, `samp`, `search`, `section`, `select`, `small`, `source`, `span`, `strong`, `sub`, `summary`, `sup`, `svg`, `table`, `tbody`, `td`, `template`, `textarea`, `tfoot`, `th`, `thead`, `time`, `tr`, `track`, `u`, `ul`, `var`, `video`, `wbr`

#### `background_tasks`

Run async functions in the background.

- `create()`: create a background task
- `create_lazy()`: prevent two tasks with the same name from running at the same time
- `await_on_shutdown`: mark a coroutine function to be awaited during shutdown (by default all background tasks are cancelled)

#### `run`

Run IO and CPU bound functions in separate threads and processes.

- [`run.cpu_bound()`](https://nicegui.io/documentation/section_action_events#running_cpu-bound_tasks): run a CPU-bound function in a separate process
- [`run.io_bound()`](https://nicegui.io/documentation/section_action_events#running_i_o-bound_tasks): run an IO-bound function in a separate thread

#### `binding`

[Bind properties of objects to each other](https://nicegui.io/documentation/section_binding_properties).

- [`binding.BindableProperty`](https://nicegui.io/documentation/section_binding_properties#bindable_properties_for_maximum_performance): bindable properties for maximum performance
- [`binding.bindable_dataclass()`](https://nicegui.io/documentation/section_binding_properties#bindable_dataclass): create a dataclass with bindable properties
- `binding.bind()`, `binding.bind_from()`, `binding.bind_to()`: methods to bind two properties

#### `observables`

Observable collections that notify observers when their contents change.

- `ObservableCollection`: base class
- `ObservableDict`: an observable dictionary
- `ObservableList`: an observable list
- `ObservableSet`: an observable set

#### `testing`

Write automated UI tests which run in a headless browser (slow) or fully simulated in Python (fast).

- [`Screen`](https://nicegui.io/documentation/section_testing#screen_fixture) fixture: start a real (headless) browser to interact with your application
- [`User`](https://nicegui.io/documentation/section_testing#user_fixture) fixture: simulate user interaction on a Python level (fast)
