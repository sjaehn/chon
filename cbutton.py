from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.button import Button


class CButton(Button):
    name = StringProperty("")
    hover = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_over)

    def on_mouse_over(self, window, pos):
        if self.collide_point(*pos):
            self.hover = True
        else:
            self.hover = False

