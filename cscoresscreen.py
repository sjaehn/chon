from datetime import date
from os import makedirs
from os.path import join, isfile

from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from json import load as load_json
from json import dumps

from cscoreinput import CScoreInput
from cscorewidget import CScoreWidget


class CScoresScreen(Screen):
    MAX_SCORES = 10
    scores_head = []
    scores_data_before = []
    scores_data_after = []
    scores_data_game = None
    scores_data_game_after = None
    name_input = None

    def load_scores(self):
        app = App.get_running_app()

        # Create user data dir, if not exists
        makedirs(app.user_data_dir, exist_ok=True)

        # Check if scores file exists, otherwise use stub
        scores_filename = join(app.user_data_dir, "scores.json")
        scores_stub_filename = join(app.DATA_PATH, "scores.json")
        source = scores_filename if isfile(scores_filename) else scores_stub_filename

        # Read data
        with open(source, "r", encoding="utf8") as read_file:
            raw_data = load_json(read_file)
            self.scores_head = raw_data[0]
            scores_data = raw_data[1:]
            self.scores_data_before = [line.copy() for line in scores_data]
            self.scores_data_after = []

    def get_game_scores(self):
        screen_manager: ScreenManager = App.get_running_app().root
        game_screen = screen_manager.get_screen('game_screen')

        # Game over?
        if game_screen.ids.game_over_label.opacity != 0:
            # Get game data
            self.scores_data_game = {"pos": None,
                                     "name": "YOUR NAME",
                                     "date": str(date.today()),
                                     "lev": 1 + game_screen.nr_molecules // 10,
                                     "mol": game_screen.nr_molecules,
                                     "score": game_screen.score}

            # Reset game
            game_screen.reset()

            # Remove continue button
            menu_screen = screen_manager.get_screen('menu_screen')
            menu_screen.remove_continue_button()

        # Or game still running?
        else:
            self.scores_data_game = None

        self.scores_data_game_after = None

    def mix_scores(self):
        if self.scores_data_game:
            # Game score inside high scores?
            # Split list to insert game score
            for line_nr in range(len(self.scores_data_before)):
                line = self.scores_data_before[line_nr]
                if self.scores_data_game["score"] > line["score"]:
                    self.scores_data_game.update({"pos": line_nr + 1})
                    self.scores_data_after = self.scores_data_before[line_nr:]
                    self.scores_data_before = self.scores_data_before[:line_nr]

                    # Renumber positions after
                    for line_after in self.scores_data_after:
                        line_after.update({"pos": line_after["pos"] + 1})

                    # Limit data before + 1 (game score) + data after to MAX_SCORES
                    self.scores_data_after = self.scores_data_after[: self.MAX_SCORES - 1 - len(self.scores_data_before)]

                    break

            # Or game score outside high scores
            if self.scores_data_game["pos"] is None:
                # ... but inside top MAX_SCORES
                if len(self.scores_data_before) < self.MAX_SCORES:
                    self.scores_data_game.update({"pos": len(self.scores_data_before) + 1})

                # Otherwise: game scores outside the list
                else:
                    self.scores_data_game_after = self.scores_data_game
                    self.scores_data_game_after.update({"pos": "---"})
                    self.scores_data_game = None

    def save_scores(self):
        app = App.get_running_app()
        scores_data = [self.scores_head] + self.scores_data_before
        scores_data += [self.scores_data_game] if self.scores_data_game is not None else []
        scores_data += self.scores_data_after
        scores_data = scores_data[: self.MAX_SCORES + 1]

        with open(join(app.user_data_dir, "scores.json"), "w", encoding="utf8") as write_file:
            write_file.write(dumps(scores_data))

    @staticmethod
    def str_right(text, length):
        return " " * ((length - len(text)) if length > len(text) else 0) + text

    def build_scores_line(self, line, scores_head, **kwargs):
        scores_table = self.ids.scores_table
        total = sum(value for value in scores_head.values())

        if line is not None:
            for key in line:
                text = str(line[key])
                if type(line[key]) is int:
                    text = self.str_right(text, scores_head[key])
                text = text[:scores_head[key]]
                scores_table.add_widget(CScoreWidget(text=text,
                                                     font_size=0.02 * min(self.height, 1.333 * self.width),
                                                     size_hint=(scores_head[key] / total, 1.0 / 15.0),
                                                     **kwargs))

        else:
            for key in self.scores_head.keys():
                scores_table.add_widget(CScoreWidget(text=" ",
                                                     font_size=0.02 * min(self.height, 1.333 * self.width),
                                                     size_hint=(scores_head[key] / total, 1.0 / 15.0),
                                                     **kwargs))

    def build_scores_table(self, *args):
        scores_table = self.ids.scores_table
        scores_table.clear_widgets()

        # Work with a device-adapted copy of scores_head
        scores_head = self.scores_head.copy()
        # Mobile
        if 1.333 * self.width < self.height:
            scores_head.update({"name": self.scores_head["name"] // 3})
            scores_head.update({"date": 4})
        # Pad
        elif self.width < self.height:
            scores_head.update({"name": self.scores_head["name"] // 2})

        # Add table head
        total = sum(value for value in scores_head.values())
        for key in scores_head.keys():
            scores_table.add_widget(CScoreWidget(text=self.str_right(key, int(0.5 * (scores_head[key] + len(key)))),
                                                 font_size=0.02 * min(self.height, 1.333 * self.width),
                                                 size_hint=(scores_head[key] / total, 1.0 / 15.0)))
        for key in scores_head.keys():
            scores_table.add_widget(CScoreWidget(text="-" * scores_head[key],
                                                 font_size=0.02 * min(self.height, 1.333 * self.width),
                                                 size_hint=(scores_head[key] / total, 1.0 / 15.0)))

        # All scores before game score
        for line in self.scores_data_before:
            self.build_scores_line(line, scores_head)

        # Game score if inside high scores (otherwise, empty line)
        if self.scores_data_game is not None:
            for key in self.scores_data_game:
                value = self.scores_data_game[key]
                text = str(value)
                if type(value) is int:
                    text = self.str_right(text, scores_head[key])
                text = text[:scores_head[key]]
                if key == "name":
                    self.name_input = CScoreInput(text=text,
                                                  font_size=0.02 * min(self.height, 1.333 * self.width),
                                                  size_hint=(scores_head[key] / total, 1.0 / 15.0))
                    scores_table.add_widget(self.name_input)
                    self.name_input.bind(focus=self.on_input_text_changed)
                else:
                    scores_table.add_widget(CScoreWidget(text=text,
                                                         font_size=0.02 * min(self.height, 1.333 * self.width),
                                                         size_hint=(scores_head[key] / total, 1.0 / 15.0),
                                                         color = [1, 0, 0, 1]))

        # All scores after game score
        for line in self.scores_data_after:
            self.build_scores_line(line, scores_head)

        # Game score outside high scores
        if self.scores_data_game_after is not None:
            # Empty line
            for key in self.scores_head.keys():
                scores_table.add_widget(CScoreWidget(text=" ",
                                                     font_size=0.02 * min(self.height, self.width),
                                                     size_hint=(scores_head[key] / total, 1.0 / 15.0)))
            # Game score
            self.build_scores_line(self.scores_data_game_after, scores_head, color=[1, 0, 0, 1])

    def on_enter(self, *args):
        self.load_scores()
        self.get_game_scores()
        self.mix_scores()
        self.save_scores()
        self.build_scores_table()
        self.bind(pos=self.build_scores_table, size=self.build_scores_table)

    def on_leave(self, *args):
        self.bind(pos=self.build_scores_table, size=self.build_scores_table)

    def on_input_text_changed(self, instance, value):
        # Input focus leave
        if not value:
            self.scores_data_game["name"] = self.name_input.text[:24]
            self.save_scores()