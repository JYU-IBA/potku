# coding=utf-8
"""
Created on 5.4.2013
Updated on 4.12.2018

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

from pathlib import Path
from typing import List
from typing import Optional

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QMessageBox

import dialogs.dialog_functions as df
import modules.cut_file as cut_file
import modules.depth_files as depth_files
import widgets.binding as bnd
import widgets.gui_utils as gutils
from modules.element import Element
from modules.enums import DepthProfileUnit
from modules.global_settings import GlobalSettings
from modules.measurement import Measurement
from modules.observing import ProgressReporter
from widgets.base_tab import BaseTab
from widgets.gui_utils import StatusBarHandler
from widgets.matplotlib.measurement.depth_profile import \
    MatplotlibDepthProfileWidget


class DepthProfileDialog(QtWidgets.QDialog):
    """
    Dialog for making a depth profile.
    """
    # TODO replace these global variables with PropertySavingWidget.
    #   These should not be mutated because they are (static) class variables
    #   instead of member variables.
    checked_cuts = {}
    x_unit = DepthProfileUnit.ATOMS_PER_SQUARE_CM
    line_zero = False
    line_scale = False
    used_eff = True
    systerr = 0.0

    status_msg = bnd.bind("label_status")
    used_cuts = bnd.bind("treeWidget")
    cross_sections = bnd.bind("label_cross")
    tof_slope = bnd.bind("label_calibslope")
    tof_offset = bnd.bind("label_caliboffset")
    depth_stop = bnd.bind("label_depthstop")
    depth_steps = bnd.bind("label_depthnumber")
    depth_bin = bnd.bind("label_depthbin")
    depth_scale = bnd.bind("label_depthscale")
    used_efficiency_files = bnd.bind("label_efficiency_files")
    warning = bnd.bind("label_warning_text")

    systematic_error = bnd.bind("spin_systerr")
    show_scale_line = bnd.bind("check_scaleline")
    show_used_eff = bnd.bind("show_eff")
    show_zero_line = bnd.bind("check_0line")
    reference_density = bnd.bind("sbox_reference_density")
    x_axis_units = bnd.bind("group_x_axis_units")

    def __init__(self, parent: BaseTab, measurement: Measurement,
                 global_settings: GlobalSettings,
                 statusbar: Optional[QtWidgets.QStatusBar] = None):
        """Inits depth profile dialog.
        
        Args:
            parent: a MeasurementTabWidget.
            measurement: a Measurement object
            global_settings: a GlobalSettings object
            statusbar: a QStatusBar object
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile_params.ui", self)

        # Basic stuff
        self.parent = parent
        self.measurement = measurement
        self.statusbar = statusbar

        # Connect buttons
        self.OKButton.clicked.connect(self._accept_params)
        self.cancelButton.clicked.connect(self.close)

        locale = QLocale.c()
        self.spin_systerr.setLocale(locale)
        self.sbox_reference_density.setLocale(locale)

        m_name = self.measurement.name
        if m_name not in DepthProfileDialog.checked_cuts:
            DepthProfileDialog.checked_cuts[m_name] = set()

        gutils.fill_cuts_treewidget(
            self.measurement,
            self.treeWidget.invisibleRootItem(),
            use_elemloss=True)
        self.used_cuts = DepthProfileDialog.checked_cuts[m_name]

        self._update_label()
        self.treeWidget.itemClicked.connect(self._update_label)

        gutils.set_btn_group_data(self.group_x_axis_units, DepthProfileUnit)
        self.x_axis_units = DepthProfileDialog.x_unit
        if self.x_axis_units == DepthProfileUnit.NM:
            self._show_reference_density()
        else:
            self._hide_reference_density()

        self.radioButtonNm.clicked.connect(self._show_reference_density)
        self.radioButtonAtPerCm2.clicked.connect(
            self._hide_reference_density)

        self.systematic_error = DepthProfileDialog.systerr

        # Checkboxes
        self.systematic_error = DepthProfileDialog.systerr
        self.show_scale_line = DepthProfileDialog.line_scale
        self.show_zero_line = DepthProfileDialog.line_zero
        self.show_used_eff = DepthProfileDialog.used_eff

        self.cross_sections = global_settings.get_cross_sections()

        self._show_measurement_settings()
        self._show_efficiency_files()
        # Does not work correctly if self is replaced with DepthProfileDialog
        self.eff_files_str = self.used_efficiency_files

        self.exec_()

    def _update_label(self):
        if len(self.used_cuts) <= 1:
            self.label_warning_text.setText('')
            return
        else:
            elements = [Element.from_cutfile_string(fp.name) for fp in self.used_cuts]
            seen = []
            duplicates = []
            for element in elements:
                if element not in seen:
                    seen.append(element)
                elif element not in duplicates:
                    duplicates.append(element)
            if not duplicates:
                self.label_warning_text.setText('')
                return

            self.label_warning_text.setText("Multiple cutfiles for {}\n"
                                            "Check elemental losses".format(" and ".join([str(d) for d in duplicates])))
            self.label_warning_text.setStyleSheet("color: red")

    @gutils.disable_widget
    def _accept_params(self, *_):
        """Accept given parameters.

        Args:
            *_: unused event args
        """
        self.status_msg = ""
        sbh = StatusBarHandler(self.statusbar)
        sbh.reporter.report(10)

        try:
            output_dir = self.measurement.get_depth_profile_dir()

            # Get the filepaths of the selected items
            used_cuts = self.used_cuts
            DepthProfileDialog.checked_cuts[self.measurement.name] = set(
                used_cuts)

            elements = [Element.from_cutfile_string(fp.name) for fp in used_cuts]

            x_unit = self.x_axis_units

            DepthProfileDialog.x_unit = x_unit
            DepthProfileDialog.line_zero = self.show_zero_line
            DepthProfileDialog.line_scale = self.show_scale_line
            DepthProfileDialog.systerr = self.systematic_error
            DepthProfileDialog.used_eff = self.show_used_eff

            DepthProfileDialog.eff_files_str = self.eff_files_str

            sbh.reporter.report(20)

            # If items are selected, proceed to generating the depth profile
            if used_cuts:
                self.status_msg = "Please wait. Creating depth profile."
                if self.parent.depth_profile_widget:
                    self.parent.del_widget(self.parent.depth_profile_widget)

                # If reference density changed, update value to measurement
                if x_unit == DepthProfileUnit.NM:
                    _, _, _, profile, measurement = \
                        self.measurement.get_used_settings()
                    if profile.reference_density != self.reference_density:
                        profile.reference_density = self.reference_density
                        measurement.to_file()

                self.parent.depth_profile_widget = DepthProfileWidget(
                    self.parent, output_dir, used_cuts, elements, x_unit,
                    DepthProfileDialog.line_zero, DepthProfileDialog.used_eff,
                    DepthProfileDialog.line_scale, DepthProfileDialog.systerr,
                    DepthProfileDialog.eff_files_str,
                    progress=sbh.reporter.get_sub_reporter(
                        lambda x: 30 + 0.6 * x
                    ))

                sbh.reporter.report(90)

                icon = self.parent.icon_manager.get_icon(
                    "depth_profile_icon_2_16.png")
                self.parent.add_widget(
                    self.parent.depth_profile_widget, icon=icon)
                self.close()
            else:
                self.status_msg = "Please select .cut file[s] to create " \
                                  "depth profiles."
        except Exception as e:
            error_log = f"Exception occurred when trying to create depth " \
                        f"profiles: {e}"
            self.measurement.log_error(error_log)
        finally:
            sbh.reporter.report(100)

    def _show_reference_density(self):
        """
        Add a filed for modifying the reference density.
        """
        self.label_reference_density.setVisible(True)
        self.sbox_reference_density.setVisible(True)

    def _hide_reference_density(self):
        """
        Remove reference density form dialog if it is there.
        """
        self.label_reference_density.setVisible(False)
        self.sbox_reference_density.setVisible(False)

    def _show_efficiency_files(self):
        """Update efficiency files to UI which are used.
        """
        detector, *_ = self.measurement.get_used_settings()
        self.used_efficiency_files = df.get_efficiency_text_tree(
            self.treeWidget, detector)

    def _show_measurement_settings(self):
        """Show some important setting values in the depth profile parameter
        dialog for the user.
        """
        detector, _, _, profile, _ = self.measurement.get_used_settings()

        self.tof_slope = detector.tof_slope
        self.tof_offset = detector.tof_offset
        self.depth_stop = profile.depth_step_for_stopping
        self.depth_steps = profile.number_of_depth_steps
        self.depth_bin = profile.depth_step_for_output
        self.depth_scale = f"{profile.depth_for_concentration_from} - " \
                           f"{profile.depth_for_concentration_to}"
        self.reference_density = profile.reference_density


