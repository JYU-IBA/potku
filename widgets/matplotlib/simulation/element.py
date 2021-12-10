# coding=utf-8
"""
Created on 1.3.2018
Updated on 28.8.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2021 Joonas Koponen

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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n " \
             "Sinikka Siironen \n Joonas Koponen"
__version__ = "2.0"

import copy
import platform

import modules.general_functions as general

from widgets.icon_manager import IconManager
from dialogs.energy_spectrum import EnergySpectrumParamsDialog
from dialogs.energy_spectrum import EnergySpectrumWidget
from dialogs.simulation.element_simulation_settings import \
    ElementSimulationSettingsDialog

from collections import Counter

from modules.recoil_element import RecoilElement
from modules.element_simulation import ElementSimulation
from modules.element import Element

from PyQt5 import QtWidgets

from widgets.simulation.circle import Circle
from widgets.simulation.recoil_element import RecoilElementWidget

BUTTON_MAX_WIDTH = 25


class ElementWidget(QtWidgets.QWidget):
    """Class for creating an element widget for the recoil atom distribution.
    """

    def __init__(self, parent, element: Element, parent_tab,
                 element_simulation: ElementSimulation, color,
                 icon_manager: IconManager, statusbar=None,
                 spectra_changed=None, recoil_name_changed=None,
                 settings_updated=None):
        """
        Initializes the ElementWidget.

        Args:
            parent: A RecoilAtomDistributionWidget.
            element: An Element object.
            parent_tab: A SimulationTabWidget.
            element_simulation: ElementSimulation object.
            color: Color for the circle.
            icon_manager: Icon manager.
            statusbar: PyQt statusbar
            spectra_changed: pyqtSignal that indicates a change in energy
                spectra
            recoil_name_changed: signal that indicates that a recoil name
                has changed.
        """
        super().__init__()

        self.parent = parent
        self.tab = parent_tab
        self.element_simulation = element_simulation
        self.statusbar = statusbar
        self.recoil_element: RecoilElement = \
            self.element_simulation.get_main_recoil()

        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)

        buttons = []
        instance_buttons = []

        self.radio_button = QtWidgets.QRadioButton()

        instance_buttons.append(self.radio_button)

        if element.isotope:
            isotope_superscript = general.digits_to_superscript(
                str(element.isotope))
            button_text = isotope_superscript + " " + element.symbol
        else:
            button_text = element.symbol

        self.radio_button.setText(button_text)

        # Circle for showing the recoil color
        self.circle = Circle(color)
        instance_buttons.append(self.circle)

        change_recoil_element_info = QtWidgets.QPushButton()
        change_recoil_element_info.setIcon(icon_manager.get_icon(
            "measuring_unit_settings.svg"))
        change_recoil_element_info.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)

        change_recoil_element_info.clicked.connect(parent.change_recoil_element_info)
        change_recoil_element_info.setToolTip("Modify the recoil element info")

        draw_spectrum_button = QtWidgets.QPushButton()
        draw_spectrum_button.setIcon(icon_manager.get_icon(
            "energy_spectrum_icon.svg"))
        draw_spectrum_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)

        draw_spectrum_button.clicked.connect(lambda: self.plot_spectrum(
            spectra_changed=spectra_changed))
        draw_spectrum_button.setToolTip("Draw energy spectra")

        settings_button = QtWidgets.QPushButton()
        settings_button.setIcon(icon_manager.get_icon("gear.svg"))
        settings_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                      QtWidgets.QSizePolicy.Fixed)
        settings_button.clicked.connect(
            lambda: self.open_element_simulation_settings(
                settings_updated=settings_updated))
        settings_button.setToolTip("Edit element simulation settings")

        add_recoil_button = QtWidgets.QPushButton()
        add_recoil_button.setIcon(icon_manager.get_icon("edit_add.svg"))
        add_recoil_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                        QtWidgets.QSizePolicy.Fixed)
        add_recoil_button.clicked.connect(lambda: self.add_new_recoil(
            spectra_changed=spectra_changed,
            recoil_name_changed=recoil_name_changed))
        add_recoil_button.setToolTip("Add a new recoil to element")

        if platform.system() == "Darwin":
            horizontal_layout.setContentsMargins(0, 0, 12, 0)

        change_recoil_element_info.setMaximumWidth(BUTTON_MAX_WIDTH)
        draw_spectrum_button.setMaximumWidth(BUTTON_MAX_WIDTH)
        settings_button.setMaximumWidth(BUTTON_MAX_WIDTH)
        add_recoil_button.setMaximumWidth(BUTTON_MAX_WIDTH)

        horizontal_layout.addWidget(self.radio_button)
        horizontal_layout.addWidget(self.circle)
        horizontal_layout.addWidget(change_recoil_element_info)
        horizontal_layout.addWidget(draw_spectrum_button)
        horizontal_layout.addWidget(settings_button)
        horizontal_layout.addWidget(add_recoil_button)

        self.setLayout(horizontal_layout)

        self.running_int_recoil = 1

    def add_new_recoil(self, spectra_changed=None, recoil_name_changed=None):
        """
        Add new recoil to element simulation.
        """
        points = copy.deepcopy(
            self.element_simulation.get_main_recoil().get_points())

        element = copy.copy(
            self.element_simulation.get_main_recoil().element)
        name = "Default-" + str(self.running_int_recoil)

        color = self.element_simulation.get_main_recoil().color

        if self.element_simulation.simulation_type == "ERD":
            rec_type = "rec"
        else:
            rec_type = "sct"

        recoil_element = RecoilElement(element, points, color, name,
                                       rec_type=rec_type)
        self.running_int_recoil += 1
        recoil_widget = RecoilElementWidget(
            self.parent, self.tab, self, self.element_simulation,
            color, recoil_element, statusbar=self.statusbar,
            spectra_changed=spectra_changed,
            recoil_name_changed=recoil_name_changed
        )
        recoil_element.widgets.append(recoil_widget)
        self.element_simulation.recoil_elements.append(recoil_element)

        self.parent.radios.addButton(recoil_widget.radio_button)
        # Add recoil widget under ite element simulation's element widget
        for i in range(self.parent.recoil_vertical_layout.count()):
            if self.parent.recoil_vertical_layout.itemAt(i).widget() == self:
                self.parent.recoil_vertical_layout.insertWidget(i + 1,
                                                                recoil_widget)
                break
        recoil_widget.radio_button.setChecked(True)

        # Save recoil element
        recoil_element.to_file(self.element_simulation.directory)

    def open_element_simulation_settings(self, settings_updated=None):
        """
        Open element simulation settings.
        """
        es = ElementSimulationSettingsDialog(self.element_simulation, self.tab)
        if settings_updated is not None:
            es.settings_updated.connect(settings_updated.emit)
        es.exec_()

    def plot_spectrum(self, spectra_changed=None):
        """Plot an energy spectrum and show it in a widget.
        """
        previous = None
        dialog = EnergySpectrumParamsDialog(
            self.tab,
            spectrum_type=EnergySpectrumWidget.SIMULATION,
            element_simulation=self.element_simulation,
            simulation=self.tab.obj,
            recoil_widget=self,
            statusbar=self.statusbar)
        if dialog.result_files:
            energy_spectrum_widget = EnergySpectrumWidget(
                parent=self.tab,
                use_cuts=dialog.result_files,
                bin_width=dialog.bin_width,
                spectrum_type=EnergySpectrumWidget.SIMULATION,
                spectra_changed=spectra_changed,
                simulated_sum_spectrum_is_selected=dialog.simulated_sum_spectrum_is_selected,
                measured_sum_spectrum_is_selected=dialog.measured_sum_spectrum_is_selected)

            # Check all energy spectrum widgets, if one has the same
            # elements, delete it
            for e_widget in self.tab.energy_spectrum_widgets:
                keys = e_widget.energy_spectrum_data.keys()
                if Counter(keys) == Counter(
                        energy_spectrum_widget.energy_spectrum_data.keys()):
                    previous = e_widget
                    self.tab.energy_spectrum_widgets.remove(e_widget)
                    self.tab.del_widget(e_widget)
                    break

            self.tab.energy_spectrum_widgets.append(
                energy_spectrum_widget)
            icon = self.parent.element_manager.icon_manager.get_icon(
                "energy_spectrum_icon_16.png")
            self.tab.add_widget(energy_spectrum_widget, icon=icon)

            if previous and energy_spectrum_widget is not None:
                energy_spectrum_widget.save_file_int = previous.save_file_int
                energy_spectrum_widget.save_to_file(measurement=False,
                                                    update=True)
            elif not previous and energy_spectrum_widget is not None:
                energy_spectrum_widget.save_to_file(measurement=False,
                                                    update=False)
