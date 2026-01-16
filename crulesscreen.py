from kivy.app import App
from cnaviscreen import CNaviScreen


class CRulesScreen(CNaviScreen):

    def on_key_escape(self):
        app = App.get_running_app()
        app.root.current = 'menu_screen'
        return True

