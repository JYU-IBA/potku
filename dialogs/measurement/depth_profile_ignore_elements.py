# coding=utf-8
"""
Created on 5.8.2013
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

MatplotlibDepthProfileWidget handles the drawing and operation of the
depth profile graph.
"""
__author__ = "Timo Konu \n Severi Jääskeläinen \n Samuel Kaiponen \n Heta " \
             "Rekilä \n Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import widgets.gui_utils as gutils
import widgets.binding as bnd

from modules.element import Element

from typing import Set
from typing import List

from PyQt5 import uic
from PyQt5 import QtWidgets


class DepthProfileIgnoreElements(QtWidgets.QDialog):
    """
    Dialog for ignoring elements in a depth profile.
    """

    included_in_graph = bnd.bind("tree_elements")
    included_in_ratio = bnd.bind("tree_ratio")

    @property
    def ignored_from_graph(self):
        try:
            return self._get_ignored(set(self.included_in_graph))
        except AttributeError:
            return set()

    @property
    def ignored_from_ratio(self):
        try:
            return self._get_ignored(set(self.included_in_ratio))
        except AttributeError:
            return set()

    def _get_ignored(self, included):
        return {
            elem for elem in self._elements if elem not in included
        }

    def __init__(self, elements: List[Element], ignored_graph: Set[Element],
                 ignored_ratio: Set[Element]):
        """Init the dialog.
        
        Args:
            elements: A list of elements in Depth Profile.
            ignored_graph: A list of elements ignored previously for the graph.
            ignored_ratio: A list of elements ignored previously for ratio
                calculation.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile_ignored.ui", self)

        self._elements = sorted(set(elements))
        self.button_ok.clicked.connect(self.accept)
        self.button_cancel.clicked.connect(self.reject)

        # Fill the trees
        gutils.fill_tree(
            self.tree_elements.invisibleRootItem(), self._elements)
        gutils.fill_tree(
            self.tree_ratio.invisibleRootItem(), self._elements)

        self.included_in_graph = set(
            elem for elem in self._elements if elem not in ignored_graph
        )
        self.included_in_ratio = set(
            elem for elem in self._elements if elem not in ignored_ratio
        )
