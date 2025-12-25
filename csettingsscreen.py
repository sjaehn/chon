from kivy.app import App
from kivy.core.window import Window, Keyboard
from kivy.uix.screenmanager import Screen


class CSettingsScreen(Screen):
    _controls = {}
    _listen_to = ""

    def set_control_label(self, action, control):
        """
        Sets/changes the text of the respective ..._control_label
        :param action: Action.
        :param control: Text to display.
        """
        if action in self._controls.keys():
            self.ids[action + "_control_label"].text = control

    def on_keydown(self, obj, keycode, scancode, text, modifiers):
        if self._listen_to in self._controls.keys():
            key = Keyboard.keycode_to_string(obj, keycode)
            self._controls.update({self._listen_to: "Key: " + key})
            self.set_control_label(self._listen_to, "Key: " + key)
            self._listen_to = ""

    def on_touch(self, t_type, touch):
        app = App.get_running_app()

        # Listener active?
        if self._listen_to not in self._controls.keys():
            return False

        # Exclude other touchable widgets
        for name, widget in self.ids.items():
            if not name.endswith("_control_label"):
                if widget.collide_point(touch.ox, touch.oy):
                    return False

        # Scan for matching control
        dx = touch.x - touch.ox
        dy = touch.y - touch.oy
        params = {"type": ["touch", t_type],
                  "dx": dx,
                  "dy": dy,
                  "is_double_tap": touch.is_double_tap,
                  "is_triple_tap": touch.is_triple_tap}
        for name, control in app.controls.items():
            if control.equals(**params):
                self._controls.update({self._listen_to: name})
                self.set_control_label(self._listen_to, name)
                self._listen_to = ""
                return True

        return False


    def on_touch_move(self, touch):
        return self.on_touch("move", touch)

    def on_touch_up(self, touch):
        return self.on_touch("up", touch)

    def listen_to(self, action):
        """
        Sets the action to listen to.
        :param action: Action.
        """
        # Not listening yet
        if (self._listen_to == "") and (action in self._controls.keys()):
            self._listen_to = action
            self.set_control_label(self._listen_to, "Press any key")

        # Otherwise: Do not listen anymore
        elif (self._listen_to == action) and (action in self._controls.keys()):
            self.set_control_label(self._listen_to, self._controls[self._listen_to])
            self._listen_to = ""

    def on_enter(self, *args):
        app = App.get_running_app()

        self._controls = {"left": app.left_control,
                         "right": app.right_control,
                         "drop": app.drop_control,
                         "flip": app.flip_control,
                         "rotate": app.rotate_control}

        for action in self._controls.keys():
            self.set_control_label(action, self._controls[action])

        Window.bind(on_key_down=self.on_keydown)

    def on_leave(self, *args):
        app = App.get_running_app()

        app.left_control = self._controls["left"]
        app.right_control = self._controls["right"]
        app.drop_control = self._controls["drop"]
        app.flip_control = self._controls["flip"]
        app.rotate_control = self._controls["rotate"]

        app.save_user_config()
        Window.unbind(on_key_down=self.on_keydown)
