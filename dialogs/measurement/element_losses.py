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
             "Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n Samuel " \
             "Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging
import os

import dialogs.dialog_functions as df
import widgets.gui_utils as gutils
import modules.cut_file as cut_file

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

    def __init__(self, parent, statusbar=None):
        """Inits element losses class.
        
         Args:
            parent: A MeasurementTabWidget.
        """
        super().__init__()
        uic.loadUi(gutils.get_ui_dir() / "ui_element_losses_params.ui", self)

        self.parent = parent
        self.measurement: Measurement = self.parent.obj
        self.statusbar = statusbar
        self.cuts = []

        self.OKButton.clicked.connect(self.__accept_params)
        self.cancelButton.clicked.connect(self.close)
        # self.referenceCut.currentIndexChanged.connect(self.__load_targets)

        # TODO: Reads cut files twice. Requires Refactor.
        m_name = self.measurement.name
        if m_name not in ElementLossesDialog.reference_cut:
            ElementLossesDialog.reference_cut[m_name] = None
        cuts, unused_elemloss = parent.obj.get_cut_files()
        for i, cut in enumerate(cuts):
            if ".potku" in cut:
                cut = os.path.basename()
            self.cuts.append(cut)
            self.referenceCut.addItem(cut)
            if cut == ElementLossesDialog.reference_cut[m_name]:
                self.referenceCut.setCurrentIndex(i)

        if m_name not in ElementLossesDialog.checked_cuts:
            ElementLossesDialog.checked_cuts[m_name] = []

        gutils.fill_cuts_treewidget(
            parent.obj, self.targetCutTree, True,
            ElementLossesDialog.checked_cuts[m_name])

        self.partitionCount.setValue(ElementLossesDialog.split_count)
        self.radioButton_0max.setChecked(ElementLossesDialog.y_scale == 0)
        self.radioButton_minmax.setChecked(ElementLossesDialog.y_scale == 1)

        self.exec_()

    def __accept_params(self):
        """Called when OK button is pressed. Creates a elementlosses widget and
        adds it to the parent (mdiArea).
        """
        sbh = StatusBarHandler(self.statusbar)

        cut_dir = self.measurement.directory_cuts
        cut_elo = self.measurement.get_changes_dir()
        y_axis_0_scale = self.radioButton_0max.isChecked()
        reference_cut = Path(cut_dir, self.referenceCut.currentText())
        split_count = self.partitionCount.value()
        checked_cuts = []
        root = self.targetCutTree.invisibleRootItem()
        root_child_count = root.childCount()
        m_name = self.measurement.name
        ElementLossesDialog.checked_cuts[m_name].clear()
        for i in range(root_child_count):
            item = root.child(i)
            if item.checkState(0):
                checked_cuts.append(Path(cut_dir, item.file_name))
                ElementLossesDialog.checked_cuts[m_name].append(item.file_name)
            child_count = item.childCount()
            if child_count > 0:  # Elemental Losses
                for j in range(child_count):
                    item_child = item.child(j)
                    if item_child.checkState(0):
                        checked_cuts.append(Path(cut_elo, item_child.file_name))
                        ElementLossesDialog.checked_cuts[m_name].append(
                            item_child.file_name)
        if y_axis_0_scale:
            y_scale = 0
        else:
            y_scale = 1

        ElementLossesDialog.reference_cut[m_name] = \
            self.referenceCut.currentText()
        ElementLossesDialog.split_count = split_count
        ElementLossesDialog.y_scale = y_scale

        sbh.reporter.report(25)

        if checked_cuts:
            if self.parent.elemental_losses_widget:
                self.parent.del_widget(self.parent.elemental_losses_widget)

            self.parent.elemental_losses_widget = ElementLossesWidget(
                self.parent, reference_cut, checked_cuts, split_count,
                y_scale, statusbar=self.statusbar,
                progress=sbh.reporter.get_sub_reporter(
                    lambda x: 25 + 0.70 * x
                ))
            icon = self.parent.icon_manager \
                .get_icon("elemental_losses_icon_16.png")
            self.parent.add_widget(self.parent.elemental_losses_widget,
                                   icon=icon)

            measurement_name = self.measurement.name
            msg = "Created Element Losses. Splits: {0} {1} {2}" \
                .format(split_count,
                        "Reference cut: {0}".format(reference_cut),
                        "List of cuts: {0}".format(checked_cuts))
            logging.getLogger(measurement_name).info(msg)

            log_info = "Elemental Losses split counts:\n"

            split_counts = self.parent.elemental_losses_widget.split_counts
            splitinfo = "\n".join(
                ["{0}: {1}".format(
                    key, ", ".join(str(v) for v in split_counts[key]))
                    for key in split_counts])
            logging.getLogger(measurement_name).info(log_info + splitinfo)

            sbh.reporter.report(100)
            self.close()

        sbh.reporter.report(100)


class ElementLossesWidget(QtWidgets.QWidget):
    """Element losses widget which is added to measurement tab.
    """
    save_file = "widget_composition_changes.save"

    def __init__(self, parent, reference_cut_file, checked_cuts,
                 partition_count, y_scale, statusbar=None, progress=None):
        """Inits widget.
        
        Args:
            parent: A MeasurementTabWidget.
            reference_cut_file: String representing reference cut file.
            checked_cuts: String list representing cut files.
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
            self.measurement: Measurement = self.parent.obj
            self.reference_cut_file = reference_cut_file
            self.checked_cuts = checked_cuts
            self.partition_count = partition_count
            self.y_scale = y_scale
            self.statusbar = statusbar

            title = "{0} - Reference cut: {1}".format(
                self.windowTitle(),
                os.path.basename(self.reference_cut_file))
            self.setWindowTitle(title)

            # Calculate elemental losses
            self.losses = ElementLosses(
                self.measurement.directory_cuts,
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
            logging.getLogger(self.measurement.name).error(msg)
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
            if file.exists():
                os.remove(file)
        except:
            pass
        super().closeEvent(evnt)

    def update_cuts(self):
        """
        Update checked cuts and reference cut with Measurement cuts.
        """
        changes_dir = self.measurement.get_changes_dir()

        df.update_cuts(self.checked_cuts,
                       self.measurement.directory_cuts,
                       changes_dir)

        self.losses.checked_cuts = self.checked_cuts

        # Update reference cut
        _, suffix = self.reference_cut_file.name.split(".", 1)
        self.reference_cut_file = Path(
            self.measurement.directory_cuts,
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
