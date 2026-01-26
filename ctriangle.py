from kivy.graphics import Color, Triangle, Rectangle, StencilPush, StencilUse, StencilUnUse, StencilPop, PushMatrix, \
    PopMatrix, Rotate, Translate
from kivy.properties import NumericProperty, ReferenceListProperty, ColorProperty, ObjectProperty
from kivy.uix.widget import Widget


class CTriangle(Widget):
    """
    Widget containing a triangle. The triangle is defined by the three points p1, p2, and p3 (and/or by their
    respective x and y coordinates: x1, y1, x2, y2, x3, y3). The triangle is either shown in monocolor or using a
    image texture depending on an image provided.
    """

    x1 = NumericProperty(0)
    y1 = NumericProperty(0)
    p1 = ReferenceListProperty(x1, y1)
    x2 = NumericProperty(0)
    y2 = NumericProperty(0)
    p2 = ReferenceListProperty(x2, y2)
    x3 = NumericProperty(0)
    y3 = NumericProperty(0)
    p3 = ReferenceListProperty(x3, y3)

    rgba = ColorProperty([.5, .5, .5, 1])
    texture = ObjectProperty()
    image = ObjectProperty()
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update, size=self.update,
                  p1=self.update, p2=self.update, p3=self.update, rgba=self.update, angle=self.update,
                  image=self.update)
        self.update()

    def clone(self):
        """
        Clone this object except its parents, children, ids and canvas.
        :return: Copy of this object.
        """
        t = CTriangle(pos=self.pos, size=self.size, top=self.top, right=self.right, center=self.center,
                      cls=self.cls, size_hint=self.size_hint, size_hint_min=self.size_hint_min,
                      size_hint_max=self.size_hint_max, opacity=self.opacity,
                      disabled=self.disabled, motion_filter=self.motion_filter,
                      p1=self.p1, p2=self.p2, p3=self.p3, rgba=self.rgba, angle=self.angle, image=self.image)
        return t

    def update(self, *args):
        """
        Redraws this object.
        :param args: Unused.
        """
        self.canvas.clear()
        with self.canvas:
            PushMatrix()
            # Matrix operations
            Translate(x=self.x, y=self.y)
            Rotate(angle=self.angle, origin=self.gravity_center())
            StencilPush()
            # Stencil
            Triangle(points=(self.x1, self.y1, self.x2, self.y2, self.x3, self.y3))
            StencilUse()
            # Draw
            if self.image:
                Rectangle(pos=(0, 0), size=self.image.size, texture=self.image.texture)
            else:
                Color(rgba=self.rgba)
                Rectangle(pos=(0, 0), size=self.size)
            StencilUnUse()
            # Remove stencil
            Triangle(points=(self.x1, self.y1, self.x2, self.y2, self.x3, self.y3))
            StencilPop()
            PopMatrix()

    def collide_widget(self, wid):
        """
        Check if another widget collides with the **triangle area** of this widget.
        :param wid: Other widget to check.
        :return: True if collides, False otherwise.
        """
        if self.x + max(self.x1, self.x2, self.x3) < wid.x:
            return False
        if self.x + min(self.x1, self.x2, self.x3) > wid.right:
            return False
        if self.y + max(self.y1, self.y2, self.y3) < wid.y:
            return False
        if self.y + min(self.y1, self.y2, self.y3) > wid.top:
            return False
        return True

    def gravity_center(self):
        """
        Calculates the center of gravity of this object based on its triangle points.
        :return: x, y coordinates of center of gravity.
        """
        return (self.x1 + self.x2 + self.x3) / 3, (self.y1 + self.y2 + self.y3) / 3

    def split(self, p_idx, ratio):
        """
        Splits this object into two new triangle objects. The split line has to cross at least one of the three
        triangle points and the opposite line.
        :param p_idx: Index of the triangle point (1, 2 or 3).
        :param ratio: Ratio where to cross the opposite line (0.0 to 1.0).
        :return: Two new triangle objects.
        """

        if (ratio < 0) or (ratio > 1):
            raise ValueError("ratio must be between 0.0 and 1.0, but is " + str(ratio) + ".")

        t1 = self.clone()
        t2 = self.clone()
        if p_idx == 1:
            xn = self.x2 + ratio * (self.x3 - self.x2)
            yn = self.y2 + ratio * (self.y3 - self.y2)
            t1.p3 = (xn, yn)
            t2.p2 = (xn, yn)
        elif p_idx == 2:
            xn = self.x3 + ratio * (self.x1 - self.x3)
            yn = self.y3 + ratio * (self.y1 - self.y3)
            t1.p3 = (xn, yn)
            t2.p1 = (xn, yn)
        elif p_idx == 3:
            xn = self.x1 + ratio * (self.x2 - self.x1)
            yn = self.y1 + ratio * (self.y2 - self.y1)
            t1.p2 = (xn, yn)
            t2.p1 = (xn, yn)
        else:
            raise ValueError("p_idx must be 1 or 2 or 3, but is " + str(p_idx) + ".")
        # TODO Textures, optimize
        return t1, t2

    def split_longest(self, ratio):
        """
        Splits this object into two new triangle objects. The split line crosses the longest line of the triangle and
        its opposite point.
        :param ratio: Ratio where to cross the longest line (0.0 to 1.0).
        :return: Two new triangle objects.
        """
        a2 = (self.x2 - self.x1) ** 2 + (self.y2 - self.y1) ** 2
        b2 = (self.x3 - self.x2) ** 2 + (self.y3 - self.y2) ** 2
        c2 = (self.x1 - self.x3) ** 2 + (self.y1 - self.y3) ** 2

        if (a2 > b2) and (a2 > c2):
            return self.split(p_idx=3, ratio=ratio)
        elif (b2 > a2) and (b2 > c2):
            return self.split(p_idx=1, ratio=ratio)
        else:
            return self.split(p_idx=2, ratio=ratio)