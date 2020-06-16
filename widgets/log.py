# coding=utf-8
"""
Created on 16.4.2013
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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

from pathlib import Path

from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtWidgets


class LogWidget(QtWidgets.QWidget):
    """Log widget which displays the log. This widget handles
    the loghandlers emits.
    """
    on_log_message = QtCore.pyqtSignal(str)
    on_error_message = QtCore.pyqtSignal(str)

    def __init__(self):
        """Initializes the LogHandler widget.
        """
        super().__init__()
        uic.loadUi(Path("ui_files", "ui_log_widget.ui"), self)
        # This is used to ensure that the window can't be closed.        
        self.want_to_close = False
        self.hideButton.clicked.connect(self.minimize_window)
        self.on_log_message.connect(self.add_text)
        self.on_error_message.connect(self.add_error)

    def add_text(self, message):
        """Adds the specified message to the log field.

        Args:
            message: the message which will be displayed.
        """
        self.defaultLogText.append(message)

    def add_error(self, message):
        """Adds the specified message to the error field.

        Args:
            message: the message which will be displayed.
        """
        self.errorLogText.append(message)

    def closeEvent(self, close_event):  # Inherited
        """Event which happens when the windows is closing.

        Instead of closing, minimize the window. This is because the disabling
        of the close button isn't implemented yet.

        Args:
            close_event: Close event
        """
        if self.want_to_close:
            super(LogWidget, self).closeEvent(close_event)
        else:
            close_event.ignore()
            self.minimize_window()

    def minimize_window(self):
        """Minimize the window.
        """
        self.setWindowState(QtCore.Qt.WindowMinimized)
