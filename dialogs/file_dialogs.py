# coding=utf-8
"""
Created on 29.1.2020

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

__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli " \
             "Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä " \
             "\n Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

from PyQt5 import QtWidgets


def open_file_dialog(parent, default_folder, title, files):
    """Opens open file dialog

    Opens dialog to select file to be opened and returns full file path to
    selected file if one is selected. If no file is selected returns None.

    Args:
        parent: Parent object which opens the open file dialog.
        default_folder: String representing which folder is shown when dialog
            opens.
        title: String representing open file dialog title.
        files: String representing what type of file can be opened.

    Returns:
        A full path to the selected filename if a file is selected. For
        example:

        "C:/Transfer/FinlandiaData/esimerkkidata.zip"
    """
    filename = QtWidgets.QFileDialog.getOpenFileName(parent, title,
                                                     default_folder,
                                                     parent.tr(files))
    return filename[0]


def open_files_dialog(parent, default_folder, title, files):
    """Opens open file dialog for multiple files

    Opens dialog to select files to be opened and returns full file path to
    selected file if one or more is selected.
    If no file is selected returns None.

    Args:
        parent: Parent object which opens the open file dialog.
        default_folder: String representing which folder is shown when dialog
            opens.
        title: String representing open file dialog title.
        files: String representing what type of file can be opened.

    Returns:
        A full path to the selected filename if a file is selected. For
        example:

        "C:/Transfer/FinlandiaData/esimerkkidata.zip"
    """
    filenames = QtWidgets.QFileDialog.getOpenFileNames(parent, title,
                                                       default_folder,
                                                       parent.tr(files))
    return filenames[0]     # TODO does this return just one?


def save_file_dialog(parent, default_folder, title, files):
    """Opens save file dialog

    Opens dialog to select savefile name and returns full file path to
    selected file if one is selected. If no file is selected returns None.

    Args:
        parent: Parent object which opens the open file dialog.
        default_folder: String representing which folder is shown when dialog
            opens.
        title: String representing open file dialog title.
        files: String representing what type of file can be opened.

    Returns:
        A full path to the selected filename if a file is selected. For
        example:

        "C:/Transfer/FinlandiaData/esimerkkidata.zip"
    """
    filename = QtWidgets.QFileDialog.getSaveFileName(parent, title,
                                                     default_folder,
                                                     parent.tr(files))[0]
    return filename