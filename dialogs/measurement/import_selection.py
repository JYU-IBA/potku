import json

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic
import os
from pathlib import Path
import widgets.gui_utils as gutils
from modules.selection import Selector, Selection


class SelectionDialog(QtWidgets.QDialog):

    def __init__(self, selector, filename: Path):

        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_selection_dialog.ui", self)
        self.setWindowTitle("Choose selections")
        self.selector = selector
        self.chosen_selections = None

        self.pushButton_Cancel.clicked.connect(self.close)
        self.pushButton_OK.clicked.connect(self.on_clicked)
        self.load_selection(filename)

    def load_selection(self, filename: Path):
        selections = []
        with filename.open() as f:
            for line in f:
                sel = Selection.from_string(None, None, None, line)
                if sel:
                    selections.append(sel)
        self.set_selections(selections)

    def set_selections(self, selections):
        """Sets the elements to the tree with checkboxes

        Args:
            selections: List of selections from the chosen selections file
        """
        self.current_selections = selections
        self.treeWidget.clear()

        for selection in selections:
            tree_element = QtWidgets.QTreeWidgetItem([selection.name()])
            tree_element.setCheckState(0, QtCore.Qt.Checked)
            self.treeWidget.addTopLevelItem(tree_element)

    @QtCore.pyqtSlot()
    def on_clicked(self):
        """Makes a list of the chosen selections"""

        chosen_selections = []

        # Checks which elements are checked
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            if item.checkState(0) == QtCore.Qt.Checked:
                chosen_selections.append(self.current_selections[i])

        self.chosen_selections = chosen_selections
        self.close()
