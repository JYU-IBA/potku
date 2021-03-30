# coding=utf-8
"""
Created on 27.3.2013
Updated on 18.12.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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
             "Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n Samuel " \
             "Kaiponen \n Heta Rekilä \n Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import os

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import widgets.binding as bnd
import modules.cut_file as cut_file

from typing import Optional
from typing import List

from pathlib import Path

from widgets.gui_utils import StatusBarHandler

from modules.element_losses import ElementLosses
from modules.measurement import Measurement

from PyQt5 import QtWidgets
from PyQt5 import uic

from widgets.matplotlib.measurement.element_losses \
    import MatplotlibElementLossesWidget


class ElementLossesDialog(QtWidgets.QDialog):
    """Class to handle element losses dialogs.
    """
    checked_cuts = {}
    reference_cut = {}
    split_count = 10
    y_scale = 1

    status_msg = bnd.bind("label_status")
    used_reference_cut = bnd.bind("referenceCut")
    used_cuts = bnd.bind("targetCutTree")

    def __init__(self, parent, measurement: Measurement, statusbar:
                 Optional[QtWidgets.QStatusBar] = None):
        """Inits element losses class.
        
         Args:
            parent: A MeasurementTabWidget.
            
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_element_losses_params.ui", self)
        self.parent = parent
        self.measurement = measurement
        self.statusbar = statusbar
        self.cuts = []

        self.OKButton.clicked.connect(self.__accept_params)
        self.cancelButton.clicked.connect(self.close)
        # self.referenceCut.currentIndexChanged.connect(self.__load_targets)

        # TODO: Reads cut files twice. Requires Refactor.
        # Reference cuts
        m_name = self.measurement.name
        if m_name not in ElementLossesDialog.reference_cut:
            ElementLossesDialog.reference_cut[m_name] = None
        cuts, _ = self.measurement.get_cut_files()
        gutils.fill_combobox(
            self.referenceCut, cuts, text_func=lambda fp: fp.name)
        self.used_reference_cut = ElementLossesDialog.reference_cut[m_name]

        # Cuts and element losses
        if m_name not in ElementLossesDialog.checked_cuts:
            ElementLossesDialog.checked_cuts[m_name] = set()
        gutils.fill_cuts_treewidget(
            self.measurement, self.targetCutTree.invisibleRootItem(),
            use_elemloss=True)
        self.used_cuts = ElementLossesDialog.checked_cuts[m_name]

        self.partitionCount.setValue(ElementLossesDialog.split_count)
        self.radioButton_0max.setChecked(ElementLossesDialog.y_scale == 0)
        self.radioButton_minmax.setChecked(ElementLossesDialog.y_scale == 1)

        self.exec_()

    @gutils.disable_widget
    def __accept_params(self, *_):
        """Called when OK button is pressed. Creates a elementlosses widget and
        adds it to the parent (mdiArea).

        Args:
            *_: unused event args
        """
        self.status_msg = ""
        sbh = StatusBarHandler(self.statusbar)

        y_axis_0_scale = self.radioButton_0max.isChecked()
        reference_cut = self.used_reference_cut
        split_count = self.partitionCount.value()
        m_name = self.measurement.name
        used_cuts = self.used_cuts
        ElementLossesDialog.checked_cuts[m_name] = set(used_cuts)

        if y_axis_0_scale:
            y_scale = 0
        else:
            y_scale = 1

        ElementLossesDialog.reference_cut[m_name] = \
            self.referenceCut.currentText()
        ElementLossesDialog.split_count = split_count
        ElementLossesDialog.y_scale = y_scale

        sbh.reporter.report(25)

        if used_cuts:
            if self.parent.elemental_losses_widget:
                self.parent.del_widget(self.parent.elemental_losses_widget)

            self.parent.elemental_losses_widget = ElementLossesWidget(
                self.parent, self.measurement, reference_cut, used_cuts,
                split_count, y_scale, statusbar=self.statusbar,
                progress=sbh.reporter.get_sub_reporter(
                    lambda x: 25 + 0.70 * x
                ))
            icon = self.parent.icon_manager \
                .get_icon("elemental_losses_icon_16.png")
            self.parent.add_widget(self.parent.elemental_losses_widget,
                                   icon=icon)

            msg = f"Created Element Losses. Splits: {split_count} " \
                  f"Reference cut: {reference_cut} " \
                  f"List of cuts: {used_cuts}"
            self.measurement.log(msg)

            log_info = "Elemental Losses split counts:\n"

            split_counts = self.parent.elemental_losses_widget.split_counts
            splitinfo = "\n".join(
                ["{0}: {1}".format(
                    key, ", ".join(str(v) for v in split_counts[key]))
                    for key in split_counts])
            self.measurement.log(log_info + splitinfo)

            sbh.reporter.report(100)
            self.close()
        else:
            self.status_msg = "Please select .cut file[s] to create element " \
                              "losses."
        sbh.reporter.report(100)


