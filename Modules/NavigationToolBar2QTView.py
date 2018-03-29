from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

class NavigationToolBar2QTView(NavigationToolbar):

    def __init__(self, canvas, main_frame):
        super().__init__(canvas, main_frame)
        self._views = [[0], [0]]

