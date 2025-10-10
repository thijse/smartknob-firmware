Configuration & Deployment

URLs

[_link_](https://nicegui.io/documentation/section_configuration_deployment#urls)

You can access the list of all URLs on which the NiceGUI app is available via `app.urls`. The URLs are not available in `app.on_startup` because the server is not yet running. Instead, you can access them in a page function or register a callback with `app.urls.on_change`.

_circle__circle__circle_

main.py

`from nicegui import app, ui  @ui.page('/') def index():     for url in app.urls:         ui.link(url, target=url)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

[https://nicegui.io](https://nicegui.io/)

[ui.run](https://nicegui.io/documentation/run)[_link_](https://nicegui.io/documentation/section_configuration_deployment#ui_run)

You can call ui.run() with optional arguments. Most of them only apply after stopping and fully restarting the app and do not apply with auto-reloading.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">host:</th><td class="field-body">start server with this host (defaults to <cite>'127.0.0.1</cite> in native mode, otherwise <cite>'0.0.0.0'</cite>)</td></tr><tr class="field"><th class="field-name">port:</th><td class="field-body">use this port (default: 8080 in normal mode, and an automatically determined open port in native mode)</td></tr><tr class="field"><th class="field-name">title:</th><td class="field-body">page title (default: <cite>'NiceGUI'</cite>, can be overwritten per page)</td></tr><tr class="field"><th class="field-name">viewport:</th><td class="field-body">page meta viewport content (default: <cite>'width=device-width, initial-scale=1'</cite>, can be overwritten per page)</td></tr><tr class="field"><th class="field-name">favicon:</th><td class="field-body">relative filepath, absolute URL to a favicon (default: <cite>None</cite>, NiceGUI icon will be used) or emoji (e.g. <cite>'🚀'</cite>, works for most browsers)</td></tr><tr class="field"><th class="field-name">dark:</th><td class="field-body">whether to use Quasar's dark mode (default: <cite>False</cite>, use <cite>None</cite> for "auto" mode)</td></tr><tr class="field"><th class="field-name">language:</th><td class="field-body">language for Quasar elements (default: <cite>'en-US'</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">binding_refresh_interval:</th></tr><tr class="field"><td> </td><td class="field-body">time between binding updates (default: <cite>0.1</cite> seconds, bigger is more CPU friendly)</td></tr><tr class="field"><th class="field-name" colspan="2">reconnect_timeout:</th></tr><tr class="field"><td> </td><td class="field-body">maximum time the server waits for the browser to reconnect (default: 3.0 seconds)</td></tr><tr class="field"><th class="field-name" colspan="2">message_history_length:</th></tr><tr class="field"><td> </td><td class="field-body">maximum number of messages that will be stored and resent after a connection interruption (default: 1000, use 0 to disable, <em>added in version 2.9.0</em>)</td></tr><tr class="field"><th class="field-name" colspan="2">cache_control_directives:</th></tr><tr class="field"><td> </td><td class="field-body">cache control directives for internal static files (default: <cite>'public, max-age=31536000, immutable, stale-while-revalidate=31536000'</cite>)</td></tr><tr class="field"><th class="field-name">fastapi_docs:</th><td class="field-body">enable FastAPI's automatic documentation with Swagger UI, ReDoc, and OpenAPI JSON (bool or dictionary as described <a class="reference external" href="https://fastapi.tiangolo.com/tutorial/metadata/">here</a>, default: <cite>False</cite>, <em>updated in version 2.9.0</em>)</td></tr><tr class="field"><th class="field-name">show:</th><td class="field-body">automatically open the UI in a browser tab (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name">on_air:</th><td class="field-body">tech preview: <a class="reference external" href="https://nicegui.io/documentation/section_configuration_deployment#nicegui_on_air">allows temporary remote access</a> if set to <cite>True</cite> (default: disabled)</td></tr><tr class="field"><th class="field-name">native:</th><td class="field-body">open the UI in a native window of size 800x600 (default: <cite>False</cite>, deactivates <cite>show</cite>, automatically finds an open port)</td></tr><tr class="field"><th class="field-name">window_size:</th><td class="field-body">open the UI in a native window with the provided size (e.g. <cite>(1024, 786)</cite>, default: <cite>None</cite>, also activates <cite>native</cite>)</td></tr><tr class="field"><th class="field-name">fullscreen:</th><td class="field-body">open the UI in a fullscreen window (default: <cite>False</cite>, also activates <cite>native</cite>)</td></tr><tr class="field"><th class="field-name">frameless:</th><td class="field-body">open the UI in a frameless window (default: <cite>False</cite>, also activates <cite>native</cite>)</td></tr><tr class="field"><th class="field-name">reload:</th><td class="field-body">automatically reload the UI on file changes (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">uvicorn_logging_level:</th></tr><tr class="field"><td> </td><td class="field-body">logging level for uvicorn server (default: <cite>'warning'</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">uvicorn_reload_dirs:</th></tr><tr class="field"><td> </td><td class="field-body">string with comma-separated list for directories to be monitored (default is current working directory only)</td></tr><tr class="field"><th class="field-name" colspan="2">uvicorn_reload_includes:</th></tr><tr class="field"><td> </td><td class="field-body">string with comma-separated list of glob-patterns which trigger reload on modification (default: <cite>'*.py'</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">uvicorn_reload_excludes:</th></tr><tr class="field"><td> </td><td class="field-body">string with comma-separated list of glob-patterns which should be ignored for reload (default: <cite>'.*, .py[cod], .sw.*, ~*'</cite>)</td></tr><tr class="field"><th class="field-name">tailwind:</th><td class="field-body">whether to use Tailwind (experimental, default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name">prod_js:</th><td class="field-body">whether to use the production version of Vue and Quasar dependencies (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name" colspan="2">endpoint_documentation:</th></tr><tr class="field"><td> </td><td class="field-body">control what endpoints appear in the autogenerated OpenAPI docs (default: 'none', options: 'none', 'internal', 'page', 'all')</td></tr><tr class="field"><th class="field-name">storage_secret:</th><td class="field-body">secret key for browser-based storage (default: <cite>None</cite>, a value is required to enable ui.storage.individual and ui.storage.browser)</td></tr><tr class="field"><th class="field-name" colspan="2">show_welcome_message:</th></tr><tr class="field"><td> </td><td class="field-body">whether to show the welcome message (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name">kwargs:</th><td class="field-body">additional keyword arguments are passed to <cite>uvicorn.run</cite></td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.label('page with custom title')  ui.run(title='My App')`

_content\_copy_

_circle__circle__circle_

My App

page with custom title

See [more...](https://nicegui.io/documentation/run)

Native Mode

[_link_](https://nicegui.io/documentation/section_configuration_deployment#native_mode)

You can enable native mode for NiceGUI by specifying `native=True` in the `ui.run` function. To customize the initial window size and display mode, use the `window_size` and `fullscreen` parameters respectively. Additionally, you can provide extra keyword arguments via `app.native.window_args` and `app.native.start_args`. Pick any parameter as it is defined by the internally used [pywebview module](https://pywebview.flowrl.com/api) for the `webview.create_window` and `webview.start` functions. Note that these keyword arguments will take precedence over the parameters defined in `ui.run`.

Additionally, you can change `webview.settings` via `app.native.settings`.

In native mode the `app.native.main_window` object allows you to access the underlying window. It is an async version of [`Window` from pywebview](https://pywebview.flowrl.com/api/#webview-window).

_circle__circle__circle_

main.py

`from nicegui import app, ui  app.native.window_args['resizable'] = False app.native.start_args['debug'] = True app.native.settings['ALLOW_DOWNLOADS'] = True  ui.label('app running in native mode') ui.button('enlarge', on_click=lambda: app.native.main_window.resize(1000, 700))  ui.run(native=True, window_size=(400, 300), fullscreen=False)`

_content\_copy_

_circle__circle__circle_

NiceGUI

app running in native mode

enlarge

Note that the native app is run in a separate [process](https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process). Therefore any configuration changes from code run under a [main guard](https://docs.python.org/3/library/__main__.html#idiomatic-usage) is ignored by the native app. The following examples show the difference between a working and a non-working configuration.

_circle__circle__circle_

good\_example.py

`from nicegui import app, ui  app.native.window_args['resizable'] = False  # works  if __name__ == '__main__':     ui.run(native=True, reload=False)`

_circle__circle__circle_

bad\_example.py

`from nicegui import app, ui  if __name__ == '__main__':     app.native.window_args['resizable'] = False  # ignored      ui.run(native=True, reload=False)`

If webview has trouble finding required libraries, you may get an error relating to "WebView2Loader.dll". To work around this issue, try moving the DLL file up a directory, e.g.:

- from `.venv/Lib/site-packages/webview/lib/x64/WebView2Loader.dll`
- to `.venv/Lib/site-packages/webview/lib/WebView2Loader.dll`

Environment Variables

[_link_](https://nicegui.io/documentation/section_configuration_deployment#environment_variables)

You can set the following environment variables to configure NiceGUI:

- `MATPLOTLIB` (default: true) can be set to `false` to avoid the potentially costly import of Matplotlib. This will make `ui.pyplot` and `ui.line_plot` unavailable.
- `NICEGUI_STORAGE_PATH` (default: local ".nicegui") can be set to change the location of the storage files.
- `MARKDOWN_CONTENT_CACHE_SIZE` (default: 1000): The maximum number of Markdown content snippets that are cached in memory.
- `RST_CONTENT_CACHE_SIZE` (default: 1000): The maximum number of ReStructuredText content snippets that are cached in memory.
- `NICEGUI_REDIS_URL` (default: None, means local file storage): The URL of the Redis server to use for shared persistent storage.
- `NICEGUI_REDIS_KEY_PREFIX` (default: "nicegui:"): The prefix for Redis keys.

_circle__circle__circle_

main.py

`from nicegui import ui from nicegui.elements import markdown  ui.label(f'Markdown content cache size is {markdown.prepare_content.cache_info().maxsize}')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Markdown content cache size is 1000

Background Tasks

[_link_](https://nicegui.io/documentation/section_configuration_deployment#background_tasks)

`background_tasks.create()` allows you to run an async function in the background and return a task object. By default the task will be automatically cancelled during shutdown. You can prevent this by using the `@background_tasks.await_on_shutdown` decorator (added in version 2.16.0). This is useful for tasks that need to be completed even when the app is shutting down.

_circle__circle__circle_

main.py

`import aiofiles import asyncio from nicegui import background_tasks, ui  results = {'answer': '?'}  async def compute() -> None:     await asyncio.sleep(1)     results['answer'] = 42  @background_tasks.await_on_shutdown async def backup() -> None:     await asyncio.sleep(1)     async with aiofiles.open('backup.json', 'w') as f:         await f.write(f'{results["answer"]}')     print('backup.json written', flush=True)  ui.label().bind_text_from(results, 'answer', lambda x: f'answer: {x}') ui.button('Compute', on_click=lambda: background_tasks.create(compute())) ui.button('Backup', on_click=lambda: background_tasks.create(backup()))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

answer: ?

ComputeBackup

Custom Vue Components

[_link_](https://nicegui.io/documentation/section_configuration_deployment#custom_vue_components)

You can create custom components by subclassing `ui.element` and implementing a corresponding Vue component. The ["Custom Vue components" example](https://github.com/zauberzeug/nicegui/tree/main/examples/custom_vue_component) demonstrates how to create a custom counter component which emits events and receives updates from the server.

The ["Signature pad" example](https://github.com/zauberzeug/nicegui/blob/main/examples/signature_pad) shows how to define dependencies for a custom component using a `package.json` file. This allows you to use third-party libraries via NPM in your component.

Last but not least, the ["Node module integration" example](https://github.com/zauberzeug/nicegui/blob/main/examples/node_module_integration) demonstrates how to create a package.json file and a webpack.config.js file to bundle a custom Vue component with its dependencies.

Server Hosting

[_link_](https://nicegui.io/documentation/section_configuration_deployment#server_hosting)

To deploy your NiceGUI app on a server, you will need to execute your `main.py` (or whichever file contains your `ui.run(...)`) on your cloud infrastructure. You can, for example, just install the [NiceGUI python package via pip](https://pypi.org/project/nicegui/) and use systemd or similar service to start the main script. In most cases, you will set the port to 80 (or 443 if you want to use HTTPS) with the `ui.run` command to make it easily accessible from the outside.

A convenient alternative is the use of our [pre-built multi-arch Docker image](https://hub.docker.com/r/zauberzeug/nicegui) which contains all necessary dependencies. With this command you can launch the script `main.py` in the current directory on the public port 80:

_circle__circle__circle_

bash

`docker run -it --restart always \ -p 80:8080 \ -e PUID=$(id -u) \ -e PGID=$(id -g) \ -v $(pwd)/:/app/ \ zauberzeug/nicegui:latest`

The demo assumes `main.py` uses the port 8080 in the `ui.run` command (which is the default). The `-d` tells docker to run in background and `--restart always` makes sure the container is restarted if the app crashes or the server reboots. Of course this can also be written in a Docker compose file:

_circle__circle__circle_

docker-compose.yml

`app:     image: zauberzeug/nicegui:latest     restart: always     ports:         - 80:8080     environment:         - PUID=1000 # change this to your user id         - PGID=1000 # change this to your group id     volumes:         - ./:/app/`

There are other handy features in the Docker image like non-root user execution and signal pass-through. For more details we recommend to have a look at our [Docker example](https://github.com/zauberzeug/nicegui/tree/main/examples/docker_image).

To serve your application with [HTTPS](https://fastapi.tiangolo.com/deployment/https/) encryption, you can provide SSL certificates in multiple ways. For instance, you can directly provide your certificates to [Uvicorn](https://www.uvicorn.org/), which NiceGUI is based on, by passing the relevant [options](https://www.uvicorn.org/#command-line-options) to `ui.run()`. If both a certificate and key file are provided, the application will automatically be served over HTTPS:

_circle__circle__circle_

main.py

`from nicegui import ui  ui.run(     port=443,     ssl_certfile="<path_to_certfile>",     ssl_keyfile="<path_to_keyfile>", )`

In production we also like using reverse proxies like [Traefik](https://doc.traefik.io/traefik/) or [NGINX](https://www.nginx.com/) to handle these details for us. See our development [docker-compose.yml](https://github.com/zauberzeug/nicegui/blob/main/docker-compose.yml) as an example based on traefik or [this example nginx.conf file](https://github.com/zauberzeug/nicegui/blob/main/examples/nginx_https/nginx.conf) showing how NGINX can be used to handle the SSL certificates and reverse proxy to your NiceGUI app.

You may also have a look at [our demo for using a custom FastAPI app](https://github.com/zauberzeug/nicegui/tree/main/examples/fastapi). This will allow you to do very flexible deployments as described in the [FastAPI documentation](https://fastapi.tiangolo.com/deployment/). Note that there are additional steps required to allow multiple workers.

Package for Installation

[_link_](https://nicegui.io/documentation/section_configuration_deployment#package_for_installation)

NiceGUI apps can also be bundled into an executable with `nicegui-pack` which is based on [PyInstaller](https://www.pyinstaller.org/). This allows you to distribute your app as a single file that can be executed on any computer.

Just make sure to call `ui.run` with `reload=False` in your main script to disable the auto-reload feature. Running the `nicegui-pack` command below will create an executable `myapp` in the `dist` folder:

_circle__circle__circle_

main.py

`from nicegui import native, ui  ui.label('Hello from PyInstaller')  ui.run(reload=False, port=native.find_open_port())`

_circle__circle__circle_

bash

`nicegui-pack --onefile --name "myapp" main.py`

**Packaging Tips:**

- When building a PyInstaller app, your main script can use a native window (rather than a browser window) by using `ui.run(reload=False, native=True)`. The `native` parameter can be `True` or `False` depending on whether you want a native window or to launch a page in the user's browser - either will work in the PyInstaller generated app.

- Specifying `--windowed` to `nicegui-pack` will prevent a terminal console from appearing. However you should only use this option if you have also specified `native=True` in your `ui.run` command. Without a terminal console the user won't be able to exit the app by pressing Ctrl-C. With the `native=True` option, the app will automatically close when the window is closed, as expected.

- Specifying `--windowed` to `nicegui-pack` will create an `.app` file on Mac which may be more convenient to distribute. When you double-click the app to run it, it will not show any console output. You can also run the app from the command line with `./myapp.app/Contents/MacOS/myapp` to see the console output.

- Specifying `--onefile` to `nicegui-pack` will create a single executable file. Whilst convenient for distribution, it will be slower to start up. This is not NiceGUI's fault but just the way Pyinstaller zips things into a single file, then unzips everything into a temporary directory before running. You can mitigate this by removing `--onefile` from the `nicegui-pack` command, and zip up the generated `dist` directory yourself, distribute it, and your end users can unzip once and be good to go, without the constant expansion of files due to the `--onefile` flag.

- Summary of user experience for different options:
  
  | `nicegui-pack`           | `ui.run(...)`  | Explanation                                                                                                                              |
  | ------------------------ | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
  | `onefile`                | `native=False` | Single executable generated in `dist/`, runs in browser                                                                                  |
  | `onefile`                | `native=True`  | Single executable generated in `dist/`, runs in popup window                                                                             |
  | `onefile` and `windowed` | `native=True`  | Single executable generated in `dist/` (on Mac a proper `dist/myapp.app` generated incl. icon), runs in popup window, no console appears |
  | `onefile` and `windowed` | `native=False` | Avoid (no way to exit the app)                                                                                                           |
  | Specify neither          |                | A `dist/myapp` directory created which can be zipped manually and distributed; run with `dist/myapp/myapp`                               |

- If you are using a Python virtual environment, ensure you `pip install pyinstaller` within your virtual environment so that the correct PyInstaller is used, or you may get broken apps due to the wrong version of PyInstaller being picked up. That is why the `nicegui-pack` invokes PyInstaller using `python -m PyInstaller` rather than just `pyinstaller`.

_circle__circle__circle_

bash

`python -m venv venv source venv/bin/activate pip install nicegui pip install pyinstaller`

Note: If you're getting an error "TypeError: a bytes-like object is required, not 'str'", try adding the following lines to the top of your `main.py` file:

`import sys sys.stdout = open('logs.txt', 'w')`

See [https://github.com/zauberzeug/nicegui/issues/681](https://github.com/zauberzeug/nicegui/issues/681) for more information.

**macOS Packaging**

Add the following snippet before anything else in your main app's file, to prevent new processes from being spawned in an endless loop:

`# macOS packaging support from multiprocessing import freeze_support  # noqa freeze_support()  # noqa  # all your other imports and code`

The `# noqa` comment instructs Pylance or autopep8 to not apply any PEP rule on those two lines, guaranteeing they remain on top of anything else. This is key to prevent process spawning.
