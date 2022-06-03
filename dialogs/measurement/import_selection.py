from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic
import os
from pathlib import Path
import dialogs.file_dialogs as fdialogs
import widgets.gui_utils as gutils
from modules.selection import Selector

class SelectionDialog(QtWidgets.QDialog):

    def __init__(self):

        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_selection_dialog.ui", self)
        self.setWindowTitle("Choose selection")

        self.chosen_selections = None
        self.current_selections = None
        self.filename = None


        self.pushButton_ChooseSelection.clicked.connect(self.load_selection)
        self.pushButton_Cancel.clicked.connect(self.close)
        self.pushButton_OK.clicked.connect(self.on_clicked)


    def load_selection(self):
        """Show dialog to load selections."""

        filename = fdialogs.open_file_dialog(self, Path(os.getcwd()),
                                             "Load Element Selection",
                                             "Selection file (*.selections)")
        self.filename = filename
        if filename is None:
            return
        elements, current_selections = Selector.load_chosen(self, filename)
        self.current_selections = current_selections
        self.treeWidget.clear() #Clears old selections from the tree
        self.set_elements(elements)

    def set_elements(self, elements):
        """Sets the elements to the tree with checkboxes

        Args:
            elements: List of elements from the chosen selections file
        """

        for element in elements:
            self.tree_element = QtWidgets.QTreeWidgetItem([element])
            self.tree_element.setCheckState(0, QtCore.Qt.Checked)
            self.treeWidget.addTopLevelItem(self.tree_element)

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

