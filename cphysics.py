class CMotion:
    """
    Physics abstract class implementing s = v * t using points and frames.
    Member properties x and y must be provided upon implementation.
    """
    x_velocity: float = 0
    """
    Velocity along x axis in points per frame.
    """

    y_velocity: float = 0
    """
    Velocity along y axis in points per frame.
    """

    def __init__(self, x_velocity: float = 0, y_velocity: float = 0):
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity

    def move(self, frames: float):
        """
        Changes position in points (x, y) after the provided number of frames using the velocity properties.
        x and y must be provided by the implementation.
        :param frames: Time in frames.
        """
        self.x += self.x_velocity * frames
        self.y += self.y_velocity * frames

    def stop(self):
        """
        Stops movement of this object by setting the x velocity and y velocity to zero.
        """
        self.x_velocity = 0
        self.y_velocity = 0


class CSpin:
    """
    Physics abstract class implementing alpha = spin * t using frames.
    Member property angle must be provided upon implementation.
    """

    spin: float = 0
    """
    Spin angle (in degrees).
    """

    def __init__(self, spin: float = 0):
        self.spin = spin

    def rotate(self, frames: float):
        """
        Changes rotation angle in degrees. Property angle must be provided by the implementation.
        :param frames: Time in frames.
        """
        self.angle += self.spin * frames

class CAcceleration(CMotion):
    """
    Physics class implementing v = a * t using frames.
    Inherited member properties x and y must be provided upon implementation.
    """

    x_acceleration: float = 0
    """
    Acceleration along x axis in points per frame^2.
    """

    y_acceleration: float = 0
    """
    Acceleration along y axis in points per frame^2.
    """

    def __init__(self,
                 x_acceleration: float = 0, y_acceleration: float = 0,
                 x_velocity: float = 0, y_velocity: float = 0):
        super().__init__(x_velocity, y_velocity)
        self.x_acceleration = x_acceleration
        self.y_acceleration = y_acceleration

    def move(self, frames: float):
        """
        Changes position in points (x, y) after the provided number of frames using acceleration and velocity
        properties. Inherited member properties x and y must be provided upon implementation.
        :param frames: Time in frames.
        """
        self.x_velocity += self.x_acceleration * frames
        self.y_velocity += self.y_acceleration * frames
        super().move(frames)

