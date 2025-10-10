Action & _Events_

[Timer](https://nicegui.io/documentation/timer)[_link_](https://nicegui.io/documentation/section_action_events#timer)

One major drive behind the creation of NiceGUI was the necessity to have a simple approach to update the interface in regular intervals, for example to show a graph with incoming measurements. A timer will execute a callback repeatedly with a given interval.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">interval:</th><td class="field-body">the interval in which the timer is called (can be changed during runtime)</td></tr><tr class="field"><th class="field-name">callback:</th><td class="field-body">function or coroutine to execute when interval elapses</td></tr><tr class="field"><th class="field-name">active:</th><td class="field-body">whether the callback should be executed or not (can be changed during runtime)</td></tr><tr class="field"><th class="field-name">once:</th><td class="field-body">whether the callback is only executed once after a delay specified by <cite>interval</cite> (default: <cite>False</cite>)</td></tr><tr class="field"><th class="field-name">immediate:</th><td class="field-body">whether the callback should be executed immediately (default: <cite>True</cite>, ignored if <cite>once</cite> is <cite>True</cite>, <em>added in version 2.9.0</em>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from datetime import datetime from nicegui import ui  label = ui.label() ui.timer(1.0, lambda: label.set_text(f'{datetime.now():%X}'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

11:27:45

See [more...](https://nicegui.io/documentation/timer)

[Keyboard](https://nicegui.io/documentation/keyboard)[_link_](https://nicegui.io/documentation/section_action_events#keyboard)

Adds global keyboard event tracking.

The on\_key callback receives a KeyEventArguments object with the following attributes:

- sender: the Keyboard element

- client: the client object

- action: a KeyboardAction object with the following attributes:
  
  - keydown: whether the key was pressed
  - keyup: whether the key was released
  - repeat: whether the key event was a repeat

- key: a KeyboardKey object with the following attributes:
  
  - name: the name of the key (e.g. "a", "Enter", "ArrowLeft"; see [here](https://developer.mozilla.org/en-US/docs/Web/API/UI_Events/Keyboard_event_key_values) for a list of possible values)
  - code: the code of the key (e.g. "KeyA", "Enter", "ArrowLeft")
  - location: the location of the key (0 for standard keys, 1 for left keys, 2 for right keys, 3 for numpad keys)

- modifiers: a KeyboardModifiers object with the following attributes:
  
  - alt: whether the alt key was pressed
  - ctrl: whether the ctrl key was pressed
  - meta: whether the meta key was pressed
  - shift: whether the shift key was pressed

For convenience, the KeyboardKey object also has the following properties:

- is\_cursorkey: whether the key is a cursor (arrow) key
- number: the integer value of a number key (0-9, None for other keys)
- backspace, tab, enter, shift, control, alt, pause, caps\_lock, escape, space, page\_up, page\_down, end, home, arrow\_left, arrow\_up, arrow\_right, arrow\_down, print\_screen, insert, delete, meta, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12: whether the key is the respective key

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">on_key:</th><td class="field-body">callback to be executed when keyboard events occur.</td></tr><tr class="field"><th class="field-name">active:</th><td class="field-body">boolean flag indicating whether the callback should be executed or not (default: <tt class="docutils literal">True</tt>)</td></tr><tr class="field"><th class="field-name">repeating:</th><td class="field-body">boolean flag indicating whether held keys should be sent repeatedly (default: <tt class="docutils literal">True</tt>)</td></tr><tr class="field"><th class="field-name">ignore:</th><td class="field-body">ignore keys when one of these element types is focussed (default: <tt class="docutils literal">['input', 'select', 'button', 'textarea']</tt>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui from nicegui.events import KeyEventArguments  def handle_key(e: KeyEventArguments):     if e.key == 'f' and not e.action.repeat:         if e.action.keyup:             ui.notify('f was just released')         elif e.action.keydown:             ui.notify('f was just pressed')     if e.modifiers.shift and e.action.keydown:         if e.key.arrow_left:             ui.notify('going left')         elif e.key.arrow_right:             ui.notify('going right')         elif e.key.arrow_up:             ui.notify('going up')         elif e.key.arrow_down:             ui.notify('going down')  keyboard = ui.keyboard(on_key=handle_key) ui.label('Key events can be caught globally by using the keyboard element.') ui.checkbox('Track key events').bind_value_to(keyboard, 'active')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Key events can be caught globally by using the keyboard element.

Track key events

See [more...](https://nicegui.io/documentation/keyboard)

UI Updates

[_link_](https://nicegui.io/documentation/section_action_events#ui_updates)

NiceGUI tries to automatically synchronize the state of UI elements with the client, e.g. when a label text, an input value or style/classes/props of an element have changed. In other cases, you can explicitly call `element.update()` or `ui.update(*elements)` to update. The demo code shows both methods for a `ui.echart`, where it is difficult to automatically detect changes in the `options` dictionary.

_circle__circle__circle_

main.py

`from nicegui import ui from random import random  chart = ui.echart({     'xAxis': {'type': 'value'},     'yAxis': {'type': 'value'},     'series': [{'type': 'line', 'data': [[0, 0], [1, 1]]}], })  def add():     chart.options['series'][0]['data'].append([random(), random()])     chart.update()  def clear():     chart.options['series'][0]['data'].clear()     ui.update(chart)  with ui.row():     ui.button('Add', on_click=add)     ui.button('Clear', on_click=clear)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

AddClear

[Refreshable UI functions](https://nicegui.io/documentation/refreshable)[_link_](https://nicegui.io/documentation/section_action_events#refreshable_ui_functions)

The @ui.refreshable decorator allows you to create functions that have a refresh method. This method will automatically delete all elements created by the function and recreate them.

For decorating refreshable methods in classes, there is a @ui.refreshable\_method decorator, which is equivalent but prevents static type checking errors.

_circle__circle__circle_

main.py

`import random from nicegui import ui  numbers = []  @ui.refreshable def number_ui() -> None:     ui.label(', '.join(str(n) for n in sorted(numbers)))  def add_number() -> None:     numbers.append(random.randint(0, 100))     number_ui.refresh()  number_ui() ui.button('Add random number', on_click=add_number)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Add random number

See [more...](https://nicegui.io/documentation/refreshable)

Async event handlers

[_link_](https://nicegui.io/documentation/section_action_events#async_event_handlers)

Most elements also support asynchronous event handlers.

Note: You can also pass a `functools.partial` into the `on_click` property to wrap async functions with parameters.

_circle__circle__circle_

main.py

`import asyncio from nicegui import ui  async def async_task():     ui.notify('Asynchronous task started')     await asyncio.sleep(5)     ui.notify('Asynchronous task finished')  ui.button('start async task', on_click=async_task)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

start async task

[Generic Events](https://nicegui.io/documentation/generic_events)[_link_](https://nicegui.io/documentation/section_action_events#generic_events)

Most UI elements come with predefined events. For example, a `ui.button` like "A" in the demo has an `on_click` parameter that expects a coroutine or function. But you can also use the `on` method to register a generic event handler like for "B". This allows you to register handlers for any event that is supported by JavaScript and Quasar.

For example, you can register a handler for the `mousemove` event like for "C", even though there is no `on_mousemove` parameter for `ui.button`. Some events, like `mousemove`, are fired very often. To avoid performance issues, you can use the `throttle` parameter to only call the handler every `throttle` seconds ("D").

The generic event handler can be synchronous or asynchronous and optionally takes `GenericEventArguments` as argument ("E"). You can also specify which attributes of the JavaScript or Quasar event should be passed to the handler ("F"). This can reduce the amount of data that needs to be transferred between the server and the client.

Here you can find more information about the events that are supported:

- [https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement#events](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement#events) for HTML elements
- [https://quasar.dev/vue-components](https://quasar.dev/vue-components) for Quasar-based elements (see the "Events" tab on the individual component page)

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.row():     ui.button('A', on_click=lambda: ui.notify('You clicked the button A.'))     ui.button('B').on('click', lambda: ui.notify('You clicked the button B.')) with ui.row():     ui.button('C').on('mousemove', lambda: ui.notify('You moved on button C.'))     ui.button('D').on('mousemove', lambda: ui.notify('You moved on button D.'), throttle=0.5) with ui.row():     ui.button('E').on('mousedown', lambda e: ui.notify(e))     ui.button('F').on('mousedown', lambda e: ui.notify(e), ['ctrlKey', 'shiftKey'])  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

AB

CD

EF

See [more...](https://nicegui.io/documentation/generic_events)

Running CPU-bound tasks

[_link_](https://nicegui.io/documentation/section_action_events#running_cpu-bound_tasks)

NiceGUI provides a `cpu_bound` function for running CPU-bound tasks in a separate process. This is useful for long-running computations that would otherwise block the event loop and make the UI unresponsive. The function returns a future that can be awaited.

Note: The function needs to transfer the whole state of the passed function to the process, which is done with pickle. It is encouraged to create free functions or static methods which get all the data as simple parameters (i.e. no class or UI logic) and return the result, instead of writing it in class properties or global variables.

_circle__circle__circle_

main.py

`import time from nicegui import run, ui  def compute_sum(a: float, b: float) -> float:     time.sleep(1)  # simulate a long-running computation     return a + b  async def handle_click():     result = await run.cpu_bound(compute_sum, 1, 2)     ui.notify(f'Sum is {result}')  ui.button('Compute', on_click=handle_click)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Compute

Running I/O-bound tasks

[_link_](https://nicegui.io/documentation/section_action_events#running_i_o-bound_tasks)

NiceGUI provides an `io_bound` function for running I/O-bound tasks in a separate thread. This is useful for long-running I/O operations that would otherwise block the event loop and make the UI unresponsive. The function returns a future that can be awaited.

_circle__circle__circle_

main.py

`import httpx from nicegui import run, ui  async def handle_click():     URL = 'https://httpbin.org/delay/1'     response = await run.io_bound(httpx.get, URL, timeout=3)     ui.notify(f'Downloaded {len(response.content)} bytes')  ui.button('Download', on_click=handle_click)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Download

[Run JavaScript](https://nicegui.io/documentation/run_javascript)[_link_](https://nicegui.io/documentation/section_action_events#run_javascript)

This function runs arbitrary JavaScript code on a page that is executed in the browser. The client must be connected before this function is called. To access a client-side Vue component or HTML element by ID, use the JavaScript functions getElement() or getHtmlElement() (_added in version 2.9.0_).

If the function is awaited, the result of the JavaScript code is returned. Otherwise, the JavaScript code is executed without waiting for a response.

Note that requesting data from the client is only supported for page functions, not for the shared auto-index page.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">code:</th><td class="field-body">JavaScript code to run</td></tr><tr class="field"><th class="field-name">timeout:</th><td class="field-body">timeout in seconds (default: <cite>1.0</cite>)</td></tr><tr class="field"><th class="field-name">return:</th><td class="field-body">AwaitableResponse that can be awaited to get the result of the JavaScript code</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  @ui.page('/') def page():     def alert():         ui.run_javascript('alert("Hello!")')      async def get_date():         time = await ui.run_javascript('Date()')         ui.notify(f'Browser time: {time}')      def access_elements():         ui.run_javascript(f'getHtmlElement({label.id}).innerText += " Hello!"')      ui.button('fire and forget', on_click=alert)     ui.button('receive result', on_click=get_date)     ui.button('access elements', on_click=access_elements)     label = ui.label()  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

fire and forgetreceive resultaccess elements

See [more...](https://nicegui.io/documentation/run_javascript)

[Read and write to the clipboard](https://nicegui.io/documentation/clipboard)[_link_](https://nicegui.io/documentation/section_action_events#read_and_write_to_the_clipboard)

The following demo shows how to use `ui.clipboard.read()`, `ui.clipboard.write()` and `ui.clipboard.read_image()` to interact with the clipboard.

Because auto-index page can be accessed by multiple browser tabs simultaneously, reading the clipboard is not supported on this page. This is only possible within page-builder functions decorated with `ui.page`, as shown in this demo.

Note that your browser may ask for permission to access the clipboard or may not support this feature at all.

_circle__circle__circle_

main.py

`from nicegui import ui  @ui.page('/') async def index():     ui.button('Write Text', on_click=lambda: ui.clipboard.write('Hi!'))      async def read() -> None:         ui.notify(await ui.clipboard.read())     ui.button('Read Text', on_click=read)      async def read_image() -> None:         img = await ui.clipboard.read_image()         if not img:             ui.notify('You must copy an image to clipboard first.')         else:             image.set_source(img)     ui.button('Read Image', on_click=read_image)     image = ui.image().classes('w-72')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Write TextRead TextRead Image

See [more...](https://nicegui.io/documentation/clipboard)

Events

[_link_](https://nicegui.io/documentation/section_action_events#events)

You can register coroutines or functions to be called for the following events:

- `app.on_startup`: called when NiceGUI is started or restarted
- `app.on_shutdown`: called when NiceGUI is shut down or restarted
- `app.on_connect`: called for each client which connects (optional argument: nicegui.Client)
- `app.on_disconnect`: called for each client which disconnects (optional argument: nicegui.Client)
- `app.on_exception`: called when an exception occurs (optional argument: exception)

When NiceGUI is shut down or restarted, all tasks still in execution will be automatically canceled.

_circle__circle__circle_

main.py

`from datetime import datetime from nicegui import app, ui  dt = datetime.now()  def handle_connection():     global dt     dt = datetime.now() app.on_connect(handle_connection)  label = ui.label() ui.timer(1, lambda: label.set_text(f'Last new connection: {dt:%H:%M:%S}'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Last new connection: 11:27:35

Custom error page

[_link_](https://nicegui.io/documentation/section_action_events#custom_error_page)

You can use `@app.on_page_exception` to define a custom error page.

The handler must be a synchronous function that creates a page like a normal page function. It can take the exception as an argument, but it is not required. It overrides the default "sad face" error page, except when the error is re-raised.

The following example shows how to create a custom error page handler that only handles a specific exception. The default error page handler is still used for all other exceptions.

Note: Showing the traceback may not be a good idea in production, as it may leak sensitive information.

_Added in version 2.20.0_

_circle__circle__circle_

main.py

`import traceback from nicegui import app, ui  @app.on_page_exception def timeout_error_page(exception: Exception) -> None:     if not isinstance(exception, TimeoutError):         raise exception     with ui.column().classes('absolute-center items-center gap-8'):         ui.icon('sym_o_timer', size='xl')         ui.label(f'{exception}').classes('text-2xl')         ui.code(traceback.format_exc(chain=False))  @ui.page('/raise_timeout_error') def raise_timeout_error():     raise TimeoutError('This took too long')  @ui.page('/raise_runtime_error') def raise_runtime_error():     raise RuntimeError('Something is wrong')  ui.link('Raise timeout error (custom error page)', '/raise_timeout_error') ui.link('Raise runtime error (default error page)', '/raise_runtime_error')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

[Raise timeout error (custom error page)](https://nicegui.io/raise_timeout_error)[Raise runtime error (default error page)](https://nicegui.io/raise_runtime_error)

Shut down NiceGUI

[_link_](https://nicegui.io/documentation/section_action_events#shut_down_nicegui)

This will programmatically stop the server.

_circle__circle__circle_

main.py

`from nicegui import app, ui  ui.button('shutdown', on_click=app.shutdown)  ui.run(reload=False)`

_content\_copy_

_circle__circle__circle_

NiceGUI

shutdown

[Storage](https://nicegui.io/documentation/storage)[_link_](https://nicegui.io/documentation/section_action_events#storage)

NiceGUI offers a straightforward mechanism for data persistence within your application. It features five built-in storage types:

- `app.storage.tab`: Stored server-side in memory, this dictionary is unique to each non-duplicated tab session and can hold arbitrary objects. Data will be lost when restarting the server until [https://github.com/zauberzeug/nicegui/discussions/2841](https://github.com/zauberzeug/nicegui/discussions/2841) is implemented. This storage is only available within [page builder functions](https://nicegui.io/documentation/page) and requires an established connection, obtainable via [`await client.connected()`](https://nicegui.io/documentation/page#wait_for_client_connection).
- `app.storage.client`: Also stored server-side in memory, this dictionary is unique to each client connection and can hold arbitrary objects. Data will be discarded when the page is reloaded or the user navigates to another page. Unlike data stored in `app.storage.tab` which can be persisted on the server even for days, `app.storage.client` helps caching resource-hungry objects such as a streaming or database connection you need to keep alive for dynamic site updates but would like to discard as soon as the user leaves the page or closes the browser. This storage is only available within [page builder functions](https://nicegui.io/documentation/page).
- `app.storage.user`: Stored server-side, each dictionary is associated with a unique identifier held in a browser session cookie. Unique to each user, this storage is accessible across all their browser tabs. `app.storage.browser['id']` is used to identify the user. This storage is only available within [page builder functions](https://nicegui.io/documentation/page) and requires the `storage_secret` parameter in`ui.run()` to sign the browser session cookie.
- `app.storage.general`: Also stored server-side, this dictionary provides a shared storage space accessible to all users.
- `app.storage.browser`: Unlike the previous types, this dictionary is stored directly as the browser session cookie, shared among all browser tabs for the same user. However, `app.storage.user` is generally preferred due to its advantages in reducing data payload, enhancing security, and offering larger storage capacity. By default, NiceGUI holds a unique identifier for the browser session in `app.storage.browser['id']`. This storage is only available within [page builder functions](https://nicegui.io/documentation/page) and requires the `storage_secret` parameter in `ui.run()` to sign the browser session cookie.

The following table will help you to choose storage.

| Storage type                | `client` | `tab`  | `browser` | `user` | `general` |
| --------------------------- | -------- | ------ | --------- | ------ | --------- |
| Location                    | Server   | Server | Browser   | Server | Server    |
| Across tabs                 | No       | No     | Yes       | Yes    | Yes       |
| Across browsers             | No       | No     | No        | No     | Yes       |
| Across server restarts      | No       | Yes    | No        | Yes    | Yes       |
| Across page reloads         | No       | Yes    | Yes       | Yes    | Yes       |
| Needs page builder function | Yes      | Yes    | Yes       | Yes    | No        |
| Needs client connection     | No       | Yes    | No        | No     | No        |
| Write only before response  | No       | No     | Yes       | No     | No        |
| Needs serializable data     | No       | No     | Yes       | Yes    | Yes       |
| Needs `storage_secret`      | No       | No     | Yes       | Yes    | No        |

_circle__circle__circle_

main.py

`from nicegui import app, ui  @ui.page('/') def index():     app.storage.user['count'] = app.storage.user.get('count', 0) + 1     with ui.row():        ui.label('your own page visits:')        ui.label().bind_text_from(app.storage.user, 'count')  ui.run(storage_secret='private key to secure the browser session cookie')`

_content\_copy_

_circle__circle__circle_

NiceGUI

your own page visits:

1

See [more...](https://nicegui.io/documentation/storage)

[](https://nicegui.io/imprint_privacy)