class ElementLossesWidget(QtWidgets.QWidget):
    """Element losses widget which is added to measurement tab.
    """
    save_file = "widget_composition_changes.save"

    def __init__(self, parent, measurement: Measurement,
                 reference_cut_file: Path, checked_cuts: List[Path],
                 partition_count: int, y_scale: int, statusbar=None,
                 progress=None):
        """Inits widget.
        
        Args:
            parent: A MeasurementTabWidget.
            reference_cut_file: absolute path to cut file.
            checked_cuts: list of absolute paths to cut files.
            partition_count: Integer representing how many splits cut files 
                are divided to.
            y_scale: Integer flag representing how Y axis is scaled.
            progress: a ProgressReporter object
        """
        try:
            super().__init__()
            uic.loadUi(gutils.get_ui_dir() / "ui_element_losses.ui", self)

            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.measurement = measurement
            self.reference_cut_file = reference_cut_file
            self.checked_cuts = checked_cuts
            self.partition_count = partition_count
            self.y_scale = y_scale
            self.statusbar = statusbar

            title = "{0} - Reference cut: {1}".format(
                self.windowTitle(),
                self.reference_cut_file.name)
            self.setWindowTitle(title)

            # Calculate elemental losses
            self.losses = ElementLosses(
                self.measurement.get_cuts_dir(),
                self.measurement.get_composition_changes_dir(),
                self.reference_cut_file,
                self.checked_cuts,
                self.partition_count)

            if progress is not None:
                sub_progress = progress.get_sub_reporter(
                    lambda x: 0.9 * x
                )
            else:
                sub_progress = None

            self.split_counts = self.losses.count_element_cuts(
                progress=sub_progress
            )

            # Check for RBS selections.
            rbs_list = cut_file.get_rbs_selections(self.checked_cuts)
            # Connect buttons
            self.splitSaveButton.clicked.connect(self.__save_splits)

            self.matplotlib = MatplotlibElementLossesWidget(
                self, self.split_counts, legend=True, y_scale=y_scale,
                rbs_list=rbs_list, reference_cut_file=reference_cut_file)
        except Exception as e:
            msg = f"Could not create Elemental Losses graph: {e}"
            self.measurement.log_error(msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
        finally:
            if progress is not None:
                progress.report(100)

    def delete(self):
        """Delete variables and do clean up.
        """
        self.losses = None
        self.matplotlib.delete()
        self.matplotlib = None
        self.close()

    def __save_splits(self):
        sbh = StatusBarHandler(self.statusbar)
        self.losses.save_splits(progress=sbh.reporter.get_sub_reporter(
            lambda x: 0.9 * x
        ))
        sbh.reporter.report(100)

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget.
        """
        self.parent.elemental_losses_widget = None
        file = Path(self.measurement.directory, self.save_file)
        try:
            file.unlink()
        except OSError:
            pass
        super().closeEvent(evnt)

    def update_cuts(self):
        """
        Update checked cuts and reference cut with Measurement cuts.
        """
        changes_dir = self.measurement.get_changes_dir()

        df.update_cuts(
            self.checked_cuts, self.measurement.get_cuts_dir(), changes_dir)

        self.losses.checked_cuts = self.checked_cuts

        # Update reference cut
        _, suffix = self.reference_cut_file.name.split(".", 1)
        self.reference_cut_file = Path(
            self.measurement.get_cuts_dir(),
            f"{self.measurement.name}.{suffix}")
        self.losses.reference_cut_file = self.reference_cut_file

        self.losses.directory_composition_changes = changes_dir

        # Update title
        title = "{0} - Reference cut: {1}".format(
            "Composition changes",
            os.path.basename(self.reference_cut_file))
        self.setWindowTitle(title)

    def save_to_file(self):
        """Save object information to file.
        """
        reference = os.path.relpath(self.reference_cut_file,
                                    self.measurement.directory)

        files = "\t".join([os.path.relpath(tmp, self.measurement.directory)
                           for tmp in self.checked_cuts])

        file = Path(self.measurement.get_composition_changes_dir(),
                    self.save_file)

        with open(file, "wt") as fh:
            fh.write("{0}\n".format(reference))
            fh.write("{0}\n".format(files))
            fh.write("{0}\n".format(self.partition_count))
            fh.write("{0}".format(self.y_scale))