class DepthProfileWidget(QtWidgets.QWidget):
    """Depth Profile widget which is added to measurement tab.
    """
    save_file = "widget_depth_profile.save"

    def __init__(self, parent: BaseTab, output_dir: Path, cut_files: List[Path],
                 elements: List[Element], x_units: DepthProfileUnit,
                 line_zero: bool, used_eff: bool, line_scale: bool,
                 systematic_error: float,
                 eff_files_str: Optional[str],
                 progress: Optional[ProgressReporter] = None):
        """Inits widget.

        Args:
            parent: a MeasurementTabWidget.
            output_dir: full path to depth file location
            cut_files: A list of Cut files.
            elements: A list of Element objects that are used in depth profile.
            x_units: Units to be used for x-axis of depth profile.
            line_zero: A boolean representing if vertical line is drawn at zero.
            used_eff: A boolean representing if used eff files are shown.
            line_scale: A boolean representing if horizontal line is drawn at 
                        the defined depth scale.
            systematic_error: A double representing systematic error.
        """
        try:
            super().__init__()
            uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile.ui", self)

            self.parent = parent
            self.measurement: Measurement = parent.obj
            self.output_dir = output_dir
            self.elements = elements
            self.x_units = x_units
            self.use_cuts = cut_files
            self._line_zero_shown = line_zero
            self._eff_files_shown = used_eff
            self._eff_files_str = eff_files_str
            self._line_scale_shown = line_scale
            self._systematic_error = systematic_error

            if progress is not None:
                sub_progress = progress.get_sub_reporter(lambda x: 0.5 * x)
            else:
                sub_progress = None

            detector, _, _, profile, _ = self.measurement.get_used_settings()
            if self._eff_files_str is None:
                cuts = self.measurement.get_cut_files()[0]  # Ignore element losses
                self._eff_files_str = df.get_efficiency_text_cuts(cuts, detector)

            used_eff_files = depth_files.generate_depth_files(
                self.use_cuts, self.output_dir, self.measurement,
                progress=sub_progress
                )
            if progress is not None:
                progress.report(50)

            # Check for RBS selections.
            rbs_list = cut_file.get_rbs_selections(self.use_cuts)

            if self._line_scale_shown:
                depth_scale = (
                    profile.depth_for_concentration_from,
                    profile.depth_for_concentration_to
                )
            else:
                depth_scale = None

            if progress is not None:
                sub_progress = progress.get_sub_reporter(
                    lambda x: 50 + 0.5 * x)
            else:
                sub_progress = None

            self.matplotlib = MatplotlibDepthProfileWidget(
                self, self.output_dir, self.elements, rbs_list,
                icon_manager=self.parent.icon_manager,
                selection_colors=self.measurement.selector.get_colors(),
                depth_scale=depth_scale, x_units=self.x_units,
                add_line_zero=self._line_zero_shown,
                show_eff_files=self._eff_files_shown,
                used_eff_files=used_eff_files,
                systematic_error=self._systematic_error, progress=sub_progress)
        except Exception as e:
            msg = f"Could not create a depth profile: {e}"
            self.measurement.log_error(msg)
            QMessageBox.critical(self, "Error", msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
        finally:
            if progress is not None:
                progress.report(100)

    def delete(self):
        """Delete variables and do clean up.
        """
        self.matplotlib.delete()
        self.matplotlib = None
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget.
        """
        self.parent.depth_profile_widget = None
        file = Path(self.measurement.directory, self.save_file)
        try:
            file.unlink()
        except OSError:
            pass
        super().closeEvent(evnt)

    def save_to_file(self):
        """Save object information to file.
        """
        output_dir = Path.relative_to(
            self.output_dir, self.measurement.directory)

        file = Path(self.measurement.get_depth_profile_dir(), self.save_file)

        with file.open("w") as fh:
            fh.write("{0}\n".format(str(output_dir)))
            fh.write("{0}\n".format("\t".join([
                str(element) for element in self.elements])))
            fh.write("{0}\n".format("\t".join([
                str(cut) for cut in self.use_cuts])))
            fh.write("{0}\n".format(self.x_units.simple_str()))
            fh.write("{0}\n".format(self._line_zero_shown))
            fh.write("{0}\n".format(self._line_scale_shown))
            fh.write("{0}".format(self._systematic_error))

    def update_use_cuts(self):
        """
        Update used cuts list with new Measurement cuts.
        """
        changes_dir = self.measurement.get_changes_dir()
        df.update_cuts(
            self.use_cuts, self.measurement.get_cuts_dir(), changes_dir)

        self.output_dir = self.measurement.get_depth_profile_dir()
