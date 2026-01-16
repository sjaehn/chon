from kivy.app import App
from kivy.core.window import Keyboard
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.weakproxy import WeakProxy

from ccontinuebutton import CContinueButton
from ccontrol import CControl
from cnaviscreen import CNaviScreen


class CMenuScreen(CNaviScreen):
    """
    Main menu screen class.
    """
    continue_button = None
    _started = False

    def add_continue_button(self):
        """
        Adds a new continue button.
        """
        if self.continue_button is None:
            self.continue_button = CContinueButton()
            button_box: BoxLayout = self.ids.button_box
            button_box.add_widget(self.continue_button, index=-1)

            # Register in ids and navigable_ids
            self.ids["continue_button"] = WeakProxy(self.continue_button)
            self.navigable_ids.insert(1, "continue_button")

            # Also re-label start button to restart
            start_button = self.ids.start_button
            start_button.name = "Restart"

    def remove_continue_button(self):
        """
        Removes the continue button.
        """
        if self.continue_button is not None:
            button_box: BoxLayout = self.ids.button_box
            button_box.remove_widget(self.continue_button)
            self.continue_button = None

            # Unregister from ids and navigable_ids
            del self.ids["continue_button"]
            self.navigable_ids.remove("continue_button")

    def goto_game_screen(self, *args):
        self.manager.current = "game_screen"

    def reset_and_goto_game_screen(self, *args):
        """
        Starts a new game. Resets game screen data and goto game screen.
        :param args: Unused.
        """
        screen_manager: ScreenManager = App.get_running_app().root
        game_screen = screen_manager.get_screen('game_screen')
        game_screen.reset()

        self.goto_game_screen()

    def after_init(self):
        """
        Called from App upon start after build. Initializes everything what cannot be initialized before.
        """
        if not self._started:
            app = App.get_running_app()

            # Add keyboard to controls (not possible in app module)
            keycodes = Keyboard.keycodes.keys()
            for keycode in keycodes:
                app.controls.update({"Key: " + keycode: CControl(type=["key", "down"], keycode=keycode)})

            self._started = True