_Data_ Elements

[Table](https://nicegui.io/documentation/table)[_link_](https://nicegui.io/documentation/section_data_elements#table)

A table based on Quasar's [QTable](https://quasar.dev/vue-components/table) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">rows:</th><td class="field-body">list of row objects</td></tr><tr class="field"><th class="field-name">columns:</th><td class="field-body">list of column objects (defaults to the columns of the first row <em>since version 2.0.0</em>)</td></tr><tr class="field"><th class="field-name" colspan="2">column_defaults:</th></tr><tr class="field"><td> </td><td class="field-body">optional default column properties, <em>added in version 2.0.0</em></td></tr><tr class="field"><th class="field-name">row_key:</th><td class="field-body">name of the column containing unique data identifying the row (default: "id")</td></tr><tr class="field"><th class="field-name">title:</th><td class="field-body">title of the table</td></tr><tr class="field"><th class="field-name">selection:</th><td class="field-body">selection type ("single" or "multiple"; default: <cite>None</cite>)</td></tr><tr class="field"><th class="field-name">pagination:</th><td class="field-body">a dictionary correlating to a pagination object or number of rows per page (<cite>None</cite> hides the pagination, 0 means "infinite"; default: <cite>None</cite>).</td></tr><tr class="field"><th class="field-name">on_select:</th><td class="field-body">callback which is invoked when the selection changes</td></tr><tr class="field"><th class="field-name" colspan="2">on_pagination_change:</th></tr><tr class="field"><td> </td><td class="field-body">callback which is invoked when the pagination changes</td></tr></tbody></table>

If selection is 'single' or 'multiple', then a selected property is accessible containing the selected rows.

_circle__circle__circle_

main.py

`from nicegui import ui  columns = [     {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left'},     {'name': 'age', 'label': 'Age', 'field': 'age', 'sortable': True}, ] rows = [     {'name': 'Alice', 'age': 18},     {'name': 'Bob', 'age': 21},     {'name': 'Carol'}, ] ui.table(columns=columns, rows=rows, row_key='name')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

| Name  | _arrow\_upward_Age |
| ----- | ------------------ |
| Alice | 18                 |
| Bob   | 21                 |
| Carol |                    |

See [more...](https://nicegui.io/documentation/table)

[AG Grid](https://nicegui.io/documentation/aggrid)[_link_](https://nicegui.io/documentation/section_data_elements#ag_grid)

An element to create a grid using [AG Grid](https://www.ag-grid.com/).

The methods run\_grid\_method and run\_row\_method can be used to interact with the AG Grid instance on the client.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">options:</th><td class="field-body">dictionary of AG Grid options</td></tr><tr class="field"><th class="field-name">html_columns:</th><td class="field-body">list of columns that should be rendered as HTML (default: <tt class="docutils literal">[]</tt>)</td></tr><tr class="field"><th class="field-name">theme:</th><td class="field-body">AG Grid theme (default: "balham")</td></tr><tr class="field"><th class="field-name" colspan="2">auto_size_columns:</th></tr><tr class="field"><td> </td><td class="field-body">whether to automatically resize columns to fit the grid width (default: <tt class="docutils literal">True</tt>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  grid = ui.aggrid({     'defaultColDef': {'flex': 1},     'columnDefs': [         {'headerName': 'Name', 'field': 'name'},         {'headerName': 'Age', 'field': 'age'},         {'headerName': 'Parent', 'field': 'parent', 'hide': True},     ],     'rowData': [         {'name': 'Alice', 'age': 18, 'parent': 'David'},         {'name': 'Bob', 'age': 21, 'parent': 'Eve'},         {'name': 'Carol', 'age': 42, 'parent': 'Frank'},     ],     'rowSelection': 'multiple', }).classes('max-h-40')  def update():     grid.options['rowData'][0]['age'] += 1     grid.update()  ui.button('Update', on_click=update) ui.button('Select all', on_click=lambda: grid.run_grid_method('selectAll')) ui.button('Show parent', on_click=lambda: grid.run_grid_method('setColumnsVisible', ['parent'], True))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Name

Age

Alice

18

Bob

21

Carol

42

to of

Page of

UpdateSelect allShow parent

See [more...](https://nicegui.io/documentation/aggrid)

[Highcharts chart](https://nicegui.io/documentation/highchart)[_link_](https://nicegui.io/documentation/section_data_elements#highcharts_chart)

An element to create a chart using [Highcharts](https://www.highcharts.com/). Updates can be pushed to the chart by changing the options property. After data has changed, call the update method to refresh the chart.

Due to Highcharts' restrictive license, this element is not part of the standard NiceGUI package. It is maintained in a [separate repository](https://github.com/zauberzeug/nicegui-highcharts/) and can be installed with pip install nicegui\[highcharts\].

By default, a Highcharts.chart is created. To use, e.g., Highcharts.stockChart instead, set the type property to "stockChart".

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">options:</th><td class="field-body">dictionary of Highcharts options</td></tr><tr class="field"><th class="field-name">type:</th><td class="field-body">chart type (e.g. "chart", "stockChart", "mapChart", ...; default: "chart")</td></tr><tr class="field"><th class="field-name">extras:</th><td class="field-body">list of extra dependencies to include (e.g. "annotations", "arc-diagram", "solid-gauge", ...)</td></tr><tr class="field"><th class="field-name">on_point_click:</th><td class="field-body">callback function that is called when a point is clicked</td></tr><tr class="field"><th class="field-name" colspan="2">on_point_drag_start:</th></tr><tr class="field"><td> </td><td class="field-body">callback function that is called when a point drag starts</td></tr><tr class="field"><th class="field-name">on_point_drag:</th><td class="field-body">callback function that is called when a point is dragged</td></tr><tr class="field"><th class="field-name">on_point_drop:</th><td class="field-body">callback function that is called when a point is dropped</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui from random import random  chart = ui.highchart({     'title': False,     'chart': {'type': 'bar'},     'xAxis': {'categories': ['A', 'B']},     'series': [         {'name': 'Alpha', 'data': [0.1, 0.2]},         {'name': 'Beta', 'data': [0.3, 0.4]},     ], }).classes('w-full h-64')  def update():     chart.options['series'][0]['data'][0] = random()     chart.update()  ui.button('Update', on_click=update)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Created with Highcharts 11.4.8ValuesAlphaBeta00.10.20.30.40.5ABHighcharts.com

Update

See [more...](https://nicegui.io/documentation/highchart)

[Apache EChart](https://nicegui.io/documentation/echart)[_link_](https://nicegui.io/documentation/section_data_elements#apache_echart)

An element to create a chart using [ECharts](https://echarts.apache.org/). Updates can be pushed to the chart by changing the options property. After data has changed, call the update method to refresh the chart.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">options:</th><td class="field-body">dictionary of EChart options</td></tr><tr class="field"><th class="field-name">on_click_point:</th><td class="field-body">callback that is invoked when a point is clicked</td></tr><tr class="field"><th class="field-name">enable_3d:</th><td class="field-body">enforce importing the echarts-gl library</td></tr><tr class="field"><th class="field-name">renderer:</th><td class="field-body">renderer to use ("canvas" or "svg", <em>added in version 2.7.0</em>)</td></tr><tr class="field"><th class="field-name">theme:</th><td class="field-body">an EChart theme configuration (dictionary or a URL returning a JSON object, <em>added in version 2.15.0</em>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui from random import random  echart = ui.echart({     'xAxis': {'type': 'value'},     'yAxis': {'type': 'category', 'data': ['A', 'B'], 'inverse': True},     'legend': {'textStyle': {'color': 'gray'}},     'series': [         {'type': 'bar', 'name': 'Alpha', 'data': [0.1, 0.2]},         {'type': 'bar', 'name': 'Beta', 'data': [0.3, 0.4]},     ], })  def update():     echart.options['series'][0]['data'][0] = random()     echart.update()  ui.button('Update', on_click=update)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Update

See [more...](https://nicegui.io/documentation/echart)

[Pyplot Context](https://nicegui.io/documentation/pyplot)[_link_](https://nicegui.io/documentation/section_data_elements#pyplot_context)

Create a context to configure a [Matplotlib](https://matplotlib.org/) plot.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">close:</th><td class="field-body">whether the figure should be closed after exiting the context; set to <cite>False</cite> if you want to update it later (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name">kwargs:</th><td class="field-body">arguments like <cite>figsize</cite> which should be passed to <a class="reference external" href="https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.figure.html">pyplot.figure</a></td></tr></tbody></table>

_circle__circle__circle_

main.py

`import numpy as np from matplotlib import pyplot as plt from nicegui import ui  with ui.pyplot(figsize=(3, 2)):     x = np.linspace(0.0, 5.0)     y = np.cos(2 * np.pi * x) * np.exp(-x)     plt.plot(x, y, '-')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

2025-09-14T11:26:45.844793 image/svg+xml Matplotlib v3.7.5, https://matplotlib.org/ \*{stroke-linejoin: round; stroke-linecap: butt}

See [more...](https://nicegui.io/documentation/pyplot)

[Matplotlib](https://nicegui.io/documentation/matplotlib)[_link_](https://nicegui.io/documentation/section_data_elements#matplotlib)

Create a [Matplotlib](https://matplotlib.org/) element rendering a Matplotlib figure. The figure is automatically updated when leaving the figure context.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">kwargs:</th><td class="field-body">arguments like <cite>figsize</cite> which should be passed to <a class="reference external" href="https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure">matplotlib.figure.Figure</a></td></tr></tbody></table>

_circle__circle__circle_

main.py

`import numpy as np from nicegui import ui  with ui.matplotlib(figsize=(3, 2)).figure as fig:     x = np.linspace(0.0, 5.0)     y = np.cos(2 * np.pi * x) * np.exp(-x)     ax = fig.gca()     ax.plot(x, y, '-')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

2025-09-14T11:26:46.008667 image/svg+xml Matplotlib v3.7.5, https://matplotlib.org/ \*{stroke-linejoin: round; stroke-linecap: butt}

See [more...](https://nicegui.io/documentation/matplotlib)

[Line Plot](https://nicegui.io/documentation/line_plot)[_link_](https://nicegui.io/documentation/section_data_elements#line_plot)

Create a line plot using pyplot. The push method provides live updating when utilized in combination with ui.timer.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">n:</th><td class="field-body">number of lines</td></tr><tr class="field"><th class="field-name">limit:</th><td class="field-body">maximum number of datapoints per line (new points will displace the oldest)</td></tr><tr class="field"><th class="field-name">update_every:</th><td class="field-body">update plot only after pushing new data multiple times to save CPU and bandwidth</td></tr><tr class="field"><th class="field-name">close:</th><td class="field-body">whether the figure should be closed after exiting the context; set to <cite>False</cite> if you want to update it later (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name">kwargs:</th><td class="field-body">arguments like <cite>figsize</cite> which should be passed to <a class="reference external" href="https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.figure.html">pyplot.figure</a></td></tr></tbody></table>

_circle__circle__circle_

main.py

`import math from datetime import datetime from nicegui import ui  line_plot = ui.line_plot(n=2, limit=20, figsize=(3, 2), update_every=5) \     .with_legend(['sin', 'cos'], loc='upper center', ncol=2)  def update_line_plot() -> None:     now = datetime.now()     x = now.timestamp()     y1 = math.sin(x)     y2 = math.cos(x)     line_plot.push([now], [[y1], [y2]], y_limits=(-1.5, 1.5))  line_updates = ui.timer(0.1, update_line_plot, active=False) line_checkbox = ui.checkbox('active').bind_value(line_updates, 'active')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

2025-09-14T11:26:46.152982 image/svg+xml Matplotlib v3.7.5, https://matplotlib.org/ \*{stroke-linejoin: round; stroke-linecap: butt}

active

See [more...](https://nicegui.io/documentation/line_plot)

[Plotly Element](https://nicegui.io/documentation/plotly)[_link_](https://nicegui.io/documentation/section_data_elements#plotly_element)

Renders a Plotly chart. There are two ways to pass a Plotly figure for rendering, see parameter figure:

- Pass a go.Figure object, see [https://plotly.com/python/](https://plotly.com/python/)
- Pass a Python dict object with keys data, layout, config (optional), see [https://plotly.com/javascript/](https://plotly.com/javascript/)

For best performance, use the declarative dict approach for creating a Plotly chart.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">figure:</th><td class="field-body">Plotly figure to be rendered. Can be either a <cite>go.Figure</cite> instance, or a <cite>dict</cite> object with keys <cite>data</cite>, <cite>layout</cite>, <cite>config</cite> (optional).</td></tr></tbody></table>

_circle__circle__circle_

main.py

`import plotly.graph_objects as go from nicegui import ui  fig = go.Figure(go.Scatter(x=[1, 2, 3, 4], y=[1, 2, 3, 2.5])) fig.update_layout(margin=dict(l=0, r=0, t=0, b=0)) ui.plotly(fig).classes('w-full h-40')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

123411.522.53

[.cls-0{fill:#000;} .cls-1{fill:#FFF;} .cls-2{fill:#F26;} .cls-3{fill:#D69;} .cls-4{fill:#BAC;} .cls-5{fill:#9EF;} plotly-logomark](https://plotly.com/)

See [more...](https://nicegui.io/documentation/plotly)

[Linear Progress](https://nicegui.io/documentation/linear_progress)[_link_](https://nicegui.io/documentation/section_data_elements#linear_progress)

A linear progress bar wrapping Quasar's [QLinearProgress](https://quasar.dev/vue-components/linear-progress) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value of the field (from 0.0 to 1.0)</td></tr><tr class="field"><th class="field-name">size:</th><td class="field-body">the height of the progress bar (default: "20px" with value label and "4px" without)</td></tr><tr class="field"><th class="field-name">show_value:</th><td class="field-body">whether to show a value label in the center (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">color (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: "primary")</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  slider = ui.slider(min=0, max=1, step=0.01, value=0.5) ui.linear_progress().bind_value_from(slider, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

0.5

See [more...](https://nicegui.io/documentation/linear_progress)

[Circular Progress](https://nicegui.io/documentation/circular_progress)[_link_](https://nicegui.io/documentation/section_data_elements#circular_progress)

A circular progress bar wrapping Quasar's [QCircularProgress](https://quasar.dev/vue-components/circular-progress).

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">the initial value of the field</td></tr><tr class="field"><th class="field-name">min:</th><td class="field-body">the minimum value (default: 0.0)</td></tr><tr class="field"><th class="field-name">max:</th><td class="field-body">the maximum value (default: 1.0)</td></tr><tr class="field"><th class="field-name">size:</th><td class="field-body">the size of the progress circle (default: "xl")</td></tr><tr class="field"><th class="field-name">show_value:</th><td class="field-body">whether to show a value label in the center (default: <cite>True</cite>)</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">color (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: "primary")</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  slider = ui.slider(min=0, max=1, step=0.01, value=0.5) ui.circular_progress().bind_value_from(slider, 'value')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

0.5

See [more...](https://nicegui.io/documentation/circular_progress)

[Spinner](https://nicegui.io/documentation/spinner)[_link_](https://nicegui.io/documentation/section_data_elements#spinner)

This element is based on Quasar's [QSpinner](https://quasar.dev/vue-components/spinners) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">type:</th><td class="field-body">type of spinner (e.g. "audio", "ball", "bars", ..., default: "default")</td></tr><tr class="field"><th class="field-name">size:</th><td class="field-body">size of the spinner (e.g. "3em", "10px", "xl", ..., default: "1em")</td></tr><tr class="field"><th class="field-name">color:</th><td class="field-body">color of the spinner (either a Quasar, Tailwind, or CSS color or <cite>None</cite>, default: "primary")</td></tr><tr class="field"><th class="field-name">thickness:</th><td class="field-body">thickness of the spinner (applies to the "default" spinner only, default: 5.0)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.row():     ui.spinner(size='lg')     ui.spinner('audio', size='lg', color='green')     ui.spinner('dots', size='lg', color='red')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

See [more...](https://nicegui.io/documentation/spinner)

[3D Scene](https://nicegui.io/documentation/scene)[_link_](https://nicegui.io/documentation/section_data_elements#3d_scene)

Display a 3D scene using [three.js](https://threejs.org/). Currently NiceGUI supports boxes, spheres, cylinders/cones, extrusions, straight lines, curves and textured meshes. Objects can be translated, rotated and displayed with different color, opacity or as wireframes. They can also be grouped to apply joint movements.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">width:</th><td class="field-body">width of the canvas</td></tr><tr class="field"><th class="field-name">height:</th><td class="field-body">height of the canvas</td></tr><tr class="field"><th class="field-name">grid:</th><td class="field-body">whether to display a grid (boolean or tuple of <tt class="docutils literal">size</tt> and <tt class="docutils literal">divisions</tt> for <a class="reference external" href="https://threejs.org/docs/#api/en/helpers/GridHelper">Three.js' GridHelper</a>, default: 100x100)</td></tr><tr class="field"><th class="field-name">camera:</th><td class="field-body">camera definition, either instance of <tt class="docutils literal">ui.scene.perspective_camera</tt> (default) or <tt class="docutils literal">ui.scene.orthographic_camera</tt></td></tr><tr class="field"><th class="field-name">on_click:</th><td class="field-body">callback to execute when a 3D object is clicked (use <tt class="docutils literal">click_events</tt> to specify which events to subscribe to)</td></tr><tr class="field"><th class="field-name">click_events:</th><td class="field-body">list of JavaScript click events to subscribe to (default: <tt class="docutils literal">['click', 'dblclick']</tt>)</td></tr><tr class="field"><th class="field-name">on_drag_start:</th><td class="field-body">callback to execute when a 3D object is dragged</td></tr><tr class="field"><th class="field-name">on_drag_end:</th><td class="field-body">callback to execute when a 3D object is dropped</td></tr><tr class="field"><th class="field-name" colspan="2">drag_constraints:</th></tr><tr class="field"><td> </td><td class="field-body">comma-separated JavaScript expression for constraining positions of dragged objects (e.g. <tt class="docutils literal">'x = 0, z = y / 2'</tt>)</td></tr><tr class="field"><th class="field-name" colspan="2">background_color:</th></tr><tr class="field"><td> </td><td class="field-body">background color of the scene (default: "#eee")</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.scene().classes('w-full h-64') as scene:     scene.axes_helper()     scene.sphere().material('#4488ff').move(2, 2)     scene.cylinder(1, 0.5, 2, 20).material('#ff8800', opacity=0.5).move(-2, 1)     scene.extrusion([[0, 0], [0, 1], [1, 0.5]], 0.1).material('#ff8888').move(2, -1)      with scene.group().move(z=2):         scene.box().move(x=2)         scene.box().move(y=2).rotate(0.25, 0.5, 0.75)         scene.box(wireframe=True).material('#888888').move(x=2, y=2)      scene.line([-4, 0, 0], [-4, 2, 0]).material('#ff0000')     scene.curve([-4, 0, 0], [-4, -1, 0], [-3, -1, 0], [-3, 0, 0]).material('#008800')      logo = 'https://avatars.githubusercontent.com/u/2843826'     scene.texture(logo, [[[0.5, 2, 0], [2.5, 2, 0]],                          [[0.5, 0, 0], [2.5, 0, 0]]]).move(1, -3)      teapot = 'https://upload.wikimedia.org/wikipedia/commons/9/93/Utah_teapot_(solid).stl'     scene.stl(teapot).scale(0.2).move(-3, 4)      avocado = 'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/Avocado/glTF-Binary/Avocado.glb'     scene.gltf(avocado).scale(40).move(-2, -3, 0.5)      scene.text('2D', 'background: rgba(0, 0, 0, 0.2); border-radius: 5px; padding: 5px').move(z=2)     scene.text3d('3D', 'background: rgba(0, 0, 0, 0.2); border-radius: 5px; padding: 5px').move(y=-2).scale(.05)  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

2D

3D

See [more...](https://nicegui.io/documentation/scene)

[Leaflet map](https://nicegui.io/documentation/leaflet)[_link_](https://nicegui.io/documentation/section_data_elements#leaflet_map)

This element is a wrapper around the [Leaflet](https://leafletjs.com/) JavaScript library.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">center:</th><td class="field-body">initial center location of the map (latitude/longitude, default: (0.0, 0.0))</td></tr><tr class="field"><th class="field-name">zoom:</th><td class="field-body">initial zoom level of the map (default: 13)</td></tr><tr class="field"><th class="field-name">draw_control:</th><td class="field-body">whether to show the draw toolbar (default: False)</td></tr><tr class="field"><th class="field-name">options:</th><td class="field-body">additional options passed to the Leaflet map (default: {})</td></tr><tr class="field"><th class="field-name" colspan="2">hide_drawn_items:</th></tr><tr class="field"><td> </td><td class="field-body">whether to hide drawn items on the map (default: False, <em>added in version 2.0.0</em>)</td></tr><tr class="field"><th class="field-name" colspan="2">additional_resources:</th></tr><tr class="field"><td> </td><td class="field-body">additional resources like CSS or JS files to load (default: None, <em>added in version 2.11.0</em>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  m = ui.leaflet(center=(51.505, -0.09)) ui.label().bind_text_from(m, 'center', lambda center: f'Center: {center[0]:.3f}, {center[1]:.3f}') ui.label().bind_text_from(m, 'zoom', lambda zoom: f'Zoom: {zoom}')  with ui.grid(columns=2):     ui.button('London', on_click=lambda: m.set_center((51.505, -0.090)))     ui.button('Berlin', on_click=lambda: m.set_center((52.520, 13.405)))     ui.button(icon='zoom_in', on_click=lambda: m.set_zoom(m.zoom + 1))     ui.button(icon='zoom_out', on_click=lambda: m.set_zoom(m.zoom - 1))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

![](https://a.tile.osm.org/13/4093/2723.png)![](https://b.tile.osm.org/13/4094/2723.png)![](https://b.tile.osm.org/13/4093/2724.png)![](https://c.tile.osm.org/13/4094/2724.png)

[+](https://nicegui.io/documentation/section_data_elements# "Zoom in")[−](https://nicegui.io/documentation/section_data_elements# "Zoom out")

[Leaflet](https://leafletjs.com/ "A JavaScript library for interactive maps") | © [OpenStreetMap](https://openstreetmap.org/) contributors

Center: 51.505, -0.090

Zoom: 13

LondonBerlin_zoom\_in__zoom\_out_

See [more...](https://nicegui.io/documentation/leaflet)

[Tree](https://nicegui.io/documentation/tree)[_link_](https://nicegui.io/documentation/section_data_elements#tree)

Display hierarchical data using Quasar's [QTree](https://quasar.dev/vue-components/tree) component.

If using IDs, make sure they are unique within the whole tree.

To use checkboxes and on\_tick, set the tick\_strategy parameter to "leaf", "leaf-filtered" or "strict".

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">nodes:</th><td class="field-body">hierarchical list of node objects</td></tr><tr class="field"><th class="field-name">node_key:</th><td class="field-body">property name of each node object that holds its unique id (default: "id")</td></tr><tr class="field"><th class="field-name">label_key:</th><td class="field-body">property name of each node object that holds its label (default: "label")</td></tr><tr class="field"><th class="field-name">children_key:</th><td class="field-body">property name of each node object that holds its list of children (default: "children")</td></tr><tr class="field"><th class="field-name">on_select:</th><td class="field-body">callback which is invoked when the node selection changes</td></tr><tr class="field"><th class="field-name">on_expand:</th><td class="field-body">callback which is invoked when the node expansion changes</td></tr><tr class="field"><th class="field-name">on_tick:</th><td class="field-body">callback which is invoked when a node is ticked or unticked</td></tr><tr class="field"><th class="field-name">tick_strategy:</th><td class="field-body">whether and how to use checkboxes ("leaf", "leaf-filtered" or "strict"; default: <tt class="docutils literal">None</tt>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.tree([     {'id': 'numbers', 'children': [{'id': '1'}, {'id': '2'}]},     {'id': 'letters', 'children': [{'id': 'A'}, {'id': 'B'}]}, ], label_key='id', on_select=lambda e: ui.notify(e.value))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

_play\_arrow_

numbers

1

2

_play\_arrow_

letters

A

B

See [more...](https://nicegui.io/documentation/tree)

[Log View](https://nicegui.io/documentation/log)[_link_](https://nicegui.io/documentation/section_data_elements#log_view)

Create a log view that allows to add new lines without re-transmitting the whole history to the client.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">max_lines:</th><td class="field-body">maximum number of lines before dropping oldest ones (default: <cite>None</cite>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from datetime import datetime from nicegui import ui  log = ui.log(max_lines=10).classes('w-full h-20') ui.button('Log time', on_click=lambda: log.push(datetime.now().strftime('%X.%f')[:-5]))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

Log time

See [more...](https://nicegui.io/documentation/log)

[Editor](https://nicegui.io/documentation/editor)[_link_](https://nicegui.io/documentation/section_data_elements#editor)

A WYSIWYG editor based on [Quasar's QEditor](https://quasar.dev/vue-components/editor). The value is a string containing the formatted text as HTML code.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">value:</th><td class="field-body">initial value</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback to be invoked when the value changes</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  editor = ui.editor(placeholder='Type something here') ui.markdown().bind_content_from(editor, 'value',                                 backward=lambda v: f'HTML code:\n```\n{v}\n```')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

_format\_align\_left__format\_align\_center__format\_align\_right__format\_align\_justify_

_format\_bold__format\_italic__format\_underlined__strikethrough\_s_

_undo__redo_

HTML code:

See [more...](https://nicegui.io/documentation/editor)

[Code](https://nicegui.io/documentation/code)[_link_](https://nicegui.io/documentation/section_data_elements#code)

This element displays a code block with syntax highlighting.

In secure environments (HTTPS or localhost), a copy button is displayed to copy the code to the clipboard.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">content:</th><td class="field-body">code to display</td></tr><tr class="field"><th class="field-name">language:</th><td class="field-body">language of the code (default: "python")</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.code('''     from nicegui import ui      ui.label('Code inception!')      ui.run() ''').classes('w-full')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

`from nicegui import ui  ui.label('Code inception!')  ui.run()`

_content\_copy_

See [more...](https://nicegui.io/documentation/code)

[JSONEditor](https://nicegui.io/documentation/json_editor)[_link_](https://nicegui.io/documentation/section_data_elements#jsoneditor)

An element to create a JSON editor using [JSONEditor](https://github.com/josdejong/svelte-jsoneditor). Updates can be pushed to the editor by changing the properties property. After data has changed, call the update method to refresh the editor.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">properties:</th><td class="field-body">dictionary of JSONEditor properties</td></tr><tr class="field"><th class="field-name">on_select:</th><td class="field-body">callback which is invoked when some of the content has been selected</td></tr><tr class="field"><th class="field-name">on_change:</th><td class="field-body">callback which is invoked when the content has changed</td></tr><tr class="field"><th class="field-name">schema:</th><td class="field-body">optional <a class="reference external" href="https://json-schema.org/">JSON schema</a> for validating the data being edited (<em>added in version 2.8.0</em>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  json = {     'array': [1, 2, 3],     'boolean': True,     'color': '#82b92c',     None: None,     'number': 123,     'object': {         'a': 'b',         'c': 'd',     },     'time': 1575599819000,     'string': 'Hello World', } ui.json_editor({'content': {'json': json}},                on_select=lambda e: ui.notify(f'Select: {e}'),                on_change=lambda e: ui.notify(f'Change: {e}'))  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

text tree table

{

array

:

\[

3 items  

0

:

1

1

:

2

2

:

3

\]

boolean

:

true

color

:

#82b92c

null

:

null

number

:

123

object

:

{

a

:

b

c

:

d

}

time

:

1575599819000

string

:

Hello World

}

See [more...](https://nicegui.io/documentation/json_editor)

[](https://nicegui.io/imprint_privacy)
