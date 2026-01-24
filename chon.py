#import kivy
from os import makedirs
from os.path import join, dirname, isfile
from json import load as load_json, dumps
from kivy.app import App
from kivy.core.audio import SoundLoader
from kivy.core.image import Image as CoreImage
from kivy.core.text import LabelBase, Label
from kivy.graphics.texture import Texture
from kivy.properties import NumericProperty, StringProperty

from ccontrol import CControl

# Ugly hack to init SoundLoader before UI
temp = SoundLoader.load("None.mp3")

from catom import  CAtom
from cmenuscreen import CMenuScreen
from csettingsscreen import CSettingsScreen
from cgamescreen import CGameScreen
from cscoresscreen import CScoresScreen
from crulesscreen import  CRulesScreen
from creactor import CReactor
from cbutton import CButton
from ctext import CText
from cspinner import CSpinner

__version__ = "0.1"

DEBUG_CONFIG_FILENAME: str | None = None
"""
Json filename for config file used for testing and debugging. If not None, the linked file may contain:
nr_molecules: number of molecules at start (to set the level number),
bonus_names: list of names of bonus molecules as in inc/bonus.json,
fragment_names: list of names of fragments as in inc/fragments.json. 
Only these data (and in the provided order) are used for testing.
"""

def load_playlists(filename, inc_path=""):
    """
    Loads the playlists from a json file with the structure:
    {
      "playlist_1": ["sound_filename_1", "sound_filename_1", ...],
      "playlist_2": ...,
      ...
    }
    :param filename: (Path and) Filename of the json file.
    :param inc_path: Path to the sound files.
    :return: Dict of the same structure with Sound objects instead of sound_filenames.
    """
    playlists = {}
    with open(filename, "r", encoding="utf8") as read_file:
        # Load json
        files = load_json(read_file)

        # Load sound files for each json file key
        for key, f_list in files.items():
            s_list = []
            for filename in f_list:
                sound = SoundLoader.load(join(inc_path, filename))
                s_list.append(sound)

            playlists.update({key: s_list})

    return playlists


