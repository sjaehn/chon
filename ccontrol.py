import math


class CControl:
    """
    Generic class for all controls.
    """
    def __init__(self, **kwargs):
        """
        Initializes a control object.
        :param kwargs: Keyword arguments passed to the control object.
        Possible arguments depending on the device: type, min_dist, max_dist, min_angle, max_angle, is_double_tap,
        is_triple_tap, ...
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def equals(self, **kwargs):
        """
        Compares if provided parameters matches with this object.
        :param kwargs: Keyword arguments passed to the control object.
        Possible arguments depending on the device: type, dx, dy, is_double_tap, is_triple_tap, ...

        :return: True, if matches, False otherwise.
        """

        # Calculate and analyze dist, angle for 2d input devices (touch, TODO joystick)
        dx = kwargs["dx"] if "dx" in kwargs else 0
        dy = kwargs["dy"] if "dy" in kwargs else 0
        if (dx or dy) and (not hasattr(self, "dx")) and (not hasattr(self, "dy")):
            dist = math.sqrt(dx**2 + dy**2)
            angle = 180 * math.atan2(-dy, dx) / math.pi if dist != 0 else 0
            min_dist = getattr(self, "min_dist") if hasattr(self, "min_dist") else 0
            max_dist = getattr(self, "max_dist") if hasattr(self, "max_dist") else math.inf
            min_angle = getattr(self, "min_angle") if hasattr(self, "min_angle") else -180
            max_angle = getattr(self, "max_angle") if hasattr(self, "max_angle") else 180

            if dist < min_dist or dist > max_dist:
                return False

            if not ((angle >= min_angle and (angle <= max_angle)) or
                    (angle >= min_angle + 360 and (angle <= max_angle + 360))):
                return False

        # All other kwargs: direct comparison
        for key, value in kwargs.items():
            if (hasattr(self, key)) and (value != getattr(self, key)):
                return False

        return True