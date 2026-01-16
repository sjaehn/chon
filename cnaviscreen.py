from kivy.core.window import Window, Keyboard
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen


class CNaviScreen(Screen):
    """
    Screen class which allows to navigate between listed child widgets. Child widgets to navigate between must be listed
    in both, ids and navigable_ids.
    """

    JOYSTICK_ENTER_BUTTON = 0
    JOYSTICK_ESCAPE_BUTTON = 1

    navigable_ids = ListProperty([])
    """
    ListProperty containing all navigable ids.
    """

    def select_widget(self, param: str | int | None = None, value: bool = True):
        """
        Selects or unselects a widget (or all widgets) from navigable_ids.
        :param param: Index number of the widget or ID of the widget or None for all widgets.
        :param value: True for select, False for unselect.
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
        self.select_widget(param, False)

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
        Navigates one widget upwards.
        """
        if self.navigable_ids:
            selection = self.get_selected_widget_id()
            selection_idx = self.navigable_ids.index(selection) if selection in self.navigable_ids else -1
            selection_idx = selection_idx - 1 if selection_idx > 0 else 0
            self.unselect_widget()
            self.select_widget(selection_idx)

    def go_down(self):
        """
        Navigates one widget downwards.
        """
        if self.navigable_ids:
            selection = self.get_selected_widget_id()
            selection_idx = self.navigable_ids.index(selection) if selection in self.navigable_ids else -1
            selection_idx = selection_idx + 1 if selection_idx + 1 < len(self.navigable_ids) else -1
            self.unselect_widget()
            self.select_widget(selection_idx)

    def activate_selected(self):
        """
        Activates selected widget.
        """
        if self.navigable_ids:
            selection = self.get_selected_widget_id()
            if selection:
                self.ids[selection].dispatch("on_press")    # TODO Replace by a more generic activation method

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