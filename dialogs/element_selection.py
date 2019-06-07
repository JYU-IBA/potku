# coding=utf-8
"""
Created on 25.3.2013
Updated on 30.5.2018

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

Opens a element selection dialog.
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os

from PyQt5 import uic
from PyQt5 import QtWidgets


class ElementSelectionDialog(QtWidgets.QDialog):
    """ElementSelectionDialog opens a periodic table from which user can select
    an element.
    """

    def __init__(self):
        """Inits the ElementSelection class
        """
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_element_selection.ui"),
                             self)
        buttons = self.ui.findChild(QtWidgets.QButtonGroup, "elementButtons")
        buttons.buttonClicked.connect(self.__set_element)
        self.ui.pushButton_Cancel.clicked.connect(self.close)
        self.element = None
        self.exec_()

    def __set_element(self, button):
        """Sets the element to the corresponding button's text.
        
        Args:
            button: Dialog's QPushButton whose text is set as the selected
            element.
        """
        self.element = button.text()
        self.close()
