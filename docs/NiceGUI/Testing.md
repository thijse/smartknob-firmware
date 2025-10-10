_Testing_

[Project Structure](https://nicegui.io/documentation/project_structure)[_link_](https://nicegui.io/documentation/section_testing#project_structure)

The NiceGUI package provides a [pytest plugin](https://docs.pytest.org/en/stable/how-to/writing_plugins.html) which can be activated via `pytest_plugins = ['nicegui.testing.plugin']`. This makes specialized [fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html) available for testing your NiceGUI user interface. With the [`screen` fixture](https://nicegui.io/documentation/screen) you can run the tests through a headless browser (slow) and with the [`user` fixture](https://nicegui.io/documentation/user) fully simulated in Python (fast). If you only want one kind of test fixtures, you can also use the plugin `nicegui.testing.user_plugin` or `nicegui.testing.screen_plugin`.

There are a multitude of ways to structure your project and tests. Here we only present two approaches which we found useful, one for [small apps and experiments](https://nicegui.io/documentation/project_structure#simple) and a [modular one for larger projects](https://nicegui.io/documentation/project_structure#modular). You can find more information in the [pytest documentation](https://docs.pytest.org/en/stable/contents.html).

See [more...](https://nicegui.io/documentation/project_structure)

[User Fixture](https://nicegui.io/documentation/user)[_link_](https://nicegui.io/documentation/section_testing#user_fixture)

We recommend utilizing the `user` fixture instead of the [`screen` fixture](https://nicegui.io/documentation/screen) wherever possible because execution is as fast as unit tests and it does not need Selenium as a dependency when loaded via `pytest_plugins = ['nicegui.testing.user_plugin']`. The `user` fixture cuts away the browser and replaces it by a lightweight simulation entirely in Python. See [project structure](https://nicegui.io/documentation/project_structure) for a description of the setup.

You can assert to "see" specific elements or content, click buttons, type into inputs and trigger events. We aimed for a nice API to write acceptance tests which read like a story and are easy to understand. Due to the fast execution, the classical [test pyramid](https://martinfowler.com/bliki/TestPyramid.html), where UI tests are considered slow and expensive, does not apply anymore.

_circle__circle__circle_

example

`await user.open('/') user.find('Username').type('user1') user.find('Password').type('pass1').trigger('keydown.enter') await user.should_see('Hello user1!') user.find('logout').click() await user.should_see('Log in')`

**NOTE:** The `user` fixture is quite new and still misses some features. Please let us know in separate feature requests [over on GitHub](https://github.com/zauberzeug/nicegui/discussions/new?category=ideas-feature-requests).

See [more...](https://nicegui.io/documentation/user)

[Screen Fixture](https://nicegui.io/documentation/screen)[_link_](https://nicegui.io/documentation/section_testing#screen_fixture)

The `screen` fixture starts a real (headless) browser to interact with your application. This is only necessary if you have browser-specific behavior to test. NiceGUI itself is thoroughly tested with this fixture to ensure each component works as expected. So only use it if you have to.

_circle__circle__circle_

example

`from selenium.webdriver.common.keys import Keys  screen.open('/') screen.type(Keys.TAB) # to focus on the first input screen.type('user1') screen.type(Keys.TAB) # to focus the second input screen.type('pass1') screen.click('Log in') screen.should_contain('Hello user1!') screen.click('logout') screen.should_contain('Log in')`

See [more...](https://nicegui.io/documentation/screen)
