from kivy.graphics import Color, Line, InstructionGroup
from kivy.uix.relativelayout import RelativeLayout

from cmolecule import CMolecule
from cmoleculewidget import CMoleculeWidget


class CReactor(RelativeLayout):
    """
    CReactor is a layout widget which hosts all molecule widgets except act. It provides methods for the interaction
    with its child molecule widgets.
    """
    COLS = 8
    ROWS = 16

    grid = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update, size=self.update)

    def draw_canvas(self):
        if self.grid is not None: self.grid.clear()
        self.grid = InstructionGroup()
        self.grid.add(Color(1, 1, 1, 0.05))
        for c in range(1, self.COLS):
            self.grid.add(Line(points=[c * self.width / self.COLS, 0.1 * self.height / self.ROWS,
                                       c * self.width / self.COLS, (self.ROWS - 0.1) * self.height / self.ROWS], width=1))
        for r in range(1, self.ROWS):
            self.grid.add(Line(points=[0.1 * self.width / self.COLS, r * self.height / self.ROWS,
                                       (self.COLS - 0.1) * self.width / self.COLS, r * self.height / self.ROWS], width=1))
        self.canvas.before.add(self.grid)

    def update(self, *args):
        self.draw_canvas()
        for child in self.children:
            if type(child) is CMoleculeWidget:
                child.pos = self.x + self.width * child.col / self.COLS, self.y + child.row * self.height / self.ROWS
                child.size = (self.width * child.cols / self.COLS, self.height * child.rows / self.ROWS)

    def fits(self, molecule:CMolecule, col, row):
        """
        Tests if molecule fits into this CRector object (without collision detection).
        :param molecule: CMolecule to test.
        :param col: X position of molecule in blocks.
        :param row: Y position of molecule in blocks.
        :return: True, if molecule fits, otherwise False.
        """
        return (col >= 0) and (row >= 0) and (col + molecule.dim[0] <= self.COLS) and (row + molecule.dim[1] <= self.ROWS)

    def test_collision(self, molecule:CMolecule, col, row):
        """
        Tests if any child CMoleculeWidget collides with the atoms of the provided molecule.
        :param molecule: CMolecule to test.
        :param col: X position of molecule in blocks.
        :param row: XYposition of molecule in blocks.
        :return: True if collision, otherwise False.
        """
        for child in self.children:
            if type(child) is CMoleculeWidget:
                rel_pos = (child.col - col, child.row - row)
                if molecule.collides_with(child.molecule, rel_pos):
                    return True

        return False

    def list_colliders(self, molecule:CMolecule, col, row):
        """
        List all child widgets which collide with atoms from the provided molecule.
        :param molecule: CMolecule to test.
        :param col: X position of molecule in blocks.
        :param row: XYposition of molecule in blocks.
        :return: List of all colliding child widgets.
        """
        colliders = []
        for child in self.children:
            if type(child) is CMoleculeWidget:
                rel_pos = (child.col - col, child.row - row)
                if molecule.collides_with(child.molecule, rel_pos):
                    colliders.append(child)

        return colliders

    def list_molecule_widgets_if_floating(self, molecule_widget: CMoleculeWidget):
        """
        Lists all molecule widgets connected to the provided molecule widget if not directly or indirectly connected to
        the ground.
        :param molecule_widget: CMoleculeWidget.
        :return: List of CMoleculeWidgets.
        """

        def __list_molecule_widgets_if_floating_recursive__(molecule_widget: CMoleculeWidget, others:list, group:list):
            # Already on ground?
            if molecule_widget.row == 0:
                return None

            # Add molecule widget to group
            group.append(molecule_widget)

            # Remove molecule widget from others (otherwise it would collide with itself)
            if molecule_widget in others:
                others.remove(molecule_widget)

            # Get colliding molecule widgets if moved 1 step down
            colliders = molecule_widget.list_colliders(others, row=molecule_widget.row - 1)

            # And the same procedure for all molecule widgets in contact with molecule_widget
            # TODO Needs to be validated, further use of n_widgets
            for c in colliders:
                n_widgets = __list_molecule_widgets_if_floating_recursive__(c, others, group)
                if n_widgets is None:
                    return None

            return group

        others = self.children.copy()
        group = []
        result = __list_molecule_widgets_if_floating_recursive__(molecule_widget, others, group)
        return group if result else []

    def delocalize_free_bonds(self):
        """
        Moves all free bonds for the respective atom for all atoms. This simulates electron delocalization.
        """
        for child in self.children:
            if type(child) is CMoleculeWidget:
                child.delocalize_free_bonds()