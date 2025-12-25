from os.path import join

from kivy.app import App
from kivy.properties import StringProperty
from kivy.uix.label import Label


class CText(Label):
    source = StringProperty("")

    def __init__(self, source="",**kwargs):
        super().__init__(**kwargs)
        self.load()
        self.bind(source=self.load)

    def load(self, *args):
        if self.source:
            app = App.get_running_app()
            with open(join(app.DATA_PATH, self.source), "r") as read_file:
                self.text = read_file.read()
