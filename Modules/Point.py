
from matplotlib.patches import Ellipse

class Point:

    def __init__(self, x, y, size=0.1):

        self.is_selected = False
        self.x = x
        self.y = y
        self.size = size
        self.point = Ellipse((x,y), size, size)

    def on_press(self, event):

        # If the cursor is not inside the point, do nothing
        if event.inaxes != self.point.axes: return