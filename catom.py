class CAtom:
    def __init__(self, symbol: str, name: str, rgba: list[float], bonds: int | dict[str, list[int]]):
        """
        Creates an atom object.
        :param symbol: Chemical symbol.
        :param name: Atom name.
        :param rgba: Color as RGBA [0.0..1.0, 0.0..1.0, 0.0..1.0, 0.0..1.0].
        :param bonds: Either the number of bonds 1..4 or a dict with lists of free and bound electrons for each direction.
        """
        self.symbol = symbol
        self.name = name
        self.rgba = rgba
        self.bonds = {"free": [1 if i < bonds else 0 for i in range(4)],
                      "bound": [0, 0, 0, 0]} if type(bonds) == int else bonds
        self.image = None

    @classmethod
    def from_dict(cls, d):
        """
        Creates a CAtom object from a dict.
        :param d: Dict with parameters symbol, name, color (either RGB or RGBA), and bonds.
        :return: Created CAtom.
        """
        return cls(d["symbol"], d["name"], d["color"] if len(d["color"]) == 4 else d["color"] + [1.0], d["bonds"])

    @staticmethod
    def move(direction):
        """
        Converts a direction to a positional change.
        :param direction: Direction as int 0..3.
        :return: Change in position as tuple (dx, dy).
        """
        dx = (direction % 2) * (1 + (direction // 2) * -2)
        dy = ((direction + 1) % 2) * (-1 + (direction // 2) * 2)
        return dx, dy

    @staticmethod
    def direction(d_pos):
        """
        Converts a normalized positional change in a direction.
        :param d_pos: Change in position as tuple (dx, dy).
        :return: Change in position as tuple (dx, dy).
        """
        dx, dy = d_pos
        return ((dy + 2) // 2) * 2 - dx

    @staticmethod
    def opposite_direction(direction):
        """
        Gets the opposite direction.
        :param direction: Direction as int 0..3.
        :return: Opposite direction as int 0..3.
        """
        return (direction + 2) % 4

    def delocalize_free(self):
        """
        Moves all free bonds of an atom. This simulates electron delocalization.
        """

        # Either random swap
        # destinations = [i for i in range(4) if (self.bonds["bound"][i] == 0) and (self.bonds["free"][i] == 0)]
        # sources = [i for i in range(4) if self.bonds["free"][i] != 0]
        # if (len(sources) >= 1) and (len(destinations) >= 1):
        #     s = random.choice(sources)
        #     d = random.choice(destinations)
        #     temp = self.bonds["free"][d]
        #     self.bonds["free"][d] = self.bonds["free"][s]
        #     self.bonds["free"][s] = temp

        # Or rotation
        destinations = [i for i in range(4) if self.bonds["bound"][i] == 0]
        if len(destinations) > 0:
            temp = self.bonds["free"][destinations[0]]
            for i in range(len(destinations) - 1):
                self.bonds["free"][destinations[i]] = self.bonds["free"][destinations[i + 1]]
            self.bonds["free"][destinations[-1]] = temp

    def count_connected(self):
        """
        Counts the number of connected other atoms (NOT bonds).
        :return: Number of connected other atoms.
        """
        return sum(1 for bond in self.bonds["bound"] if bond)

    def equals(self, other):
        """
        Compares two atoms and returns True if both atoms have got the same symbol, the same number bond in respect of
        each: (i) single bonds, (ii) double bonds, and (iii) triple bonds.
        :param other: Other CAtom.
        :return: True or False.
        """
        return (self.symbol == other.symbol) and \
               (self.bonds["bound"].count(1) == other.bonds["bound"].count(1)) and \
               (self.bonds["bound"].count(2) == other.bonds["bound"].count(2)) and \
               (self.bonds["bound"].count(3) == other.bonds["bound"].count(3))


    def copy(self):
        """
        Creates a copy of this CAtom object.
        :return: Copy of this object.
        """
        return self.__copy__()

    def __copy__(self):
        n_atom = CAtom(self.symbol,
                       self.name,
                       self.rgba.copy(),
                       {"free": self.bonds["free"].copy(),
                        "bound": self.bonds["bound"].copy()})
        n_atom.image = self.image
        return n_atom

    def __str__(self):
        return self.symbol

