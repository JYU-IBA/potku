
from matplotlib.patches import Ellipse, Circle


class Point:

    def __init__(self, parent, x, y, size=0.3):

        self.parent = parent
        self.is_selected = False
        self.x = x
        self.y = y
        self.size = size
        self.point = Ellipse((x,y), size, size, fc="r")  # Maybe replace this with a marker
        parent.axes.add_patch(self.point)

    def on_press(self, event):

        # If the cursor is not inside the point, do nothing
        if event.inaxes != self.point.axes: return
