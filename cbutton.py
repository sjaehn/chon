from kivy.core.window import Window
from kivy.properties import StringProperty, OptionProperty
from kivy.uix.button import Button


class CButton(Button):
    name = StringProperty("")
    selected = OptionProperty("", options=["", "selected", "entered"])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_move)

    def on_mouse_move(self, window, pos):
        if self.collide_point(*pos) and (self.selected != "entered"):
            self.selected = "selected"
        else:
            self.selected = ""

