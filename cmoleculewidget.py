from kivy.app import App
from kivy.core.text import Label
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate, Translate, Scale
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.widget import Widget

from cmolecule import CMolecule
from catom import CAtom


class CMoleculeWidget(Widget):
    BOND = 0.1
    GAP = 0.05

    col = NumericProperty(0)
    row = NumericProperty(0)
    cols = NumericProperty(0)
    rows = NumericProperty(0)
    value = NumericProperty(0)
    name = StringProperty("")

    def __init__(self,
                 name: str = "",
                 value: int = 0,
                 col: int = 0,
                 row: int = 0,
                 dim: tuple[int, int] = (0, 0),
                 rgba: tuple[float, float, float, float] = (0, 0, 0, 0),
                 job: str = "",
                 params = None,
                 atoms: dict[str, None | CAtom] = None,
                 txt: list[str] | None = None,
                 **kwargs):

        super().__init__(**kwargs)
        self.name = name
        self.molecule = CMolecule(name, dim, atoms, txt)
        self.col = col
        self.row = row
        self.cols, self.rows = dim
        self.rgba = rgba
        self.value = value
        self.job = job
        self.params = params
        self._canvas_translate = None
        self._canvas_scale = None
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def draw_canvas(self):
        """
        Draws atoms and bonds to the widget canvas.
        """

        app = App.get_running_app()
        step = self.BOND + self.GAP
        bond_image = app.bond_image
        free_image = app.free_image
        self.canvas.clear()
        if (self.rows != 0) and (self.cols != 0):
            w, h = self.size
            pass

            with self.canvas:
                PushMatrix()
                # Step 1: Set origin and scale factor to scale up from 1 unit per atom
                self._canvas_translate = Translate(x=self.x, y=self.y)
                self._canvas_scale = Scale(x=w / self.cols, y=h / self.rows)
                # TODO set clipping

                # Steps 2 - 4: Draw the molecule as 1 unit per atom scale
                # Step 2: Draw background
                Color(self.rgba[0], self.rgba[1], self.rgba[2],
                      1.0 if (self.job == "destroy") and ("count" in self.params) and (self.params["count"] & 2 == 0) else self.rgba[3])
                for row in range(self.rows):
                    for col in range(self.cols):
                        atom = self.molecule.get_atom((col, row))
                        if atom is not None:
                            Rectangle(pos=(col, row), size=(1, 1))

                # Step 3: Draw bonds (bound and free)
                b_size = (self.BOND, 1)
                f_size = (self.BOND, self.BOND)
                Color(1, 1 , 1, 1)
                for row in range(self.rows):
                    yb = row - 0.5
                    yf = row - 0.01
                    for col in range(self.cols):
                        atom: CAtom = self.molecule.get_atom((col, row))
                        if atom is not None:
                            # Bound: Direction 0 and 1 only
                            for direction in range(2):
                                nr_bonds = atom.bonds["bound"][direction]
                                x = col + 0.5 * (1 - self.BOND - (nr_bonds - 1) * step)
                                for i in range(nr_bonds):
                                    if direction != 0:
                                        PushMatrix()
                                        Rotate(angle=90, origin=(col + 0.5, yb + 1))
                                        Rectangle(texture=bond_image.texture, pos=(x + i * step, yb), size=b_size)
                                        PopMatrix()
                                    else:
                                        Rectangle(texture=bond_image.texture, pos=(x + i * step, yb), size=b_size)

                            # Free:
                            for direction in range(4):
                                nr_bonds = atom.bonds["free"][direction]
                                x = col + 0.5 * (1 - self.BOND - (nr_bonds - 1) * step)
                                for i in range(nr_bonds):
                                    if direction != 0:
                                        PushMatrix()
                                        Rotate(angle=direction * 90, origin=(col + 0.5, yb + 1))
                                        Rectangle(texture=free_image.texture, pos=(x + i * step, yf), size=f_size)
                                        PopMatrix()
                                    else:
                                        Rectangle(texture=free_image.texture, pos=(x + i * step, yf), size=f_size)

                # Step 4: Draw atoms
                for row in range(self.rows):
                    for col in range(self.cols):
                        atom = self.molecule.get_atom((col, row))
                        if (atom is not None) and (atom.image is not None):
                            Color(1, 1, 1, 1)
                            Rectangle(texture=atom.image.texture, pos=(col + 0.15, row + 0.15), size=(0.7, 0.7))
                            nr_free = sum(atom.bonds["free"])
                            if nr_free:
                                label = Label(text=str(nr_free), font_size=20)
                                label.refresh()
                                if (atom.symbol == "H") or (atom.symbol == "N"):
                                    Color (0, 0, 0, 1)
                                else:
                                    Color(1, 1, 1, 1)
                                Rectangle(texture=app.number_textures[nr_free],
                                          pos=(col + 0.3, row + 0.325),
                                          size=(0.35, 0.35))
                PopMatrix()

    def update_canvas(self, *args):
        """
        Updates the canvas without change of its content (except position and scale).
        :param args: Unused.
        """
        if App.get_running_app():
            if (self._canvas_translate is not None) and (self._canvas_scale is not None):
                self._canvas_translate.xy = self.pos
                cols, rows = self.molecule.dim
                if (cols != 0) and (rows != 0):
                    w, h = self.size
                    self._canvas_scale.x = w / cols
                    self._canvas_scale.y = h / rows
            else:
                self.draw_canvas()

    def move_to(self, col, row):
        """
        Moves the molecule and thus the widget.
        :param col: Col.
        :param row: Row.
        """
        self.col = col
        self.row = row

    def set_molecule(self, molecule = None):
        """
        Sets the object molecule and dimension and redraws the widget.
        :param molecule: CMolecule
        """
        self.molecule = molecule
        self.cols, self.rows = molecule.dim
        self.draw_canvas()

    def set_job(self, job, params = None):
        self.job = job
        if params is not None:
            self.params = params
        self.draw_canvas()

    def delocalize_free_bonds(self):
        """
        Moves all free bonds for the respective atom for all atoms. This simulates electron delocalization.
        """
        self.molecule.delocalize_free_bonds()
        self.draw_canvas()

    def collides_with_others(self, others: list, col: int | None = None, row: int | None = None):
        """
        Tests if this molecule widget collides with the atoms of other CMoleculeWidgets from a list.
        :param others: List of other CMoleculeWidgets.
        :param col: Optional, alternative col for this molecule.
        :param row: Optional, alternative row for this molecule.
        :return: True if collision, otherwise False.
        """
        col = col if col is not None else self.col
        row = row if row is not None else self.row
        for o in others:
            if type(o) is type(self):
                rel_pos = (o.col - col, o.row - row)
                if self.molecule.collides_with(o.molecule, rel_pos):
                    pass
                    return True

        return False

    def list_colliders(self, others: list, col: int | None = None, row: int | None = None):
        """
        List other molecule widgets from a list which collides with atoms from this CMoleculeWidget.
        :param others: List of other CMoleculeWidgets.
        :param col: Optional, alternative col for this molecule.
        :param row: Optional, alternative row for this molecule.
        :return: List of all colliding other molecule widgets.
        """
        col = col if col is not None else self.col
        row = row if row is not None else self.row
        colliders = []
        for o in others:
            if type(o) is type(self):
                rel_pos = (o.col - col, o.row - row)
                if self.molecule.collides_with(o.molecule, rel_pos):
                    colliders.append(o)

        return colliders


