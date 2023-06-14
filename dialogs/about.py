# coding=utf-8
"""
Created on 12.5.2013
Updated on 1.6.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import widgets.gui_utils as gutils
import modules.general_functions as gf

from math import sin

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import uic


class AboutDialog(QtWidgets.QDialog):
    """About dialog that shows information about the program itself.
    """

    def __init__(self):
        """Inits the About Dialog.
        """

        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_about.ui", self)

        self.OKButton.clicked.connect(self.close)
        self.DiscoButton.clicked.connect(self.__disco)

        image = gf.get_root_dir() / "images" / "potku_logo_icon.svg"
        pixmap = QtGui.QPixmap(str(image))
        scaled_pixmap = pixmap.scaled(
            self.picture.size(), QtCore.Qt.KeepAspectRatio)
        self.picture.setPixmap(scaled_pixmap)

        version_number, version_date = gf.get_version_number_and_date()
        self.label_version.setText(f'Version {version_number}')
        self.label_date.setText(version_date)

        self.x = 0
        self.y = 2
        self.z = 3
        self.__timer = None
        self.exec_()

    def closeEvent(self, event):
        """Proper closing.
        """
        if self.__timer:
            self.__timer.stop()
        event.accept()  # let the window close

    def __disco(self):
        """Magic.
        """
        self.__timer = QtCore.QTimer(interval=10, timeout=self.__timeout)
        self.__timer.start()

    def __timeout(self):
        self.x += 0.1
        self.y += 0.1
        self.z += 0.1
        self.color_R = sin(self.x) * 127 + 127
        self.color_G = sin(self.y) * 127 + 127
        self.color_B = sin(self.z) * 127 + 127
        bg = "background-color: rgb({0},{1},{2});".format(self.color_R,
                                                          self.color_G,
                                                          self.color_B)
        self.setStyleSheet(bg)
