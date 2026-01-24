import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Keyboard
from kivy.input import MotionEvent
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import ScreenManager

from chover import CHover
from cmolecule import CMolecule
from cmoleculewidget import CMoleculeWidget
from cnaviscreen import CNaviScreen
from creactor import CReactor
from ctools import fib, dict_get_or_create


class CGameScreen(CNaviScreen):
    """
    CGameScreen is a Screen and also hosts the gameplay.
    """

    PAUSE_KEY = "lctrl" # TODO Remove it until the first release.
    MENU_KEY = "escape"
    DESTROY_COUNT = 10

    _timer = None
    _time = 0
    _drop_from = 0
    _bg_filenames = ["bg0" + str(i) + ".jpg" for i in range(2, 7)]
    _bonus_molecules = []
    _joystick_axes = {}

    def reset(self):
        """
        Reset all reactor data to restart/continue.
        """

        app = App.get_running_app()

        if "reactor" in self.ids:
            self.ids.reactor.clear_widgets()
        else:
            pass

        self.reset_act()
        self.set_theme()
        self.score = 0
        self._time = 0
        self.nr_molecules = app.test_nr_molecules
        self._drop_from = 0

        self.ids.game_over_label.opacity = 0

    def game_over(self):
        """
        Displays "game over".
        """
        # Show "Game over"
        game_over_label = self.ids.game_over_label
        game_over_label.opacity = 1

        # Remove continue button from main menu
        screen_manager: ScreenManager = App.get_running_app().root
        menu_screen = screen_manager.get_screen('menu_screen')
        menu_screen.remove_continue_button()

        # Schedule switch to scores screen
        if self._timer is not None:
            self.stop_timer()
        self._timer = Clock.schedule_once(self.switch_to_scores_screen, 2)

    def set_theme(self):
        """
        Randomly chooses a theme and sets filename for background images and sets atom images.
        """
        app = App.get_running_app()
        reactor = self.ids.reactor
        bonus = self.ids.bonus

        # Randomize but keep last list element to get sure to switch
        random.shuffle(app.themes[:-1])

        # Put this theme back to the end of the list
        theme = app.themes[0]
        app.themes.pop(0)
        app.themes.append(theme)

        # Set new bg filename and re-draw all molecules
        self.bg_filename = theme["bg"]
        bonus.draw_canvas()
        for child in reactor.children:
            if type(child) is CMoleculeWidget:
                child.draw_canvas()

    def start_timer(self):
        """
        Starts timer event scheduler.
        """
        self._timer = Clock.schedule_interval(self.on_time, 0.025)

    def stop_timer(self):
        """
        Stops timer event scheduler.
        """
        if self._timer is not None:
            self._timer.cancel()
        self._timer = None

    def start_stop_timer(self):
        """
        Starts or stops timer event scheduler.
        """
        if self._timer is None:
            self.start_timer()
        else:
            self.stop_timer()

    def reset_act(self):
        """
        Initializes act with en empty molecule.
        """

        if (not "reactor" in self.ids) or (not "act" in self.ids):
            return

        reactor = self.ids.reactor
        act = self.ids.act

        act.col = reactor.COLS // 2
        act.row = reactor.ROWS - 1
        act.job = ""
        act.params = {}
        act.value = 0
        act.rgba = (0, 0, 0, 0)
        act.set_molecule(CMolecule())

    def spawn_act(self):
        """
        Spawns a new molecule as act on top of the reactor.
        :return: True, if success. Otherwise, False.
        """

        app = App.get_running_app()
        reactor = self.ids.reactor
        act = self.ids.act

        # Step 1: Test mode:
        if app.test_fragment_names:
            choice = next(fragment for fragment in app.fragments if fragment["name"] == app.test_fragment_names[0])
            app.test_fragment_names = app.test_fragment_names[1:] + app.test_fragment_names[:1]

        # Or step 1: Play mode
        else:
            # Step 1: Find all fragments with value <= level + 1
            candidates = [f for f in app.fragments if f["value"] <= self.nr_molecules // 10 + 2]

            # Step 2: New molecule from random selection
            choice = random.choice(candidates)

        molecule = CMolecule(name=choice["name"])
        molecule.parse(atoms=app.atoms, txt=choice["data"])

        # Step 3: Random rotation, flip
        molecule.rotate(random.randint(0, 3))
        if random.randint(0, 1) == 1:
            molecule.h_flip()

        # Step 4: Apply to act
        act.col = (reactor.COLS - molecule.dim[0]) // 2
        act.row = reactor.ROWS - molecule.dim[1]
        act.job = "play"
        act.params = {"count": 0}
        act.value = fib(choice["value"])
        act.rgba = (0, 0, 0, 0)
        act.set_molecule(molecule)

        # Step 5: Also update fragment label
        fragment_label = self.ids.fragment_label
        fragment_label.text = choice["name"]

        # Step 6: Stop if no space
        return not act.collides_with_others(reactor.children)

    def destroy_act(self):
        """
        Proceeds countdown and finally destroys act.
        """
        act = self.ids.act
        bonus = self.ids.bonus
        tube = self.ids.tube

        if act.job == "destroy":
            act.set_job(act.job, {"count": act.params["count"] - 1})
            if act.params["count"] < 0:

                # Show score to be added
                w, h = act.size
                x, y = act.pos
                x += 0.75 * w
                y += h
                hover = CHover(text="+" + str(act.value * 10))
                tube.add_widget(hover)
                hover.size = (0.2 * tube.width, 0.05 * tube.height)
                hover.pos = (min(x, tube.width - hover.width), y)

                # Add score
                self.nr_molecules += 1
                self.score += act.value * 10

                # Next level?
                if self.nr_molecules % 10 == 0:
                    self.set_theme()

                # Get bonus?
                if act.molecule.equals(bonus.molecule):
                    bonus_hover = CHover(text="+" + str(bonus.value))
                    tube.add_widget(bonus_hover)
                    bonus_hover.size = (0.2 * tube.width, 0.05 * tube.height)
                    bonus_hover.pos = (min(x, tube.width - hover.width), y - bonus_hover.height)
                    self.score += bonus.value
                    bonus.set_molecule(CMolecule())
                self.reset_act()

    def merge_to_act(self):
        """
        Merges act with the first mergeable molecule widget from reactor's children, takes
        over its color, adds its value, removes it from reactor.
        :return: True, if merged. Otherwise, False.
        """

        act = self.ids.act
        reactor = self.ids.reactor

        for child in reactor.children:
            if type(child) is CMoleculeWidget:
                n_col = min(child.col, act.col)
                n_row = min(child.row, act.row)
                if act.molecule.connect(child.molecule, (child.col - act.col, child.row - act.row)):
                    act.move_to(n_col, n_row)
                    act.rgba = child.rgba
                    act.value += child.value
                    act.cols, act.rows = act.molecule.dim
                    act.draw_canvas()
                    reactor.remove_widget(child)
                    return True

        return False

    def store_act(self):
        """
        Merges (if possible) or adds act (single obj) to reactor.
        """

        app = App.get_running_app()
        act = self.ids.act
        reactor = self.ids.reactor
        bonus = self.ids.bonus

        # Play boom sound
        app.stop_sfx("drop")
        if ((act.job == "drop") and (act.params["count"] > 0)) or (act.job in ["play", "move"]):
            app.play_sfx("boom")

        # Add score
        if act.job == "drop":
            self.score += act.params["count"]

        # Check and merge
        while self.merge_to_act():
            pass

        # Random color, if not set yet
        if act.rgba == (0, 0, 0, 0):
            act.rgba = (random.randint(0, 3) / 3, random.randint(0, 3) / 3, random.randint(0, 3) / 3, 0.25)

        # Destroy act, if complete
        if not act.molecule.has_free_bonds():
            act.set_job("destroy", {"count": self.DESTROY_COUNT})
            app.play_sfx("bonus" if act.molecule.equals(bonus.molecule) else "success")

        # Otherwise, transfer to reactor
        else:
            # Copy data to a new molecule widget in reactor
            act_copy = CMoleculeWidget(name="", value=act.value, col=act.col, row=act.row, dim=act.molecule.dim,
                                       rgba=act.rgba, job="", params={"count": 0}, size_hint=(None, None))
            act_copy.set_molecule(act.molecule)
            act_copy.pos = reactor.x + reactor.width * act_copy.col / reactor.COLS, reactor.y + act_copy.row * reactor.height / reactor.ROWS
            act_copy.size = (reactor.width * act_copy.cols / reactor.COLS, reactor.height * act_copy.rows / reactor.ROWS)
            reactor.add_widget(act_copy)
            pass

            # Reset act
            self.reset_act()

    def drop_act(self):
        """
        Tries to drop the act molecule widget by 1 step. If this is not possible, then act is stored into reactor.
        :return: True if successful move 1 step down. Otherwise, False.
        """

        act = self.ids.act
        reactor = self.ids.reactor
        app = App.get_running_app()

        # Already last line: Store
        if act.row == 0:
            self.store_act()
            return False

        else:
            n_row = act.row - 1

            # No collision after move down: move
            if not act.collides_with_others(reactor.children, row=n_row):
                act.move_to(act.col, n_row)
                if act.job == "drop":
                    act.params["count"] += 1
                return True

            # Otherwise, just store
            else:
                self.store_act()
                return False

    def drop_molecule_widgets(self):
        """
        Stepwisely tries to drop all child molecule widgets from reactor by 1 block until a drop succeeded.
        :return: True, if at least one molecule widget dropped. Otherwise, False.
        """

        act = self.ids.act
        reactor = self.ids.reactor

        # Only run if act connected but empty
        if act and (not act.molecule):
            children = reactor.children.copy()
            cant_drop = []

            # Try to drop each molecule widget directly
            for child in children:
                if type(child) is CMoleculeWidget:

                    # Molecule widget has been merged in one of the loops before
                    if child not in reactor.children:
                        return True

                    # Transfer child data to act
                    act.col = child.col
                    act.row = child.row
                    act.value = child.value
                    act.rgba = child.rgba
                    act.set_job("drop", {"count": 0})
                    act.set_molecule(child.molecule)
                    reactor.remove_widget(child)

                    # ... and find the first successful drop
                    if self.drop_act() or (act.molecule and act.job == "destroy"):
                        return True

                    # Failed? Keep for drop as a group?
                    else:
                        cant_drop.append(child)

            # Try to drop as group (for recursively connected molecules)
            for cant_drop_widget in cant_drop:

                # Test if molecule widget is floating and find all molecule widgets connected to this molecule widget
                # and floating too.
                group = reactor.list_molecule_widgets_if_floating(cant_drop_widget)
                if group:

                    # Drop the block of blocks by 1 step
                    for group_widget in group:
                        group_widget.pos = (group_widget.col, group_widget.row - 1)

                    return True

        return False

    def h_move_act_to(self, col: int):
        """
        Moves act horizontally if it still fits into the reactor and doesn't collide with other molecules.
        :param col: New col.
        """
        if ("reactor" in self.ids) and ("act" in self.ids):
            reactor: CReactor = self.ids.reactor
            act: CMoleculeWidget = self.ids.act

            if act.col != col:
                row = act.row
                if reactor.fits(act.molecule, col, row):
                    if not reactor.test_collision(act.molecule, col=col, row=act.row):
                        act.move_to(col, row)

                        app = App.get_running_app()
                        app.play_sfx("move")

    def h_move_act(self, d_col: int):
        """
        Moves act horizontally if it still fits into the reactor and doesn't collide with other molecules.
        :param d_col: Change in cols.
        """
        if ("reactor" in self.ids) and ("act" in self.ids):
            act: CMoleculeWidget = self.ids.act
            col = act.col + d_col
            self.h_move_act_to(col)

    def flip_act(self):
        """
        Flips act horizontally. No collision test needed.
        """
        if "act" in self.ids:
            act: CMoleculeWidget = self.ids.act
            molecule:CMolecule = act.molecule.copy()
            molecule.h_flip()
            act.set_molecule(molecule)

            app = App.get_running_app()
            app.play_sfx("flip")

    def rotate_act(self):
        """
        Rotates act clockwise if it still fits into the reactor and doesn't collide with other molecules.
        """
        if ("reactor" in self.ids) and ("act" in self.ids):
            reactor: CReactor = self.ids.reactor
            act: CMoleculeWidget = self.ids.act
            molecule: CMolecule = act.molecule.copy()
            molecule.rotate()
            if reactor.fits(molecule, act.col, act.row):
                if not reactor.test_collision(molecule, act.col, act.row):
                    act.set_molecule(molecule)

                    app = App.get_running_app()
                    app.play_sfx("flip")

    def create_bonus(self):
        """
        Creates a new bonus molecule.
        """
        app = App.get_running_app()
        bonus = self.ids.bonus

        # Step 1 in test mode:
        if app.test_bonus_names:
            choice = next(b for b in app.bonus_molecules if b["name"] == app.test_bonus_names[0])
            app.test_bonus_names = app.test_bonus_names[1:] + app.test_bonus_names[:1]

        # Or step 1 in play mode: Check if bonus molecules with value <= level + 1 already in _bonus_molecules
        # Random insert, but not on last pos
        else:
            for bonus_molecule in app.bonus_molecules:
                if (bonus_molecule not in self._bonus_molecules) and (bonus_molecule["value"] <= 2 + self.nr_molecules // 10):
                    if len(self._bonus_molecules) > 1:
                        l = self._bonus_molecules[:-1]
                        l.insert(random.randrange(start=0, stop=len(l)), bonus_molecule)
                        self._bonus_molecules = l + [self._bonus_molecules[-1]]
                    else:
                        self._bonus_molecules.insert(0, bonus_molecule)

            # Step 2: Get the first bonus molecule and put it back to the end of the list
            choice = self._bonus_molecules[0]
            self._bonus_molecules = self._bonus_molecules[1:] + self._bonus_molecules[:1]

        # Step 3: New block from random selection
        bonus.name = choice["name"]
        bonus.value = fib(choice["value"] + 1) * 100
        bonus.set_molecule(CMolecule(name=choice["name"], atoms=app.atoms, txt=choice["data"]))

    def respond_to_controls(self, **kwargs):
        app = App.get_running_app()
        act = self.ids.act

        if (app.left_control in app.controls) and (app.controls[app.left_control].equals(**kwargs)):
            self.h_move_act(-1)
            return True
        if (app.right_control in app.controls) and (app.controls[app.right_control].equals(**kwargs)):
            self.h_move_act(1)
            return True
        if (app.flip_control in app.controls) and (app.controls[app.flip_control].equals(**kwargs)):
            self.flip_act()
            return True
        if (app.rotate_control in app.controls) and (app.controls[app.rotate_control].equals(**kwargs)):
            self.rotate_act()
            return True
        if (app.drop_control in app.controls) and (app.controls[app.drop_control].equals(**kwargs)):
            act.set_job("drop", {"count": 1})
            app.play_sfx("drop")
            return True

        return False

    def on_reactor_touch_move(self, obj, event:MotionEvent):
        """
        Callback for touch_move MotionEvents forwarded from reactor.
        :param obj: Unused.
        :param event: MotionEvent.
        :return: True of origin inside rector. Otherwise, False.
        """
        act = self.ids.act
        reactor = self.ids.reactor

        if (act.job == "move") and reactor.collide_point(event.ox, event.oy):
            dx = (event.x - act.params["opos"][0]) / (reactor.width / reactor.COLS)
            dy = (event.y - act.params["opos"][1]) / (reactor.height / reactor.ROWS)
            if self.respond_to_controls(type=["touch", "move"],
                                        dx=dx,
                                        dy=dy,
                                        is_double_tap=event.is_double_tap,
                                        is_triple_tap=event.is_triple_tap):
                act.params["opos"] = (event.x, event.y)
                return True

        return False

    def on_reactor_touch_down(self, obj, event:MotionEvent):
        """
        Callback for touch_down MotionEvents forwarded from reactor. Switch act to "move" mode.
        :param obj: Unused.
        :param event: MotionEvent.
        :return: True of origin inside rector. Otherwise, False.
        """
        act = self.ids.act
        reactor = self.ids.reactor

        if act.job == "play" and reactor.collide_point(event.ox, event.oy):
            act.params.update({"opos": event.opos})
            act.set_job("move", act.params)
            return True

        return False

    def on_reactor_touch_up(self, obj, event:MotionEvent):
        """
        Callback for touch_up MotionEvents forwarded from reactor.
        :param obj: Unused.
        :param event: MotionEvent.
        :return: True of origin inside rector. Otherwise, False.
        """
        act = self.ids.act
        reactor = self.ids.reactor

        if reactor.collide_point(event.ox, event.oy):

            if act.job == "move":
                act.set_job("play", {"count": act.params["count"]})

            dx = (event.x - event.ox) / (reactor.width / reactor.COLS)
            dy = (event.y - event.oy) / (reactor.height / reactor.ROWS)
            if self.respond_to_controls(type=["touch", "up"],
                                        dx=dx,
                                        dy=dy,
                                        is_double_tap=event.is_double_tap,
                                        is_triple_tap=event.is_triple_tap):
                return True

        return False

    def on_key_escape(self):
        app = App.get_running_app()
        app.root.current = 'menu_screen'
        return True

    def on_key_down(self, obj, keycode, scancode, text, modifiers):
        """
        Key press event callback.
        :param obj: Object.
        :param keycode: Keycode.
        :param scancode: Unused.
        :param text: Unused.
        :param modifiers: Unused.
        :return: Always return True to prevent App.stop() on <ESC>.
        """

        act = self.ids.act
        key = Keyboard.keycode_to_string(obj, keycode)

        # Config-independent keys:
        if key == self.PAUSE_KEY:
            self.start_stop_timer()
        elif key == self.MENU_KEY:
            self.on_key_escape()

        # Forward gaming keys
        elif act.job == "play":
            self.respond_to_controls(type=["key", "down"], keycode=key)

        return True

    def on_joy_axis(self, win, joy_id, axis_id, value):
        """
        Callback for value change of joystick axis devices. This callback only sets the dx value. Needs to be repeatedly
        handled in on_time.
        :param win: Unused.
        :param joy_id: ID of joystick or gamepad.
        :param axis_id: ID joystick or gamepad axis.
        :param value: 16 bit int value.
        """
        rel_val = value / 0x8000    # 16 bit int to float
        axis = dict_get_or_create(self._joystick_axes, joy_id, axis_id)
        if abs(rel_val) >= self.JOYSTICK_AXIS_THRESHOLD:
            axis.update({"dx": rel_val})
        else:
            axis.update({"dx": 0.0, "value": 0.0})

    def on_joy_hat(self, win, joy_id, hat_id, value):
        act = self.ids.act
        if act.job == "play":
            self.respond_to_controls(type=["joy", "hat"], joy_id=joy_id, hat_id=hat_id, dx=value[0], dy=value[1])

    def on_joy_button_down(self, win, joy_id, button_id):
        if button_id == self.JOYSTICK_ESCAPE_BUTTON:
            return self.on_key_escape()

        act = self.ids.act
        if act.job == "play":
            self.respond_to_controls(type=["joy", "button", "down"], joy_id=joy_id, button_id=button_id)

    def on_time(self, *args):
        """
        Timer event callback. This callback is regularly called every 0.025 s if this screen is active.
        :param args: Unused.
        """

        # Not ready
        if ("act" not in self.ids) or ("reactor" not in self.ids) or ("tube" not in self.ids):
            return

        act: CMoleculeWidget = self.ids.act
        reactor: CReactor = self.ids.reactor
        bonus: CMoleculeWidget = self.ids.bonus
        tube: RelativeLayout = self.ids.tube

        self._time += 1

        # Handle joystick axis devices
        for joy_id, joystick in self._joystick_axes.items():
            for axis_id, axis in joystick.items():
                if ("dx" in axis) and (abs(axis["dx"]) >= self.JOYSTICK_AXIS_THRESHOLD):
                    value = axis["value"] if "value" in axis else 0.0
                    value *= 0.707
                    value += axis["dx"]
                    if abs(value) >= 1.0:
                        self.respond_to_controls(type=["joy", "axis"], joy_id=joy_id, axis_id=axis_id, dx=value)
                        value -= value / abs(value)
                    axis.update({"value": value})

        # Rotate free bonds every n cycles
        if self._time % 40 == 0:
            act.delocalize_free_bonds()
            reactor.delocalize_free_bonds()

        # Fade out hovers
        hovers = [child for child in tube.children if type(child) is CHover]
        for hover in hovers:
            if hover.opacity > 0.01:
                hover.opacity -= 0.03125
            else:
                tube.remove_widget(hover)

        # Empty molecule: Cleanup reactor
        # Try to drop all floating molecule widgets. Otherwise, spawn a new molecule and check if to create a new bonus
        # molecule.
        if not act.molecule:
            if not self.drop_molecule_widgets():
                if not bonus.molecule:
                    self.create_bonus()
                if not self.spawn_act():
                    self.game_over()

        elif act.job == "destroy":
            self.destroy_act()

        elif act.job in ["play", "move"]:
            act.params["count"] += 1

            # Level-dependent number of cycles before drop to the next line
            # Starting with 10 cycles for level 1 (0..9 nr_molecules) til 1 cycle, 20% less for each level compared to the
            # previous one.
            if act.params["count"] >= 1.0 + 19.0 * (0.8 ** (self.nr_molecules // 10)):
                act.params["count"] = 0
                self.drop_act()

        elif act.job == "drop":
            self.drop_act()

    def switch_to_scores_screen(self, *args):
        self.manager.current = "scores_screen"

    def on_enter(self, *args):
        super().on_enter(*args)
        self.start_timer()

        # Also add continue button to main menu
        screen_manager: ScreenManager = App.get_running_app().root
        menu_screen = screen_manager.get_screen('menu_screen')
        menu_screen.add_continue_button()

    def on_leave(self, *args):
        self.stop_timer()
        super().on_leave(*args)