import sys
from os.path import join

from kivy.app import App
from kivy.core.window import Window, Keyboard
from kivy.uix.screenmanager import Screen
from json import load as load_json
from cnaviscreen import CNaviScreen


class CSettingsScreen(CNaviScreen):
    CONTROL_DEFAULTS_FILENAME = "control_defaults.json"

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

    def set_control_defaults(self, name):
        """
        Loads and applies default control settings.
        :param name: Control type name ("keys" or "touch" or "gamepad")
        """
        app = App.get_running_app()
        try:
            with open(join(app.DATA_PATH, self.CONTROL_DEFAULTS_FILENAME), "r", encoding="utf8") as read_file:
                default_data = load_json(read_file)
        except FileNotFoundError:
            print("Error: control defaults file not found.", file=sys.stderr)
            return
        except OSError as err:
            print("Error: {}".format(err), file=sys.stderr)
            return

        if name in default_data.keys():
            default = default_data[name]
            for key in self._controls.keys():
                if key in default:
                    self._controls.update({key:default[key]})
                    self.set_control_label(key, default[key])

    def on_key_escape(self):
        app = App.get_running_app()
        app.root.current = 'menu_screen'
        return True

    def on_keydown(self, obj, keycode, scancode, text, modifiers):
        if self._listen_to in self._controls.keys():
            key = Keyboard.keycode_to_string(obj, keycode)
            if key != "escape":
                self._controls.update({self._listen_to: "Key: " + key})
                self.set_control_label(self._listen_to, "Key: " + key)
            else:
                self.set_control_label(self._listen_to, self._controls[self._listen_to])
            self._listen_to = ""
            return True

        else:
            return super().on_key_down(obj, keycode, scancode, text, modifiers)

    def on_joy_axis(self, win, joy_id, axis_id, value):
        app = App.get_running_app()
        rel_val = value / 0x8000    # 16 bit int to float -1..1
        if (self._listen_to in self._controls.keys()) and \
                (abs(rel_val) > 0.5) and \
                (joy_id < app.MAX_JOYSTICKS) and \
                (axis_id < app.MAX_JOYSTICK_AXES):
            params = {"type": ["joy", "axis"], "joy_id": joy_id, "axis_id": axis_id, "dx": rel_val}
            for name, control in app.controls.items():
                if control.equals(**params):
                    self._controls.update({self._listen_to: name})
                    self.set_control_label(self._listen_to, name)
                    self._listen_to = ""
                    return True
        return False

    def on_joy_hat(self, win, joy_id, hat_id, value):
        app = App.get_running_app()
        if (self._listen_to in self._controls.keys()) and \
                (abs(value[0]) + abs(value[1]) > 0) and \
                (joy_id < app.MAX_JOYSTICKS) and \
                (hat_id < app.MAX_JOYSTICK_HATS):
            params = {"type": ["joy", "hat"], "joy_id": joy_id, "hat_id": hat_id, "dx": value[0], "dy": value[1]}
            for name, control in app.controls.items():
                if control.equals(**params):
                    self._controls.update({self._listen_to: name})
                    self.set_control_label(self._listen_to, name)
                    self._listen_to = ""
                    return True
        return False

    def on_joy_button_down(self, win, joy_id, button_id):
        app = App.get_running_app()
        if (self._listen_to in self._controls.keys()) and \
                (joy_id < app.MAX_JOYSTICKS) and \
                (button_id < app.MAX_JOYSTICK_BUTTONS):
            self._controls.update({self._listen_to: "Button: " + str(button_id)})
            self.set_control_label(self._listen_to, "Button: " + str(button_id))
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
            self.set_control_label(self._listen_to, "do something")

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
        Window.bind(on_joy_axis=self.on_joy_axis)
        Window.bind(on_joy_hat=self.on_joy_hat)
        Window.bind(on_joy_button_down=self.on_joy_button_down)

    def on_leave(self, *args):
        app = App.get_running_app()

        app.left_control = self._controls["left"]
        app.right_control = self._controls["right"]
        app.drop_control = self._controls["drop"]
        app.flip_control = self._controls["flip"]
        app.rotate_control = self._controls["rotate"]

        app.save_user_config()
        Window.unbind(on_key_down=self.on_keydown)
        Window.unbind(on_joy_axis=self.on_joy_axis)
        Window.unbind(on_joy_hat=self.on_joy_hat)
        Window.unbind(on_joy_button_down=self.on_joy_button_down)
