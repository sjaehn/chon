from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.button import Button


class CButton(Button):
    name = StringProperty("")
    selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_move)

    def on_mouse_move(self, window, pos):
        if self.collide_point(*pos):
            self.selected = True
        else:
            self.selected = False