class CHONApp(App):
    # Paths
    APP_PATH = dirname(__file__)
    DATA_PATH = join(APP_PATH, "data")
    INC_PATH = join(APP_PATH, "inc")
    DOC_PATH = join(APP_PATH, "doc")
    MISC_PATH = join(APP_PATH, "misc")

    # Input devices
    MAX_JOYSTICKS = 1
    MAX_JOYSTICK_AXES = 8
    MAX_JOYSTICK_HATS = 4
    MAX_JOYSTICK_BUTTONS = 16

    # Global game object data and images
    themes = []
    atoms = {}
    atom_images = {}
    fragments = {}
    bonus_molecules = {}
    fragments = []
    bonus_molecules = []
    bond_image = None
    free_image = None
    number_textures = []
    alpha_gradient = None

    # Sound effects
    sfx = {}
    sfx_volume = NumericProperty(1.0)

    # Background music
    music = None
    music_playlists = load_playlists(join(DATA_PATH, "music.json"), INC_PATH)
    music_playlist_name = StringProperty(next(iter(music_playlists)))
    music_volume = NumericProperty(0.5)

    # Controls
    # Initial values vor the controls in the game. Will be overwritten upon loading config.
    left_control = StringProperty("Key: left")
    right_control = StringProperty("Key: right")
    flip_control = StringProperty("Key: up")
    rotate_control = StringProperty("Key: down")
    drop_control = StringProperty("Key: spacebar")

    # Other config data
    controls = None

    # Tests
    test_bonus_names = []
    test_fragment_names = []
    test_nr_molecules = 0

    def load_themes(self):
        """
        Loads uix theme data from <DATA_PATH>/themes.json.
        """
        self.themes.clear()
        with open(join(self.DATA_PATH, "themes.json"), "r", encoding="utf8") as read_file:
            themes_data = load_json(read_file)
            for t in themes_data:
                self.themes.append(t)

    def load_atoms(self):
        """
        Loads atom data from <DATA_PATH>/atoms.json.
        """
        self.atoms.clear()
        with open(join(self.DATA_PATH, "atoms.json"), "r", encoding="utf8") as read_file:
            atoms_data = load_json(read_file)
            for a in atoms_data:
                atom = CAtom.from_dict(a)
                self.atoms.update({a["symbol"]: atom})

    def load_fragments(self):
        """
        Loads molecule fragment data from <DATA_PATH>/fragments.json.
        """
        self.fragments.clear()
        with open(join(self.DATA_PATH, "fragments.json"), "r", encoding="utf8") as read_file:
            fragments_data = load_json(read_file)
            for f in fragments_data:
                self.fragments.append(f)

    def load_bonus_molecules(self):
        """
        Loads bonus molecule data from <DATA_PATH>/bonus.json.
        """
        self.bonus_molecules.clear()
        with open(join(self.DATA_PATH, "bonus.json"), "r", encoding="utf8") as read_file:
            bonus_data = load_json(read_file)
            for f in bonus_data:
                self.bonus_molecules.append(f)

    def load_images(self):
        """
        Loads images for atoms (C, H, O, N), bonds and free electrons from <INC_PATH>.
        """
        for atom in self.atoms:
            # Set default atom image directly to atoms
            self.atoms[atom].image = CoreImage(join(self.INC_PATH, atom.lower() + self.themes[0]["atom_suffix"]))

            # Store all atom images
            for theme in self.themes:
                filename = atom.lower() + theme["atom_suffix"]
                if filename not in self.atom_images:
                    self.atom_images.update({filename: CoreImage(join(self.INC_PATH, filename))})

        self.bond_image = CoreImage(join(self.INC_PATH, "bond.png"))
        self.free_image = CoreImage(join(self.INC_PATH, "free.png"))

    def load_sfx(self):
        """
        Reads <DATA_PATH>/sfx.json and loads the respective sound effects from <INC_PATH>.
        """
        self.sfx.clear()
        with open(join(self.DATA_PATH, "sfx.json"), "r", encoding="utf8") as read_file:
            sfx_data = load_json(read_file)
            for key in sfx_data:
                sound = SoundLoader.load(join(self.INC_PATH, sfx_data[key]))
                self.sfx.update({key: sound})

    def load_user_config(self):
        """
        Loads the user config file and applies config data.
        """
        # Create user data dir, if not exists
        makedirs(self.user_data_dir, exist_ok=True)

        # Check if config file exists, otherwise use stub
        config_filename = join(self.user_data_dir, "config.json")
        config_stub_filename = join(self.DATA_PATH, "config.json")
        source = config_filename if isfile(config_filename) else config_stub_filename

        # Read data
        with open(source, "r", encoding="utf8") as read_file:
            config = load_json(read_file)
            if "controls" in config:
                if "left" in config["controls"]: self.left_control = config["controls"]["left"]
                if "right" in config["controls"]: self.right_control = config["controls"]["right"]
                if "flip" in config["controls"]: self.flip_control = config["controls"]["flip"]
                if "rotate" in config["controls"]: self.rotate_control = config["controls"]["rotate"]
                if "drop" in config["controls"]: self.drop_control = config["controls"]["drop"]

            if "audio" in config:
                if "sfx" in config["audio"]:
                    if "volume" in config["audio"]["sfx"]: self.sfx_volume = config["audio"]["sfx"]["volume"]
                if "music" in config["audio"]:
                    if "volume" in config["audio"]["music"]: self.music_volume = config["audio"]["music"]["volume"]
                    if "playlist" in config["audio"]["music"]: self.music_playlist_name = config["audio"]["music"]["playlist"]

    def save_user_config(self):
        """
        Saves the user config data to <user_data_dir>/config.json.
        :return:
        """
        config_data = {
                        "controls":
                            {
                                "left": self.left_control,
                                "right": self.right_control,
                                "flip": self.flip_control,
                                "rotate": self.rotate_control,
                                "drop": self.drop_control
                            },

                        "audio":
                            {
                                "sfx": {"volume":  self.sfx_volume},
                                "music":
                                    {
                                        "volume": self.music_volume,
                                        "playlist": self.music_playlist_name
                                    }
                            }
                        }
        with open(join(self.user_data_dir, "config.json"), "w", encoding="utf8") as write_file:
            write_file.write(dumps(config_data))

    def create_controls(self):

        # Load touch controls and add double and triple tap
        self.controls = {}
        with open(join(self.DATA_PATH, "touch_controls.json"), "r", encoding="utf8") as read_file:
            touch_data = load_json(read_file)
            for key, value in touch_data.items():
                params1 = value.copy()
                params1.update({"is_double_tap": False, "is_triple_tap": False})
                self.controls.update({key: CControl(**params1)})
                params2 = value.copy()
                params2.update({"is_double_tap": True})
                self.controls.update({"2"+key: CControl(**params2)})
                params3 = value.copy()
                params3.update({"is_triple_tap": True})
                self.controls.update({"3"+key: CControl(**params3)})

        # Create joystick controls (for support of up to 8 axes, 4 hats and 16 buttons)
        # Only 1 joystick id (0) supported, yet!
        for axis in range(self.MAX_JOYSTICK_AXES):
            key1 = "Axis " + str(axis) + ": +"
            params1 = {"type": ["joy", "axis"], "joy_id": 0, "axis_id": axis, "min_dist": 0.1,
                       "min_angle": 0, "max_angle": 0}
            self.controls.update({key1: CControl(**params1)})
            key2 = "Axis " + str(axis) + ": -"
            params2 = {"type": ["joy", "axis"], "joy_id": 0, "axis_id": axis, "min_dist": 0.1,
                       "min_angle": -180, "max_angle": -180}
            self.controls.update({key2: CControl(**params2)})
        for hat in range(self.MAX_JOYSTICK_HATS):
            key1 = "Hat " + str(hat) + ": left"
            params1 = {"type": ["joy", "hat"], "joy_id": 0, "hat_id": hat, "dx": -1}
            self.controls.update({key1: CControl(**params1)})
            key2 = "Hat " + str(hat) + ": right"
            params2 = {"type": ["joy", "hat"], "joy_id": 0, "hat_id": hat, "dx": 1}
            self.controls.update({key2: CControl(**params2)})
            key3 = "Hat " + str(hat) + ": up"
            params3 = {"type": ["joy", "hat"], "joy_id": 0, "hat_id": hat, "dy": 1}
            self.controls.update({key3: CControl(**params3)})
            key4 = "Hat " + str(hat) + ": down"
            params4 = {"type": ["joy", "hat"], "joy_id": 0, "hat_id": hat, "dy": -1}
            self.controls.update({key4: CControl(**params4)})
        for button in range(self.MAX_JOYSTICK_BUTTONS):
            key = "Button: " + str(button)
            params = {"type": ["joy", "button", "down"], "joy_id": 0, "button_id": button}
            self.controls.update({key: CControl(**params)})

        # Create keyboard controls: After init!!!
        pass

    def create_number_textures(self):
        """
        Creates textures containing numbers from 0 to 4. These textures are used for visualization of the number of
        free electrons.
        """
        self.number_textures = []
        for i in range(5):
            label = Label(text=str(i), font_size=20)
            label.refresh()
            self.number_textures.append(label.texture)

    def create_alpha_gradient(self):
        """
        Creates an alpha gradient texture. This texture is used to fade out background images.
        """
        self.alpha_gradient = Texture.create(size=(1,512), colorfmt='rgba')
        size = 2 * 256 * 4
        buf = [min(int(2 * x * 255 / size), 255) for x in range(size)]
        buf = bytes(buf)
        self.alpha_gradient.blit_buffer(buf, pos=(0, 0), size=(1, 512), colorfmt='rgba', bufferfmt='ubyte')

    def get_alpha_gradient(self):
        """
        Failsafe method to get the alpha gradient texture. Creates a new texture, if not created yet.
        :return: alpha gradient texture.
        """
        if self.alpha_gradient is None:
            self.create_alpha_gradient()
        return self.alpha_gradient

    def play_sfx(self, key):
        """
        Plays a sound effect.
        :param key: Sound effect name.
        """
        if (self.sfx_volume != 0) and (key in self.sfx) and self.sfx[key]:
            self.sfx[key].play()

    def stop_sfx(self, key):
        """
        Stops a sound effect.
        :param key: Sound effect name.
        """
        if (key in self.sfx) and self.sfx[key]:
            self.sfx[key].stop()

    def apply_sfx_volume(self, *args):
        """
        Applies sfx_volume to all sound effects. Stops playing sound effects, if sfx_volume is 0.
        :param args: Unused.
        """
        for key in self.sfx:
            if self.sfx[key]:
                self.sfx[key].volume = self.sfx_volume

                if self.sfx_volume == 0:
                    self.stop_sfx(key)

    def play_music(self):
        """
        Starts playing music.
        """
        if self.music and (self.music_volume != 0):
            self.music.play()
            self.music.bind(on_stop=self.on_music_stops)

    def stop_music(self):
        """
        Stops playing music.
        """
        if self.music:
            self.music.unbind(on_stop=self.on_music_stops)
            self.music.stop()

    def next_music(self, *args):
        """
        Starts playing music or continues with the next entry of the playlist.
        :param args: Unused.
        """

        # Stop music first
        if self.music and (self.music.state == "play"):
            self.stop_music()

        # Check if playlist exists and not empty
        if self.music_playlist_name in self.music_playlists:
            playlist = self.music_playlists[self.music_playlist_name]
            if playlist:
                # Rotate playlist
                sound = playlist.pop(0)
                playlist.append(sound)

                # Play
                self.music = sound
                self.music.volume = self.music_volume
                self.play_music()

    def apply_music_volume(self, *args):
        """
        Applies music_volume to the presently playing background music. Stops playing music if music_volume is 0. Re-
        starts playing stopped music if music_volume is set to a value different from 0.
        :param args: Unused.
        """
        if self.music:
            if not self.music.volume:
                self.music.volume = self.music_volume
                if self.music.state == "stop":
                    self.play_music()
            elif not self.music_volume:
                self.music.volume = self.music_volume
                if self.music.state == "play":
                    self.stop_music()
            else:
                self.music.volume = self.music_volume

    def on_music_stops(self, *args):
        """
        Callback for stopping music at the end of a track.
        :param args: Unused.
        """
        if self.music_volume:
            self.next_music()

    def load_debug_config_data(self):
        """
        Loads test data for testing and debugging purposes.
        """
        if DEBUG_CONFIG_FILENAME:
            try:
                with open(DEBUG_CONFIG_FILENAME, "r", encoding="utf8") as read_file:
                    debug_data = load_json(read_file)
                    self.test_nr_molecules = debug_data["nr_molecules"] if "nr_molecules" in debug_data else 0
                    self.test_bonus_names = debug_data["bonus_names"] if "bonus_names" in debug_data else []
                    self.test_fragment_names = debug_data["fragment_names"] if "fragment_names" in debug_data else []
            except FileNotFoundError:
                pass

    def build(self):
        self.icon = join(self.MISC_PATH, "icon.ico")
        LabelBase.register(name='OpenArrow', fn_regular=join(self.INC_PATH, 'OpenArrow-Regular.ttf'))
        LabelBase.register(name='Segment14', fn_regular=join(self.INC_PATH, 'segment14.regular.otf'))
        self.load_themes()
        self.load_atoms()
        self.load_fragments()
        self.load_bonus_molecules()
        self.load_images()
        self.load_sfx()
        self.load_user_config()
        self.create_controls()
        self.next_music()
        self.create_number_textures()
        self.create_alpha_gradient()
        self.load_debug_config_data()
        self.bind(sfx_volume=self.apply_sfx_volume)
        self.bind(music_volume=self.apply_music_volume)
        self.bind(music_playlist_name=self.next_music)
        return super().build()

    def on_start(self):
        """
        Callback for starting the application. Calls CMenuScreen.after_init().
        """
        menu_screen = self.root.screens[0]
        menu_screen.after_init()


if __name__ == '__main__':
    CHONApp().run()