from catom import CAtom
from ctools import char_to_bond


class CMolecule:
    def __init__(self, name: str = "", dim: tuple[int, int] = (0, 0), atoms: dict[str, None | CAtom] | None = None,
                 txt: list[str] | None = None):
        self.name: str = name
        self.dim: tuple[int, int] = dim
        if txt and atoms:
            self.data: list = []
            self.parse(atoms, txt)
        else:
            self.data: list[list[None | CAtom]] = [[None for __ in range(dim[0])] for _ in range(dim[1])]

    def parse(self, atoms: dict[str, None | CAtom], txt: list[str]):
        """
        Creates molecule data from a formatted text. The formatted text represents a 2D array with single char symbol letters for the atoms and single char numbers for the number of bonds between the atom symbols.
        :param atoms: Dict containing the atoms.
        :param txt: Formatted text.
        """

        # Step 1: Remove empty lines
        txt1 = [line for line in txt if not line.isspace()]

        # Step 2: Remove spaces left and right
        left = min([(len(line) - len(line.lstrip())) for line in txt1])
        txt2 = [line[left:] for line in txt1]
        right = max([len(line.rstrip()) for line in txt2])
        txt3 = [line[:right] for line in txt2]

        # Step 2: Check dimensions and resize if needed
        rows = (len(txt3) + 1) // 2
        cols = (right + 1) // 2
        if (cols, rows) != self.dim:
            self.dim = (cols, rows)
            self.data = [[None for __ in range(cols)] for _ in range(rows)]

        # Step 3: Map all atoms
        for row in range(rows):
            line = txt3[2 * row]
            for col in range(cols):
                symbol = line[2 * col]
                if symbol in atoms:
                    atom = atoms[symbol]
                    self.set_atom((col, row), atom.copy())
                elif symbol != ' ':
                    raise ValueError("Invalid atom symbol '" + symbol + "' in " + self.name + " at position (" + str(col) + ", " + str(row) + ")")

        # Step 4: Build connections vertically
        for row in range(rows - 1):
            line = txt3[2 * row + 1]
            for col in range(cols):
                char = line[2 * col]
                nr = char_to_bond(char)
                if nr:
                    self.connect_atoms((col, row), (col, row + 1), nr=nr)

        # Step 5: Build connections horizontally
        for row in range(rows):
            line = txt3[2 * row]
            for col in range(cols - 1):
                char = line[2 * col + 1]
                nr = char_to_bond(char)
                if nr:
                    self.connect_atoms((col, row), (col + 1, row), nr=nr)

    def get_atom(self, position):
        """
        Gets the atom for a provided position.
        :param position: Position tuple (x, y).
        :return: CAtom
        """
        x, y = position
        return self.data[y][x]

    def set_atom(self, position, atom):
        """
        Sets an atom at a provided position. Does not connect or disconnect!
        :param position: Position tuple (x, y).
        :param atom: CAtom.
        """
        x, y = position
        self.data[y][x] = atom

    def disconnect_atoms(self, pos1, pos2):
        """
        Changes the connection between two CAtoms from "bound" to "free"
        :param pos1: Position of the first atom (x, y).
        :param pos2: Position of the second atom (x, y).
        """

        # Step 1: Validate pos
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        if abs(dx) + abs(dy) != 1:
            raise ValueError("Invalid parameters for pos1, pos2: pos1 and pos2 must be next to each other")

        # Step 2: Validate both positions contain atoms
        atom1 = self.get_atom(pos1)
        atom2 = self.get_atom(pos2)
        if type(atom1) != CAtom:
            raise ValueError("Invalid value for pos1: pos1 must contain a CAtom")
        if type(atom2) != CAtom:
            raise ValueError("Invalid value for pos2: pos2 must contain a CAtom")

        # Step 3: Validate existing connection
        dir1 = CAtom.direction((dx, dy))
        dir2 = CAtom.opposite_direction(dir1)
        nr_bound1 = atom1.bonds["bound"][dir1]
        nr_bound2 = atom2.bonds["bound"][dir2]
        if nr_bound1 != nr_bound2:
            raise ValueError("Incorrect data in CMolecule.data")

        # Step 4: Remove bound
        atom1.bonds["bound"][dir1] = 0
        atom2.bonds["bound"][dir2] = 0

        # Step 5: Add free
        atom1.bonds["free"][dir1] += nr_bound1
        atom2.bonds["free"][dir2] += nr_bound2


    def is_connected(self, pos1, pos2):
        """
        Tests if two neighbor atoms of this molecule are connected
        :param pos1: Position of the first atom (x, y).
        :param pos2: Position of the second atom (x, y).
        :return: True if two atoms are connected, otherwise false
        :raises ValueError: Raised if pos1 and pos2 not next to each other. Or if not both, pos1 or pos2 contain atoms.
        """

        # Step 1: Validate pos
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        if abs(dx) + abs(dy) != 1:
            raise ValueError("Invalid parameters for pos1, pos2: pos1 and pos2 must be next to each other")

        # Step 2: Validate both positions contain atoms
        atom1 = self.get_atom(pos1)
        atom2 = self.get_atom(pos2)
        if type(atom1) != CAtom:
            raise ValueError("Invalid value for pos1: pos1 must contain a CAtom")
        if type(atom2) != CAtom:
            raise ValueError("Invalid value for pos2: pos2 must contain a CAtom")

        # Step 3: Validate existing connection
        dir1 = CAtom.direction((dx, dy))
        dir2 = CAtom.opposite_direction(dir1)
        nr_bound1 = atom1.bonds["bound"][dir1]
        nr_bound2 = atom2.bonds["bound"][dir2]
        if nr_bound1 != nr_bound2:
            raise ValueError("Incorrect data in CMolecule.data")

        # Step 4: Return connection
        return nr_bound1 != 0

    def connect_atoms(self, pos1, pos2, nr=0, pedantic=True):
        """
        Connects two atoms.
        :param pos1: Position of the first atom (x, y).
        :param pos2: Position of the second atom (x, y).
        :param nr: Number of bonds 0 (use max_nr instead) or 1..3.
        :param pedantic: True, if exactly the requested number of bonds (nr) shall be used. Otherwise, False for the max possible number of bonds, but nor more than nr.
        :return: True, if connection built. Otherwise, False.
        :raises ValueError: Raised if invalid value for nr is provided. Or if pos1 and pos2 not next to each other. Or if not both, pos1 or pos2 contain atoms.
        """

        # Step 1: Validate nr
        if (nr < 1) or (nr > 3):
            raise ValueError("Invalid parameter nr: nr must be in 1..3")

        # Step 2: Validate pos
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        if abs(dx) + abs(dy) != 1:
            raise ValueError("Invalid parameters for pos1, pos2: pos1 and pos2 must be next to each other")

        # Step 3: Validate both positions contain atoms
        atom1 = self.get_atom(pos1)
        atom2 = self.get_atom(pos2)
        if  type(atom1) != CAtom:
            raise ValueError("Invalid value for pos1: pos1 must contain a CAtom")
        if type(atom2) != CAtom:
            raise ValueError("Invalid value for pos2: pos2 must contain a CAtom")

        # Step 4: Clip existing connection first
        self.disconnect_atoms(pos1, pos2)

        # Step 5: Get max number of bonds possible
        free1 = sum(atom1.bonds["free"])
        free2 = sum(atom2.bonds["free"])
        max_nr = min((free1, free2))
        if (max_nr < nr) and pedantic:
            raise ValueError("Invalid value for nr: More bonds requested than available. Maybe use pedantic=False instead.")
        bonds = max_nr if (max_nr < nr) else nr

        # Step 6: Connect
        dir1 = CAtom.direction((dx, dy))
        dir2 = CAtom.opposite_direction(dir1)
        atom1.bonds["bound"][dir1] = bonds
        atom2.bonds["bound"][dir2] = bonds

        # Step 7: Remove free clockwise starting with connection direction
        # First
        directions1 = [(dir1 + i) % 4 for i in range(4)]
        b = bonds
        for d in directions1:
            if b > atom1.bonds["free"][d]:
                b -= atom1.bonds["free"][d]
                atom1.bonds["free"][d] = 0
            else:
                atom1.bonds["free"][d] -= b
                break

        # And Second
        directions2 = [(dir2 + i) % 4 for i in range(4)]
        b = bonds
        for d in directions2:
            if b > atom2.bonds["free"][d]:
                b -= atom2.bonds["free"][d]
                atom2.bonds["free"][d] = 0
            else:
                atom2.bonds["free"][d] -= b
                break

        return bool(bonds)

    def collides_with(self, other, pos):
        """
        Tests if this CMolecule collides with the atoms of another CMolecule.
        :param other: Other CMolecule object.
        :param pos: Relative position of the other CMolecule object.
        :return: True if collision, otherwise False
        """

        # Step 1: Calculate overlap area
        x_overlap = set(range(self.dim[0])) & set(range(pos[0], pos[0] + other.dim[0]))
        y_overlap = set(range(self.dim[1])) & set(range(pos[1], pos[1] + other.dim[1]))

        # Step 2: Stepwise check if atoms in both objects
        for y in y_overlap:
            for x in x_overlap:
                xo = x - pos[0]
                yo = y - pos[1]
                if self.data[y][x] and other.data[yo][xo]:
                    pass
                    return True

        return False

    def touches(self, other, pos):
        """
        Tests if this CMolecule touches (but not collides with) the atoms of another CMolecule.
        :param other: Other CMolecule object.
        :param pos: Relative position of the other CMolecule object.
        :return: True if touched, otherwise False
        """

        # Step 1: Check for collision
        if self.collides_with(other, pos):
            return False

        # Step 2: Touch means collision after moving
        for direction in range(4):
            dx, dy = CAtom.move(direction)
            if self.collides_with(other,(pos[0] + dx, pos[1] + dy)):
                return True

        return False

    def add(self, other, pos, overwrite=False):
        """
        Adds another CMolecule data and resizes this object.
        :param other: Other CMolecule
        :param pos: Relative position of the other CMolecule object.
        :param overwrite: Overwrites data in the case of atom overlap.
        """

        # Step 1: Virtual new pos
        ox, oy = pos
        nx = min(0, ox)
        ny = min(0, oy)

        # Step 2: New dim
        w, h = self.dim
        ow, oh = other.dim
        nw = max(w, ox + ow) - nx
        nh = max(h, oy + oh) - ny

        # Step 3: Create new data array
        n_data = [[None for __ in range(nw)] for _ in range(nh)]

        # Step 4: Move self data
        for y in range(h):
            for x in range(w):
                atom = self.get_atom((x, y))
                n_data[y - ny][x - nx] = atom.copy() if atom else None

        # Step 5: Copy other data
        for y in range(oh):
            for x in range(ow):
                if (not n_data[y + oy - ny][x + ox - nx]) or overwrite:
                    atom = other.data[y][x]
                    n_data[y + oy - ny][x + ox - nx] = atom.copy() if atom else None

        # Step 6: Link data
        self.dim = (nw, nh)
        self.data = n_data

    
    def connect(self, other, pos):
        """
        Connects this CMolecule with another CMolecule. Remains this molecule unchanged if there is no connection possible.
        :param other: Other CMolecule object.
        :param pos: Relative position of the other CMolecule object.
        :return: True, if connection built. Otherwise, False.
        """

        connected = False

        # Step 1: Check if touch
        if not self.touches(other, pos):
            return False

        # Step 2: Merge data
        new_cm = self.copy()
        new_cm.add(other, pos)

        # Step 3: Find possible connection points
        w, h = new_cm.dim
        for y in range(h):
            for x in range(w):
                atom = new_cm.get_atom((x, y))
                if atom:
                    for direction in range(1,3):    # Need only 2 directions to check
                        dx, dy = CAtom.move(direction)
                        nx = x + dx
                        ny = y + dy
                        if (nx >= 0) and (nx < w) and (ny >= 0) and (ny < h):
                            neighbor = new_cm.get_atom((nx, ny))
                            if neighbor:
                                if not new_cm.is_connected((x, y), (nx, ny)):
                                    connected |= new_cm.connect_atoms((x, y), (nx, ny), nr=3, pedantic=False)

        # Step 4: Apply changes if connected
        if connected:
            self.dim = new_cm.dim
            self.data = new_cm.data

        return connected


    def rotate(self, nr=1):
        """
        Clockwise rotation of the molecule.
        :param nr: number of rotations.
        """
        for _ in range(nr):
            # Step 1: Create a new data block with rotated dimensions
            n_data = [[None for ___ in range(self.dim[1])] for __ in range(self.dim[0])]

            # Step 2: Copy data and rotate bonds
            w, h = self.dim
            for y in range(h):
                for x in range(w):

                    # Copy atoms
                    n_data[x][h - y - 1] = self.get_atom((x, y))

                    # Rotate bonds
                    atom: None | CAtom = n_data[x][h - y - 1]
                    if atom:
                        for key in atom.bonds.keys():
                            atom.bonds.update({key: atom.bonds[key][-1:] + atom.bonds[key][:-1]})

            # Step 3: Apply rotated data
            self.data = n_data
            self.dim = (h, w)


    def h_flip(self):
        """
        Flips molecule data (atoms and bonds) horizontally.
        """

        for y in range(len(self.data)):
            # Step 1: Flip line
            self.data[y].reverse()

            # Step 2: Flip bonds
            for x in range(len(self.data[y])):
                atom = self.get_atom((x, y))
                if atom:
                    for bonds in atom.bonds.values():
                        h = bonds[1]
                        bonds[1] = bonds[3]
                        bonds[3] = h

    def v_flip(self):
        """
        Flips molecule data (atoms and bonds) vertically.
        """
        # Step 1: Flip all
        self.data.reverse()

        # Step 2: Flip bonds
        for y in range(len(self.data)):
            for x in range(len(self.data[y])):
                atom = self.get_atom((x, y))
                if atom:
                    for bonds in atom.bonds.values():
                        h = bonds[0]
                        bonds[0] = bonds[2]
                        bonds[2] = h

    def flip(self, orientation="horizontal"):
        """
        Flips the molecule data either horizontally or vertically.
        :param orientation: Orientation string, either "horizontal" or "vertical".
        :raises ValueError: If orientation provided that isn't either "horizontal" or "vertical".
        """
        if orientation == "horizontal":
            self.h_flip()

        elif orientation == "vertical":
            self.v_flip()

        else:
            ValueError("Invalid value for orientation (either 'horizontal' or 'vertical').")

    def get_atom_positions(self):
        """
        Gets a list of positions for all atoms in the molecule.
        :return: List of position tuples.
        """
        return [(x,y) for x in range(self.dim[0]) for y in range(self.dim[1]) if self.get_atom((x, y))]

    def has_free_bonds(self):
        """
        Checks if a non-empty molecule has got free bonds.
        :return: True, if there are free bonds. Otherwise, False. Also, False for empty molecules.
        """
        for line in self.data:
            for atom in line:
                if atom and (sum(atom.bonds["free"]) > 0):
                    return True

        return False

    def delocalize_free_bonds(self):
        """
        Moves all free bonds for the respective atom for all atoms. This simulates electron delocalization.
        """
        for line in self.data:
            for atom in line:
                if atom:
                    atom.delocalize_free()

    def count_atoms(self, symbol):
        """
        Counts the number of atoms with a given symbol.
        :param symbol: CAtom symbol.
        :return: Number of matching atoms.
        """
        nr = 0
        for line in self.data:
            for atom in line:
                if atom and (not symbol or (atom.symbol == symbol)):
                    nr += 1

        return nr

    def count_bonds(self, bond):
        """
        Counts the number of single (bond=1), double (bond=2), or tiple bonds (bond=3).
        :param bond: Number representing the bond type 1..3.
        :return: Number of single, double, or triple bonds.
        """
        nr = 0
        for line in self.data:
            for atom in line:
                if atom:
                    bonds = sum(atom.bonds["bound"]) if bond is None else atom.bonds["bound"].count(bond)
                    nr += bonds

        return nr / 2

    def find_end_positions(self):
        """
        Finds all end positions in a molecule. This means: All positions for atoms connected to only one other atom. If
        there is none, then all positions for atoms connected to two other atoms.
        :return: List of atom coordinates as tuples (x, y).
        """
        end_positions = []
        for connections in range(1, 3):
            for row in range(self.dim[1]):
                for col in range(self.dim[0]):
                    atom = self.get_atom((col, row))
                    if atom and (atom.count_connected() == connections):
                        end_positions.append((col, row))

            if end_positions:
                return end_positions

        return []


    def equals(self, other):
        """
        Compares two CMolecules if they represent the same chemical molecule ignoring limitations of stereo-chemistry
        and rotational limitations (e.g, double bonds).
        :param other: Other CMolecule.
        :return: True if both molecule match, otherwise False.
        """

        def __compare_recursive__(pos1, pos2, mol1, mol2):

            # Copy act atoms
            atom1 = mol1.get_atom(pos1).copy()
            atom2 = mol2.get_atom(pos2).copy()

            # Check equal atoms
            if not atom1.equals(atom2):
                return False

            # Prepare to continue with neighbors
            bond_directions1 = [i for i in range(4) if atom1.bonds["bound"][i]]
            bond_directions2 = [i for i in range(4) if atom2.bonds["bound"][i]]

            # Copy molecules and remove atom from act pos
            n_mol1 = mol1.copy()
            n_mol1.set_atom(pos1, None)
            n_mol2 = mol2.copy()
            n_mol2.set_atom(pos2, None)

            for direction1 in bond_directions1:
                d_pos1 = CAtom.move(direction1)
                n_pos1 = (pos1[0] + d_pos1[0], pos1[1] + d_pos1[1])
                n_atom1 = mol1.get_atom(n_pos1)
                match = False

                if not bond_directions2:
                    return False

                for direction2 in bond_directions2:
                    d_pos2 = CAtom.move(direction2)
                    n_pos2 = (pos2[0] + d_pos2[0], pos2[1] + d_pos2[1])
                    n_atom2 = mol2.get_atom(n_pos2)

                    # Check both for None (both end in an atom checked before) -> True
                    if (n_atom1 is None) and (n_atom2 is None):
                        match = True

                    # Equal atoms -> recursive call
                    elif (n_atom1 is not None) and (n_atom2 is not None):
                        match = __compare_recursive__(n_pos1, n_pos2, n_mol1, n_mol2)

                    # Prevent checking the same branch twice
                    if match:
                        bond_directions2.remove(direction2)
                        break

                # All neighbors1 must return True
                if not match:
                    return False

            return True

        # Step 1: Compare statistics: Total number of atoms
        if self.count_atoms(None) != other.count_atoms(None):
            return False

        # Step 2: Compare statistics: Number of atoms for each symbol
        symbols = set([atom.symbol for line in self.data for atom in line if atom])
        for symbol in symbols:
            if self.count_atoms(symbol) != other.count_atoms(symbol):
                return False

        # Step 3: Compare statistics: Total number of bonds
        bonds1 = self.count_bonds(None)
        bonds2 = other.count_bonds(None)
        if bonds1 != bonds2:
            return False

        # Step 4: Compare statistics: Special case: equal single atom molecules
        if (bonds1 == 0) and (bonds2 == 0):
            return True

        # Step 5: Compare statistics: Number of bonds for each type
        for bond in range(1, 4):
            if self.count_bonds(bond) != other.count_bonds(bond):
                return False

        # Step 6: Find first end in self
        end1 = self.find_end_positions()[0] # Safe to skip check against [] as single atom molecules were excluded before
        atom1 = self.data[end1[1]][end1[0]]

        # Step 7: Find all ends with the same atom in other
        ends2 = []
        for y in range(other.dim[1]):
            for x in range(other.dim[0]):
                atom = other.get_atom((x, y))
                if atom and atom.equals(atom1):
                    ends2.append((x,y))

        # Step 8: Recursively compare for all possible ends of other until the first match
        for end2 in ends2:
            if __compare_recursive__(end1, end2, self, other):
                return True

        return False

    def copy(self):
        """
        Creates a copy of this object.
        :return: Copied CMolecule.
        """
        return self.__copy__()

    def __copy__(self):
        m = CMolecule(self.name, self.dim)
        m.data = [[self.get_atom((x, y)).copy() if self.get_atom((x, y)) else None for x in range(self.dim[0])] for y in range(self.dim[1])]
        return m

    def __str__(self):
        # TODO Bonds
        txt = ""
        for l in range(len(self.data)):
            line = self.data[l]
            for symbol in line:
                txt += symbol.symbol if symbol else " "
            if l < len(self.data) - 1:
                txt += "\n"

        return txt

    def __bool__(self):
        return self.dim != (0, 0)
