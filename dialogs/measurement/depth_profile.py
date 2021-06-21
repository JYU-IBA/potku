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

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import widgets.binding as bnd
import modules.depth_files as depth_files
import modules.cut_file as cut_file

from pathlib import Path
from typing import List
from typing import Optional

from widgets.gui_utils import StatusBarHandler
from widgets.base_tab import BaseTab
from modules.element import Element
from modules.measurement import Measurement
from modules.global_settings import GlobalSettings
from modules.observing import ProgressReporter
from modules.enums import DepthProfileUnit

from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale

from widgets.matplotlib.measurement.depth_profile import \
    MatplotlibDepthProfileWidget


class DepthProfileDialog(QtWidgets.QDialog):
    """
    Dialog for making a depth profile.
    """
    # TODO replace these global variables with PropertySavingWidget
    checked_cuts = {}
    x_unit = DepthProfileUnit.ATOMS_PER_SQUARE_CM
    line_zero = False
    line_scale = False
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

    systematic_error = bnd.bind("spin_systerr")
    show_scale_line = bnd.bind("check_scaleline")
    show_zero_line = bnd.bind("check_0line")
    reference_density = bnd.bind("sbox_reference_density")
    x_axis_units = bnd.bind("group_x_axis_units")
    
    def __init__(self, parent: BaseTab, measurement: Measurement,
                 global_settings: GlobalSettings, statusbar:
                 Optional[QtWidgets.QStatusBar] = None):
        """Inits depth profile dialog.
        
        Args:
            parent: a MeasurementTabWidget.
            measurement: a Measurement object
            global_settings: a GlobalSettings object
            statusbar: a QStatusBar object
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_depth_profile_params.ui", self)

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
        self.show_scale_line = DepthProfileDialog.line_scale
        self.show_zero_line = DepthProfileDialog.line_zero

        self.cross_sections = global_settings.get_cross_sections()

        self._show_measurement_settings()
        self._show_efficiency_files()
        self.exec_()

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
            # TODO could take care of RBS selection here
            elements = [
                Element.from_string(fp.name.split(".")[1])
                for fp in used_cuts
            ]

            x_unit = self.x_axis_units

            DepthProfileDialog.x_unit = x_unit
            DepthProfileDialog.line_zero = self.show_zero_line
            DepthProfileDialog.line_scale = self.show_scale_line
            DepthProfileDialog.systerr = self.systematic_error

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
                    DepthProfileDialog.line_zero, DepthProfileDialog.line_scale,
                    DepthProfileDialog.systerr,
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
        self.used_efficiency_files = df.get_efficiency_text(
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
                 line_zero: bool, line_scale: bool, systematic_error: float,
                 progress: Optional[ProgressReporter] = None):
        """Inits widget.
        
        Args:
            parent: a MeasurementTabWidget.
            output_dir: full path to depth file location
            cut_files: A list of Cut files.
            elements: A list of Element objects that are used in depth profile.
            x_units: Units to be used for x-axis of depth profile.
            line_zero: A boolean representing if vertical line is drawn at zero.
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
            self._line_scale_shown = line_scale
            self._systematic_error = systematic_error

            if progress is not None:
                sub_progress = progress.get_sub_reporter(lambda x: 0.5 * x)
            else:
                sub_progress = None

            depth_files.generate_depth_files(
                self.use_cuts, self.output_dir, self.measurement,
                progress=sub_progress
            )

            if progress is not None:
                progress.report(50)
            
            # Check for RBS selections.
            rbs_list = cut_file.get_rbs_selections(self.use_cuts)

            for rbs in rbs_list:
                # Search and replace instances of Beam element with scatter
                # elements.
                # When loading request, the scatter element is already
                # replaced. This is essentially done only when creating
                # a new Depth Profile graph.
                # TODO seems overly complicated. This stuff should be sorted
                #  before initializing the widget
                element = Element.from_string(rbs.split(".")[0])
                for i, elem in enumerate(elements):
                    if elem == element:
                        elements[i] = rbs_list[rbs]

            if self._line_scale_shown:
                _, _, _, profile, _ = self.measurement.get_used_settings()
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
                systematic_error=self._systematic_error, progress=sub_progress)
        except Exception as e:
            msg = f"Could not create Depth Profile graph: {e}"
            self.measurement.log_error(msg)
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
            fh.write("{0}\n".format(self.x_units))
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
