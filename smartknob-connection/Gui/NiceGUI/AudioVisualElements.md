*Audiovisual* Elements

[Image](https://nicegui.io/documentation/image)[*link*](https://nicegui.io/documentation/section_audiovisual_elements#image)

Displays an image. This element is based on Quasar's [QImg](https://quasar.dev/vue-components/img) component.

|         |                                                                                        |
| ------- | -------------------------------------------------------------------------------------- |
| source: | the source of the image; can be a URL, local file path, a base64 string or a PIL image |

*circle**circle**circle*

main.py

`from nicegui import ui  ui.image('https://picsum.photos/id/377/640/360')  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI

![](https://picsum.photos/id/377/640/360)

See [more...](https://nicegui.io/documentation/image)

Captions and Overlays

[*link*](https://nicegui.io/documentation/section_audiovisual_elements#captions_and_overlays)

By nesting elements inside a `ui.image` you can create augmentations.

Use [Quasar classes](https://quasar.dev/vue-components/img) for positioning and styling captions. To overlay an SVG, make the `viewBox` exactly the size of the image and provide `100%` width/height to match the actual rendered size.

*circle**circle**circle*

main.py

`from nicegui import ui  with ui.image('https://picsum.photos/id/29/640/360'):     ui.label('Nice!').classes('absolute-bottom text-subtitle2 text-center')  with ui.image('https://cdn.stocksnap.io/img-thumbs/960w/airplane-sky_DYPWDEEILG.jpg'):     ui.html('''         <svg viewBox="0 0 960 638" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">         <circle cx="445" cy="300" r="100" fill="none" stroke="red" stroke-width="10" />         </svg>     ''').classes('w-full bg-transparent')  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI

![](https://picsum.photos/id/29/640/360)

Nice!

![](https://cdn.stocksnap.io/img-thumbs/960w/airplane-sky_DYPWDEEILG.jpg)

[Interactive Image](https://nicegui.io/documentation/interactive_image)[*link*](https://nicegui.io/documentation/section_audiovisual_elements#interactive_image)

Create an image with an SVG overlay that handles mouse events and yields image coordinates. It is also the best choice for non-flickering image updates. If the source URL changes faster than images can be loaded by the browser, some images are simply skipped. Thereby repeatedly updating the image source will automatically adapt to the available bandwidth. See [OpenCV Webcam](https://github.com/zauberzeug/nicegui/tree/main/examples/opencv_webcam/main.py) for an example.

The mouse event handler is called with mouse event arguments containing

- type (the name of the JavaScript event),
- image_x and image_y (image coordinates in pixels),
- button and buttons (mouse button numbers from the JavaScript event), as well as
- alt, ctrl, meta, and shift (modifier keys from the JavaScript event).

You can also pass a tuple of width and height instead of an image source. This will create an empty image with the given size.

|           |                                                                                                |
| --------- | ---------------------------------------------------------------------------------------------- |
| source:   | the source of the image; can be an URL, local file path, a base64 string or just an image size |
| content:  | SVG content which should be overlaid; viewport has the same dimensions as the image            |
| size:     | size of the image (width, height) in pixels; only used if source is not set                    |
| on_mouse: | callback for mouse events (contains image coordinates image_x and image_y in pixels)           |
| events:   | list of JavaScript events to subscribe to (default: ['click'])                                 |
| cross:    | whether to show crosshairs or a color string (default: False)                                  |

*circle**circle**circle*

main.py

`from nicegui import events, ui  def mouse_handler(e: events.MouseEventArguments):     color = 'SkyBlue' if e.type == 'mousedown' else 'SteelBlue'     ii.content += f'<circle cx="{e.image_x}" cy="{e.image_y}" r="15" fill="none" stroke="{color}" stroke-width="4" />'     ui.notify(f'{e.type} at ({e.image_x:.1f}, {e.image_y:.1f})')  src = 'https://picsum.photos/id/565/640/360' ii = ui.interactive_image(src, on_mouse=mouse_handler, events=['mousedown', 'mouseup'], cross=True)  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI

![](https://picsum.photos/id/565/640/360)

See [more...](https://nicegui.io/documentation/interactive_image)

[Audio](https://nicegui.io/documentation/audio)[*link*](https://nicegui.io/documentation/section_audiovisual_elements#audio)

Displays an audio player.

|           |                                                                                  |
| --------- | -------------------------------------------------------------------------------- |
| src:      | URL or local file path of the audio source                                       |
| controls: | whether to show the audio controls, like play, pause, and volume (default: True) |
| autoplay: | whether to start playing the audio automatically (default: False)                |
| muted:    | whether the audio should be initially muted (default: False)                     |
| loop:     | whether the audio should loop (default: False)                                   |

See [here](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/audio#events) for a list of events you can subscribe to using the generic event subscription on().

*circle**circle**circle*

main.py

`from nicegui import ui  a = ui.audio('https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3') a.on('ended', lambda _: ui.notify('Audio playback completed'))  ui.button(on_click=lambda: a.props('muted'), icon='volume_off').props('outline') ui.button(on_click=lambda: a.props(remove='muted'), icon='volume_up').props('outline')  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI

*volume_off**volume_up*

See [more...](https://nicegui.io/documentation/audio)

[Video](https://nicegui.io/documentation/video)[*link*](https://nicegui.io/documentation/section_audiovisual_elements#video)

Displays a video.

|           |                                                                                  |
| --------- | -------------------------------------------------------------------------------- |
| src:      | URL or local file path of the video source                                       |
| controls: | whether to show the video controls, like play, pause, and volume (default: True) |
| autoplay: | whether to start playing the video automatically (default: False)                |
| muted:    | whether the video should be initially muted (default: False)                     |
| loop:     | whether the video should loop (default: False)                                   |

See [here](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video#events) for a list of events you can subscribe to using the generic event subscription on().

*circle**circle**circle*

main.py

`from nicegui import ui  v = ui.video('https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4') v.on('ended', lambda _: ui.notify('Video playback completed'))  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI

See [more...](https://nicegui.io/documentation/video)

[Icon](https://nicegui.io/documentation/icon)[*link*](https://nicegui.io/documentation/section_audiovisual_elements#icon)

This element is based on Quasar's [QIcon](https://quasar.dev/vue-components/icon) component.

[Here](https://fonts.google.com/icons?icon.set=Material+Icons) is a reference of possible names.

|        |                                                                                                         |
| ------ | ------------------------------------------------------------------------------------------------------- |
| name:  | name of the icon (snake case, e.g. add_circle)                                                          |
| size:  | size in CSS units, including unit name or standard size name (xs\|sm\|md\|lg\|xl), examples: 16px, 2rem |
| color: | icon color (either a Quasar, Tailwind, or CSS color or None, default: None)                             |

*circle**circle**circle*

main.py

`from nicegui import ui  ui.icon('thumb_up', color='primary').classes('text-5xl')  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI

*thumb_up*

See [more...](https://nicegui.io/documentation/icon)

[Avatar](https://nicegui.io/documentation/avatar)[*link*](https://nicegui.io/documentation/section_audiovisual_elements#avatar)

A avatar element wrapping Quasar's [QAvatar](https://quasar.dev/vue-components/avatar) component.

|             |                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------- |
| icon:       | name of the icon or image path with "img:" prefix (e.g. "map", "img:path/to/image.png")                 |
| color:      | background color (either a Quasar, Tailwind, or CSS color or None, default: "primary")                  |
| text_color: | color name from the Quasar Color Palette (e.g. "primary", "teal-10")                                    |
| size:       | size in CSS units, including unit name or standard size name (xs\|sm\|md\|lg\|xl) (e.g. "16px", "2rem") |
| font_size:  | size in CSS units, including unit name, of the content (icon, text) (e.g. "18px", "2rem")               |
| square:     | removes border-radius so borders are squared (default: False)                                           |
| rounded:    | applies a small standard border-radius for a squared shape of the component (default: False)            |

*circle**circle**circle*

main.py

`from nicegui import ui  ui.avatar('favorite_border', text_color='grey-11', square=True) ui.avatar('img:https://nicegui.io/logo_square.png', color='blue-2')  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI

*favorite_border*

*![](https://nicegui.io/logo_square.png)*

See [more...](https://nicegui.io/documentation/avatar)

SVG

[*link*](https://nicegui.io/documentation/section_audiovisual_elements#svg)

You can add Scalable Vector Graphics using the `ui.html` element.

*circle**circle**circle*

main.py

`from nicegui import ui  content = '''     <svg viewBox="0 0 200 200" width="100" height="100" xmlns="http://www.w3.org/2000/svg">     <circle cx="100" cy="100" r="78" fill="#ffde34" stroke="black" stroke-width="3" />     <circle cx="80" cy="85" r="8" />     <circle cx="120" cy="85" r="8" />     <path d="m60,120 C75,150 125,150 140,120" style="fill:none; stroke:black; stroke-width:8; stroke-linecap:round" />     </svg>''' ui.html(content)  ui.run()`

*content_copy*

*circle**circle**circle*

NiceGUI
