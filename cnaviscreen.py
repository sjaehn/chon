from kivy.core.window import Window, Keyboard
from kivy.properties import ListProperty
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner


class CNaviScreen(Screen):
    """
    Screen class which allows to navigate between listed child widgets. Child widgets to navigate between must be listed
    in both, ids and navigable_ids.
    """

    JOYSTICK_ENTER_BUTTON = 0
    JOYSTICK_ESCAPE_BUTTON = 1
    JOYSTICK_AXIS_THRESHOLD = 0.2

    navigable_ids = ListProperty([])
    """
    ListProperty containing all navigable ids.
    """

    def select_widget(self, param: str | int | None = None, value: str = "selected"):
        """
        Selects or unselects a widget (or all widgets) from navigable_ids.
        :param param: Index number of the widget or ID of the widget or None for all widgets.
        :param value: "" or "selected" or "entered.
        """

        # None = All
        if param is None:
            for id in self.navigable_ids:
                self.ids[id].selected = value

        # By index
        if isinstance(param, int):
            self.ids[self.navigable_ids[param]].selected = value

        # By ID
        if isinstance(param, str):
            self.ids[param].selected = value

    def unselect_widget(self, param: str | int | None = None):
        """
        Unselects a widget (or all widgets) from navigable_ids.
        :param param: Index number of the widget or ID of the widget or None for all widgets.
        """
        self.select_widget(param, "")

    def get_selected_widget_id(self):
        """
        Gets the first selected widget id from the navigable ids.
        :return: ID of the first selected widget (or "").
        """
        for id in self.navigable_ids:
            widget =self.ids[id]
            if widget.selected:
                return id
        return ""

    def go_up(self):
        """
        Go upwards: Either makes an upwards action on an "entered" widget (e.g., decreases its value) or navigates one
        widget upwards.
        """
        if self.navigable_ids:
            selection = self.get_selected_widget_id()
            if selection in self.navigable_ids:
                widget = self.ids[selection]

                # "entered" selection: Action on entered widget
                if widget.selected == "entered":

                    # Slider: Same as mouse wheel
                    if isinstance(widget, Slider):
                        if widget.step:
                            widget.value = max(widget.min, widget.value - widget.step)
                        else:
                            widget.value = max(widget.min, widget.value - (widget.max - widget.min) / 20)

                    # Spinner: Set prev item
                    elif isinstance(widget, Spinner):
                        if widget.values and (widget.text in widget.values):
                            idx = widget.values.index(widget.text)
                            idx = idx - 1 if idx - 1 > 0 else 0
                            widget.text = widget.values[idx]
                            widget.is_open = False  # and close dropdown

                # "selected": Move selection selected 1 pos up
                elif widget.selected == "selected":
                    selection_idx = self.navigable_ids.index(selection)
                    selection_idx = selection_idx - 1 if selection_idx > 0 else 0
                    self.unselect_widget()
                    self.select_widget(selection_idx)

            # No selected widget: Select the first one
            else:
                self.unselect_widget()
                self.select_widget(0)

    def go_down(self):
        """
        Go downwards: Either makes a downwards action on an "entered" widget (e.g., increases its value) or navigates
        one widget downwards.
        """
        if self.navigable_ids:
            selection = self.get_selected_widget_id()
            if selection in self.navigable_ids:
                widget = self.ids[selection]

                # "entered" selection: Action on entered widget
                if widget.selected == "entered":

                    # Slider: Same as mouse wheel
                    if isinstance(widget, Slider):
                        if widget.step:
                            widget.value = min(widget.max, widget.value + widget.step)
                        else:
                            widget.value = min(widget.max, widget.value + (widget.max - widget.min) / 20)

                    # Spinner: Set next item
                    elif isinstance(widget, Spinner):
                        if widget.values and (widget.text in widget.values):
                            idx = widget.values.index(widget.text)
                            idx = idx + 1 if idx + 1 < len(widget.values) else -1
                            widget.text = widget.values[idx]
                            widget.is_open = False  # and close dropdown

                # "selected": Move selection selected 1 pos up
                elif widget.selected == "selected":
                    selection_idx = self.navigable_ids.index(selection)
                    selection_idx = selection_idx + 1 if selection_idx + 1 < len(self.navigable_ids) else -1
                    self.unselect_widget()
                    self.select_widget(selection_idx)

            # No selected widget: Select the first one
            else:
                self.unselect_widget()
                self.select_widget(0)

    def activate_selected(self):
        """
        Activates selected widget.
        """
        if self.navigable_ids:
            selection = self.get_selected_widget_id()
            if selection:
                widget = self.ids[selection]

                # Spinner, Slider: enter/leave
                if isinstance(widget, Spinner) or isinstance(widget, Slider):
                    if widget.selected == "selected":
                        widget.selected = "entered"
                    elif widget.selected == "entered":
                        widget.selected = "selected"

                # Button: press
                elif isinstance(widget, Button):
                    if widget.selected == "selected":
                        self.ids[selection].dispatch("on_press")

    def on_key_escape(self):
        """
        Behaviour for escape key presses. Can be overridden by child classes.
        :return: True or False. Kivy exits the app upon escape key press and return False on default.
        """
        return False

    def on_key_down(self, window, keycode, scancode, text, modifiers):
        key = Keyboard.keycode_to_string(window, keycode)

        if key == "escape":
            return self.on_key_escape()

        if (key == "spacebar") or (key == "enter"):
            self.activate_selected()
        elif (key == "up") or (key == "left"):
            self.go_up()
        elif (key == "down") or (key == "right"):
            self.go_down()

        return True

    def on_joy_axis(self, win, joy_id, axis_id, value):
        # Override to support
        pass

    def on_joy_hat(self, win, joy_id, hat_id, value):
        if (value[0] == -1) or (value[1] == 1):
            self.go_up()
        if (value[0] == 1) or (value[1] == -1):
            self.go_down()
        return True

    def on_joy_button_down(self, win, joy_id, button_id):
        if button_id == self.JOYSTICK_ESCAPE_BUTTON:
            return self.on_key_escape()
        if button_id == self.JOYSTICK_ENTER_BUTTON:
            self.activate_selected()
        return True

    def on_enter(self, *args):
        self.unselect_widget()
        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_joy_axis=self.on_joy_axis)
        Window.bind(on_joy_hat=self.on_joy_hat)
        Window.bind(on_joy_button_down=self.on_joy_button_down)

    def on_leave(self, *args):
        Window.unbind(on_key_down=self.on_key_down)
        Window.unbind(on_joy_axis=self.on_joy_axis)
        Window.unbind(on_joy_hat=self.on_joy_hat)
        Window.unbind(on_joy_button_down=self.on_joy_button_down)