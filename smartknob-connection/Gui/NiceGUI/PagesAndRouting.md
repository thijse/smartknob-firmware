_Pages_ & Routing

[Page](https://nicegui.io/documentation/page)[_link_](https://nicegui.io/documentation/section_pages_routing#page)

This decorator marks a function to be a page builder. Each user accessing the given route will see a new instance of the page. This means it is private to the user and not shared with others (as it is done [when placing elements outside of a page decorator](https://nicegui.io/documentation/section_pages_routing#auto-index_page)).

Notes:

- The name of the decorated function is unused and can be anything.
- The page route is determined by the path argument and registered globally.
- The decorator does only work for free functions and static methods. Instance methods or initializers would require a self argument, which the router cannot associate. See [our modularization example](https://github.com/zauberzeug/nicegui/tree/main/examples/modularization/) for strategies to structure your code.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">path:</th><td class="field-body">route of the new page (path must start with '/')</td></tr><tr class="field"><th class="field-name">title:</th><td class="field-body">optional page title</td></tr><tr class="field"><th class="field-name">viewport:</th><td class="field-body">optional viewport meta tag content</td></tr><tr class="field"><th class="field-name">favicon:</th><td class="field-body">optional relative filepath or absolute URL to a favicon (default: <cite>None</cite>, NiceGUI icon will be used)</td></tr><tr class="field"><th class="field-name">dark:</th><td class="field-body">whether to use Quasar's dark mode (defaults to <cite>dark</cite> argument of <cite>run</cite> command)</td></tr><tr class="field"><th class="field-name">language:</th><td class="field-body">language of the page (defaults to <cite>language</cite> argument of <cite>run</cite> command)</td></tr><tr class="field"><th class="field-name" colspan="2">response_timeout:</th></tr><tr class="field"><td> </td><td class="field-body">maximum time for the decorated function to build the page (default: 3.0 seconds)</td></tr><tr class="field"><th class="field-name" colspan="2">reconnect_timeout:</th></tr><tr class="field"><td> </td><td class="field-body">maximum time the server waits for the browser to reconnect (defaults to <cite>reconnect_timeout</cite> argument of <cite>run</cite> command))</td></tr><tr class="field"><th class="field-name">api_router:</th><td class="field-body">APIRouter instance to use, can be left <cite>None</cite> to use the default</td></tr><tr class="field"><th class="field-name">kwargs:</th><td class="field-body">additional keyword arguments passed to FastAPI's @app.get method</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  @ui.page('/other_page') def other_page():     ui.label('Welcome to the other side')  @ui.page('/dark_page', dark=True) def dark_page():     ui.label('Welcome to the dark side')  ui.link('Visit other page', other_page) ui.link('Visit dark page', dark_page)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

[Visit other page](https://nicegui.io/other_page)[Visit dark page](https://nicegui.io/dark_page)

See [more...](https://nicegui.io/documentation/page)

Auto-index page

[_link_](https://nicegui.io/documentation/section_pages_routing#auto-index_page)

Pages created with the `@ui.page` decorator are "private". Their content is re-created for each client. Thus, in the demo to the right, the displayed ID on the private page changes when the browser reloads the page.

UI elements that are not wrapped in a decorated page function are placed on an automatically generated index page at route "/". This auto-index page is created once on startup and _shared_ across all clients that might connect. Thus, each connected client will see the _same_ elements. In the demo to the right, the displayed ID on the auto-index page remains constant when the browser reloads the page.

_circle__circle__circle_

main.py

`from nicegui import ui from uuid import uuid4  @ui.page('/private_page') async def private_page():     ui.label(f'private page with ID {uuid4()}')  ui.label(f'shared auto-index page with ID {uuid4()}') ui.link('private page', private_page)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

shared auto-index page with ID bf8489ef-53a8-4dec-ba33-e5ba9812fb9e

[private page](https://nicegui.io/private_page)

[Page Layout](https://nicegui.io/documentation/page_layout)[_link_](https://nicegui.io/documentation/section_pages_routing#page_layout)

With `ui.header`, `ui.footer`, `ui.left_drawer` and `ui.right_drawer` you can add additional layout elements to a page. The `fixed` argument controls whether the element should scroll or stay fixed on the screen. The `top_corner` and `bottom_corner` arguments indicate whether a drawer should expand to the top or bottom of the page. See [https://quasar.dev/layout/header-and-footer](https://quasar.dev/layout/header-and-footer) and [https://quasar.dev/layout/drawer](https://quasar.dev/layout/drawer) for more information about possible props. With `ui.page_sticky` you can place an element "sticky" on the screen. See [https://quasar.dev/layout/page-sticky](https://quasar.dev/layout/page-sticky) for more information.

_circle__circle__circle_

main.py

`from nicegui import ui  @ui.page('/page_layout') def page_layout():     ui.label('CONTENT')     [ui.label(f'Line {i}') for i in range(100)]     with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):         ui.label('HEADER')         ui.button(on_click=lambda: right_drawer.toggle(), icon='menu').props('flat color=white')     with ui.left_drawer(top_corner=True, bottom_corner=True).style('background-color: #d7e3f4'):         ui.label('LEFT DRAWER')     with ui.right_drawer(fixed=False).style('background-color: #ebf1fa').props('bordered') as right_drawer:         ui.label('RIGHT DRAWER')     with ui.footer().style('background-color: #3874c8'):         ui.label('FOOTER')  ui.link('show page with fancy layout', page_layout)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

[show page with fancy layout](https://nicegui.io/page_layout)

See [more...](https://nicegui.io/documentation/page_layout)

[Sub Pages](https://nicegui.io/documentation/sub_pages)[_link_](https://nicegui.io/documentation/section_pages_routing#sub_pages)

Sub pages provide URL-based navigation between different views. This allows you to easily build a single page application (SPA). The `ui.sub_pages` element itself functions as the container for the currently active sub page. You only need to provide the routes for each view builder function. NiceGUI takes care of replacing the content without triggering a full page reload when the URL changes.

**NOTE: This is an experimental feature, and the API is subject to change.**

_circle__circle__circle_

main.py

`from nicegui import ui from uuid import uuid4  @ui.page('/') @ui.page('/{_:path}')  # NOTE: our page should catch all paths def index():     ui.label(f'This ID {str(uuid4())[:6]} changes only on reload.')     ui.separator()     ui.sub_pages({'/': main, '/other': other})  def main():     ui.label('Main page content')     ui.link('Go to other page', '/other')  def other():     ui.label('Another page content')     ui.link('Go to main page', '/')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

This ID 7789ea changes only on reload.

---

Main page content

Go to other page

See [more...](https://nicegui.io/documentation/sub_pages)

Parameter injection

[_link_](https://nicegui.io/documentation/section_pages_routing#parameter_injection)

Thanks to FastAPI, a page function accepts optional parameters to provide [path parameters](https://fastapi.tiangolo.com/tutorial/path-params/), [query parameters](https://fastapi.tiangolo.com/tutorial/query-params/) or the whole incoming [request](https://fastapi.tiangolo.com/advanced/using-request-directly/) for accessing the body payload, headers, cookies and more.

_circle__circle__circle_

main.py

`from nicegui import ui  @ui.page('/icon/{icon}') def icons(icon: str, amount: int = 1):     ui.label(icon).classes('text-h3')     with ui.row():         [ui.icon(icon).classes('text-h3') for _ in range(amount)] ui.link('Star', '/icon/star?amount=5') ui.link('Home', '/icon/home') ui.link('Water', '/icon/water_drop?amount=3')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

[Star](https://nicegui.io/icon/star?amount=5)[Home](https://nicegui.io/icon/home)[Water](https://nicegui.io/icon/water_drop?amount=3)

[Page title](https://nicegui.io/documentation/page_title)[_link_](https://nicegui.io/documentation/section_pages_routing#page_title)

Set the page title for the current client.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">title:</th><td class="field-body">page title</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.button('Change page title', on_click=lambda: ui.page_title('New Title'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Change page title

See [more...](https://nicegui.io/documentation/page_title)

[Navigation functions](https://nicegui.io/documentation/navigate)[_link_](https://nicegui.io/documentation/section_pages_routing#navigation_functions)

These functions allow you to navigate within the browser history and to external URLs.

_Added in version 2.0.0_

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.row():     ui.button('Back', on_click=ui.navigate.back)     ui.button('Forward', on_click=ui.navigate.forward)     ui.button('Reload', on_click=ui.navigate.reload)     ui.button(icon='savings',               on_click=lambda: ui.navigate.to('https://github.com/sponsors/zauberzeug'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

BackForwardReload_savings_

See [more...](https://nicegui.io/documentation/navigate)

ui.open

[_link_](https://nicegui.io/documentation/section_pages_routing#ui_open)

The `ui.open` function is deprecated. Use [`ui.navigate.to`](https://nicegui.io/documentation/navigate#ui_navigate_to_\(formerly_ui_open\)) instead.

[Download functions](https://nicegui.io/documentation/download)[_link_](https://nicegui.io/documentation/section_pages_routing#download_functions)

These functions allow you to download files, URLs or raw data.

_Added in version 2.14.0_

_circle__circle__circle_

main.py

`from nicegui import ui  ui.button('Local file', on_click=lambda: ui.download.file('main.py')) ui.button('From URL', on_click=lambda: ui.download.from_url('/logo.png')) ui.button('Content', on_click=lambda: ui.download.content('Hello World', 'hello.txt'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Local fileFrom URLContent

See [more...](https://nicegui.io/documentation/download)

Add a directory of static files

[_link_](https://nicegui.io/documentation/section_pages_routing#add_a_directory_of_static_files)

add\_static\_files() makes a local directory available at the specified endpoint, e.g. '/static'. This is useful for providing local data like images to the frontend. Otherwise the browser would not be able to access the files. Do only put non-security-critical files in there, as they are accessible to everyone.

To make a single file accessible, you can use add\_static\_file(). For media files which should be streamed, you can use add\_media\_files() or add\_media\_file() instead.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">url_path:</th><td class="field-body">string that starts with a slash "/" and identifies the path at which the files should be served</td></tr><tr class="field"><th class="field-name" colspan="2">local_directory:</th></tr><tr class="field"><td> </td><td class="field-body">local folder with files to serve as static content</td></tr><tr class="field"><th class="field-name">follow_symlink:</th><td class="field-body">whether to follow symlinks (default: False)</td></tr><tr class="field"><th class="field-name">max_cache_age:</th><td class="field-body">value for max-age set in Cache-Control header (<em>added in version 2.8.0</em>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import app, ui  app.add_static_files('/examples', 'examples') ui.label('Some NiceGUI Examples').classes('text-h5') ui.link('AI interface', '/examples/ai_interface/main.py') ui.link('Custom FastAPI app', '/examples/fastapi/main.py') ui.link('Authentication', '/examples/authentication/main.py')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Some NiceGUI Examples

[AI interface](https://nicegui.io/examples/ai_interface/main.py)[Custom FastAPI app](https://nicegui.io/examples/fastapi/main.py)[Authentication](https://nicegui.io/examples/authentication/main.py)

Add directory of media files

[_link_](https://nicegui.io/documentation/section_pages_routing#add_directory_of_media_files)

add\_media\_files() allows a local files to be streamed from a specified endpoint, e.g. '/media'. This should be used for media files to support proper streaming. Otherwise the browser would not be able to access and load the the files incrementally or jump to different positions in the stream. Do only put non-security-critical files in there, as they are accessible to everyone.

To make a single file accessible via streaming, you can use add\_media\_file(). For small static files, you can use add\_static\_files() or add\_static\_file() instead.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">url_path:</th><td class="field-body">string that starts with a slash "/" and identifies the path at which the files should be served</td></tr><tr class="field"><th class="field-name" colspan="2">local_directory:</th></tr><tr class="field"><td> </td><td class="field-body">local folder with files to serve as media content</td></tr></tbody></table>

_circle__circle__circle_

main.py

`import httpx from nicegui import app, ui from pathlib import Path  media = Path('media') media.mkdir(exist_ok=True) r = httpx.get('https://cdn.coverr.co/videos/coverr-cloudy-sky-2765/1080p.mp4') (media  / 'clouds.mp4').write_bytes(r.content) app.add_media_files('/my_videos', media) ui.video('/my_videos/clouds.mp4')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Add HTML to the page

[_link_](https://nicegui.io/documentation/section_pages_routing#add_html_to_the_page)

You can add HTML to the page by calling `ui.add_head_html` or `ui.add_body_html`. This is useful for adding custom CSS styles or JavaScript code.

_circle__circle__circle_

main.py

`from nicegui import ui  ui.add_head_html('''     <style>         .my-red-label {             color: Crimson;             font-weight: bold;         }     </style> ''') ui.label('RED').classes('my-red-label')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

RED

API Responses

[_link_](https://nicegui.io/documentation/section_pages_routing#api_responses)

NiceGUI is based on [FastAPI](https://fastapi.tiangolo.com/). This means you can use all of FastAPI's features. For example, you can implement a RESTful API in addition to your graphical user interface. You simply import the `app` object from `nicegui`. Or you can run NiceGUI on top of your own FastAPI app by using `ui.run_with(app)` instead of starting a server automatically with `ui.run()`.

You can also return any other FastAPI response object inside a page function. For example, you can return a `RedirectResponse` to redirect the user to another page if certain conditions are met. This is used in our [authentication demo](https://github.com/zauberzeug/nicegui/tree/main/examples/authentication/main.py).

_circle__circle__circle_

main.py

`import random from nicegui import app, ui  @app.get('/random/{max}') def generate_random_number(max: int):     return {'min': 0, 'max': max, 'value': random.randint(0, max)}  max = ui.number('max', value=100) ui.button('generate random number',           on_click=lambda: ui.navigate.to(f'/random/{max.value:.0f}'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

max

generate random number

[](https://nicegui.io/imprint_privacy)
