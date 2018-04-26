# coding=utf-8
"""
Created on 28.3.2018
Updated on ...

TODO: Add licence and copyright information
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen"

from os.path import join
from PyQt5 import QtCore, uic, QtWidgets

from widgets.matplotlib.simulation.recoil_atom_distribution import RecoilAtomDistributionWidget
from widgets.matplotlib.simulation.composition import TargetCompositionWidget
from modules.target import Target


class TargetWidget(QtWidgets.QWidget):
    '''HistogramWidget used to draw ToF-E Histograms.
    '''

    def __init__(self, tab, target, icon_manager):
        '''Inits TofeHistogramWidget widget.

        Args:
            icon_manager: An icon manager class object.
        '''
        super().__init__()
        self.ui = uic.loadUi(join("ui_files", "ui_target_widget.ui"), self)
        # self.ui.addLayerButton.clicked.connect(self.add_layer)
        # self.ui.removeLayerButton.clicked.connect(self.remove_layer)

        # Add the TargetCompositionWidget and RecoilAtomDistributionWidget to
        # stackedWidget.
        #self.ui.stackedWidget.children()[1].setLayout(QtWidgets.QHBoxLayout)
        #self.ui.stackedWidget.children()[2].setLayout(QtWidgets.QHBoxLayout)

        self.tab = tab

        TargetCompositionWidget(self, target, icon_manager)
        self.recoil_widget = RecoilAtomDistributionWidget(self, target, icon_manager)
        self.ui.recoilListWidget.hide()
        self.ui.editLockPushButton.hide()

        self.ui.targetRadioButton.clicked.connect(lambda: {self.ui.stackedWidget.setCurrentIndex(0),
                                                           self.ui.recoilListWidget.hide(),
                                                           self.ui.editLockPushButton.hide()})
        self.ui.recoilRadioButton.clicked.connect(lambda: {self.ui.stackedWidget.setCurrentIndex(1),
                                                           self.ui.recoilListWidget.show(),
                                                           self.ui.editLockPushButton.show(),
                                                           self.recoil_widget.update_layer_borders(),
                                                           self.recoil_widget.update_elements()})

        self.ui.targetRadioButton.setChecked(True)
        self.ui.stackedWidget.setCurrentIndex(0)

        self.ui.setWindowTitle("Otsikko") # TODO: Change title
        self.set_shortcuts()

    def add_layer(self):
        """Adds a layer in the target composition.
        """
        self.targetWidget.add_layer()

    def remove_layer(self):
        """Removes a layer in the target composition.
        """
        QtWidgets.QMessageBox.critical(self, "Error", "Not implemented",
                                       QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)

    def set_shortcuts(self):
        # Toggle rectangle selector
        # self.rec_sel = QtWidgets.QShortcut(self)
        # self.rec_sel.setKey(QtCore.Qt.Key_R)
        # self.rec_sel.activated.connect(
        #     lambda: self.matplotlib.toggle_rectangle_selector())
        # Delete selected point(s)
        self.del_points = QtWidgets.QShortcut(self)
        self.del_points.setKey(QtCore.Qt.Key_Delete)
        self.del_points.activated.connect(lambda: self.recoil_widget.remove_points())
