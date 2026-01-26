from cphysics import CAcceleration, CSpin
from ctriangle import CTriangle


class CFlyingTriangle(CTriangle, CAcceleration, CSpin):
    """
    CTriangle class implementing physics.
    """
    def __init__(self, *args, **kwargs):
        if args and (type(args[0]) == CTriangle):
            a = args[0]
            CTriangle.__init__(self,
                               pos=a.pos, size=a.size, top=a.top, right=a.right, center=a.center,
                               cls=a.cls, size_hint=a.size_hint, size_hint_min=a.size_hint_min,
                               size_hint_max=a.size_hint_max, opacity=a.opacity,
                               disabled=a.disabled, motion_filter=a.motion_filter,
                               p1=a.p1, p2=a.p2, p3=a.p3, rgba=a.rgba, angle=a.angle, image=a.image)
        else:
            CTriangle.__init__(self, **kwargs)
        CAcceleration.__init__(self)
        CSpin.__init__(self)