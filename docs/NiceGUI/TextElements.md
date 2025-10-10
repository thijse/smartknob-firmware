_Text_ Elements

[Label](https://nicegui.io/documentation/label)[_link_](https://nicegui.io/documentation/section_text_elements#label)

Displays some text.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the content of the label</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.label('some label')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

some label

See [more...](https://nicegui.io/documentation/label)

[Link](https://nicegui.io/documentation/link)[_link_](https://nicegui.io/documentation/section_text_elements#link)

Create a hyperlink.

To jump to a specific location within a page you can place linkable anchors with ui.link\_target("name") and link to it with ui.link(target="#name").

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">display text</td></tr><tr class="field"><th class="field-name">target:</th><td class="field-body">page function, NiceGUI element on the same page or string that is a an absolute URL or relative path from base URL</td></tr><tr class="field"><th class="field-name">new_tab:</th><td class="field-body">open link in new tab (default: False)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.link('NiceGUI on GitHub', 'https://github.com/zauberzeug/nicegui')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

[NiceGUI on GitHub](https://github.com/zauberzeug/nicegui)

See [more...](https://nicegui.io/documentation/link)

[Chat Message](https://nicegui.io/documentation/chat_message)[_link_](https://nicegui.io/documentation/section_text_elements#chat_message)

Based on Quasar's [Chat Message](https://quasar.dev/vue-components/chat/) component.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">text:</th><td class="field-body">the message body (can be a list of strings for multiple message parts)</td></tr><tr class="field"><th class="field-name">name:</th><td class="field-body">the name of the message author</td></tr><tr class="field"><th class="field-name">label:</th><td class="field-body">renders a label header/section only</td></tr><tr class="field"><th class="field-name">stamp:</th><td class="field-body">timestamp of the message</td></tr><tr class="field"><th class="field-name">avatar:</th><td class="field-body">URL to an avatar</td></tr><tr class="field"><th class="field-name">sent:</th><td class="field-body">render as a sent message (so from current user) (default: False)</td></tr><tr class="field"><th class="field-name">text_html:</th><td class="field-body">render text as HTML (default: False)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.chat_message('Hello NiceGUI!',                 name='Robot',                 stamp='now',                 avatar='https://robohash.org/ui')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

![](https://robohash.org/ui)

Robot

Hello NiceGUI!

now

See [more...](https://nicegui.io/documentation/chat_message)

[Generic Element](https://nicegui.io/documentation/element)[_link_](https://nicegui.io/documentation/section_text_elements#generic_element)

This class is the base class for all other UI elements. But you can use it to create elements with arbitrary HTML tags.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">tag:</th><td class="field-body">HTML tag of the element</td></tr><tr class="field"><th class="field-name">_client:</th><td class="field-body">client for this element (for internal use only)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  with ui.element('div').classes('p-2 bg-blue-100'):     ui.label('inside a colored div')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

inside a colored div

See [more...](https://nicegui.io/documentation/element)

[Markdown Element](https://nicegui.io/documentation/markdown)[_link_](https://nicegui.io/documentation/section_text_elements#markdown_element)

Renders Markdown onto the page.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">content:</th><td class="field-body">the Markdown content to be displayed</td></tr><tr class="field"><th class="field-name">extras:</th><td class="field-body">list of <a class="reference external" href="https://github.com/trentm/python-markdown2/wiki/Extras#implemented-extras">markdown2 extensions</a> (default: <cite>['fenced-code-blocks', 'tables']</cite>)</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.markdown('This is **Markdown**.')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

This is **Markdown**.

See [more...](https://nicegui.io/documentation/markdown)

[ReStructuredText](https://nicegui.io/documentation/restructured_text)[_link_](https://nicegui.io/documentation/section_text_elements#restructuredtext)

Renders ReStructuredText onto the page.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">content:</th><td class="field-body">the ReStructuredText content to be displayed</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.restructured_text('This is **reStructuredText**.')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

This is **reStructuredText**.

See [more...](https://nicegui.io/documentation/restructured_text)

[Mermaid Diagrams](https://nicegui.io/documentation/mermaid)[_link_](https://nicegui.io/documentation/section_text_elements#mermaid_diagrams)

Renders diagrams and charts written in the Markdown-inspired [Mermaid](https://mermaid.js.org/) language. The mermaid syntax can also be used inside Markdown elements by providing the extension string 'mermaid' to the ui.markdown element.

The optional configuration dictionary is passed directly to mermaid before the first diagram is rendered. This can be used to set such options as

> {'securityLevel': 'loose', ...} - allow running JavaScript when a node is clicked {'logLevel': 'info', ...} - log debug info to the console

Refer to the Mermaid documentation for the mermaid.initialize() method for a full list of options.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">content:</th><td class="field-body">the Mermaid content to be displayed</td></tr><tr class="field"><th class="field-name">config:</th><td class="field-body">configuration dictionary to be passed to <tt class="docutils literal">mermaid.initialize()</tt></td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.mermaid(''' graph LR;     A --> B;     A --> C; ''')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

#c3620\_mermaid{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#333;}#c3620\_mermaid .error-icon{fill:#552222;}#c3620\_mermaid .error-text{fill:#552222;stroke:#552222;}#c3620\_mermaid .edge-thickness-normal{stroke-width:1px;}#c3620\_mermaid .edge-thickness-thick{stroke-width:3.5px;}#c3620\_mermaid .edge-pattern-solid{stroke-dasharray:0;}#c3620\_mermaid .edge-thickness-invisible{stroke-width:0;fill:none;}#c3620\_mermaid .edge-pattern-dashed{stroke-dasharray:3;}#c3620\_mermaid .edge-pattern-dotted{stroke-dasharray:2;}#c3620\_mermaid .marker{fill:#333333;stroke:#333333;}#c3620\_mermaid .marker.cross{stroke:#333333;}#c3620\_mermaid svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#c3620\_mermaid p{margin:0;}#c3620\_mermaid .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#333;}#c3620\_mermaid .cluster-label text{fill:#333;}#c3620\_mermaid .cluster-label span{color:#333;}#c3620\_mermaid .cluster-label span p{background-color:transparent;}#c3620\_mermaid .label text,#c3620\_mermaid span{fill:#333;color:#333;}#c3620\_mermaid .node rect,#c3620\_mermaid .node circle,#c3620\_mermaid .node ellipse,#c3620\_mermaid .node polygon,#c3620\_mermaid .node path{fill:#ECECFF;stroke:#9370DB;stroke-width:1px;}#c3620\_mermaid .rough-node .label text,#c3620\_mermaid .node .label text{text-anchor:middle;}#c3620\_mermaid .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#c3620\_mermaid .node .label{text-align:center;}#c3620\_mermaid .node.clickable{cursor:pointer;}#c3620\_mermaid .arrowheadPath{fill:#333333;}#c3620\_mermaid .edgePath .path{stroke:#333333;stroke-width:2.0px;}#c3620\_mermaid .flowchart-link{stroke:#333333;fill:none;}#c3620\_mermaid .edgeLabel{background-color:rgba(232,232,232, 0.8);text-align:center;}#c3620\_mermaid .edgeLabel p{background-color:rgba(232,232,232, 0.8);}#c3620\_mermaid .edgeLabel rect{opacity:0.5;background-color:rgba(232,232,232, 0.8);fill:rgba(232,232,232, 0.8);}#c3620\_mermaid .labelBkg{background-color:rgba(232, 232, 232, 0.5);}#c3620\_mermaid .cluster rect{fill:#ffffde;stroke:#aaaa33;stroke-width:1px;}#c3620\_mermaid .cluster text{fill:#333;}#c3620\_mermaid .cluster span{color:#333;}#c3620\_mermaid div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(80, 100%, 96.2745098039%);border:1px solid #aaaa33;border-radius:2px;pointer-events:none;z-index:100;}#c3620\_mermaid .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#333;}#c3620\_mermaid :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}

A

B

C

See [more...](https://nicegui.io/documentation/mermaid)

[HTML Element](https://nicegui.io/documentation/html)[_link_](https://nicegui.io/documentation/section_text_elements#html_element)

Renders arbitrary HTML onto the page, wrapped in the specified tag. [Tailwind](https://v3.tailwindcss.com/) can be used for styling. You can also use ui.add\_head\_html to add html code into the head of the document and ui.add\_body\_html to add it into the body.

<table class="docutils field-list" frame="void" rules="none"><tbody valign="top"><tr class="field"><th class="field-name">content:</th><td class="field-body">the HTML code to be displayed</td></tr><tr class="field"><th class="field-name">tag:</th><td class="field-body">the HTML tag to wrap the content in (default: "div")</td></tr></tbody></table>

_circle__circle__circle_

main.py

`from nicegui import ui  ui.html('This is <strong>HTML</strong>.')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

This is **HTML**.

See [more...](https://nicegui.io/documentation/html)

Other HTML Elements

[_link_](https://nicegui.io/documentation/section_text_elements#other_html_elements)

There is also an `html` module that allows you to insert other HTML elements like `<span>`, `<div>`, `<p>`, etc. It is equivalent to using the `ui.element` method with the `tag` argument.

Like with any other element, you can add classes, style, props, tooltips and events. One convenience is that the keyword arguments are automatically added to the element's `props` dictionary.

_Added in version 2.5.0_

_circle__circle__circle_

main.py

`from nicegui import html, ui  with html.section().style('font-size: 120%'):     html.strong('This is bold.') \         .classes('cursor-pointer') \         .on('click', lambda: ui.notify('Bold!'))     html.hr()     html.em('This is italic.').tooltip('Nice!')     with ui.row():         html.img().props('src=https://placehold.co/60')         html.img(src='https://placehold.co/60')  ui.run()`

_content\_copy_

_circle__circle__circle_

NiceGUI

**This is bold.**

---

_This is italic._

![](https://placehold.co/60)![](https://placehold.co/60)

[](https://nicegui.io/imprint_privacy)
