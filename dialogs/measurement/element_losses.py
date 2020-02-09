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
import sys

from pathlib import Path

from modules.cut_file import get_scatter_element
from modules.cut_file import is_rbs
from modules.element_losses import ElementLosses

from PyQt5 import QtCore
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

    def __init__(self, parent):
        """Inits element losses class.
        
         Args:
            parent: A MeasurementTabWidget.
        """
        super().__init__()
        self.parent = parent
        self.cuts = []
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_element_losses_params.ui"), self)

        self.ui.OKButton.clicked.connect(self.__accept_params)
        self.ui.cancelButton.clicked.connect(self.close)
        # self.ui.referenceCut.currentIndexChanged.connect(self.__load_targets)

        # TODO: Reads cut files twice. Requires Refactor.
        m_name = self.parent.obj.name
        if m_name not in ElementLossesDialog.reference_cut.keys():
            ElementLossesDialog.reference_cut[m_name] = None
        cuts, unused_elemloss = parent.obj.get_cut_files()
        dirtyinteger = 0
        for cut in cuts:
            if ".potku" in cut:
                cut = os.path.basename()
            self.cuts.append(cut)
            self.ui.referenceCut.addItem(cut)
            if cut == ElementLossesDialog.reference_cut[m_name]:
                self.ui.referenceCut.setCurrentIndex(dirtyinteger)
            dirtyinteger += 1

        if m_name not in ElementLossesDialog.checked_cuts.keys():
            ElementLossesDialog.checked_cuts[m_name] = []
        parent.obj.fill_cuts_treewidget(
            self.ui.targetCutTree,
            True,
            ElementLossesDialog.checked_cuts[m_name])

        self.ui.partitionCount.setValue(ElementLossesDialog.split_count)
        self.ui.radioButton_0max.setChecked(ElementLossesDialog.y_scale == 0)
        self.ui.radioButton_minmax.setChecked(ElementLossesDialog.y_scale == 1)

        self.exec_()

    def __accept_params(self):
        """Called when OK button is pressed. Creates a elementlosses widget and
        adds it to the parent (mdiArea).
        """
        cut_dir = self.parent.obj.directory_cuts
        cut_elo = os.path.join(self.parent.obj.directory_composition_changes,
                               "Changes")
        y_axis_0_scale = self.ui.radioButton_0max.isChecked()
        reference_cut = os.path.join(cut_dir,
                                     self.ui.referenceCut.currentText())
        split_count = self.ui.partitionCount.value()
        checked_cuts = []
        root = self.ui.targetCutTree.invisibleRootItem()
        root_child_count = root.childCount()
        m_name = self.parent.obj.name
        ElementLossesDialog.checked_cuts[m_name].clear()
        for i in range(root_child_count):
            item = root.child(i)
            if item.checkState(0):
                checked_cuts.append(os.path.join(cut_dir, item.file_name))
                ElementLossesDialog.checked_cuts[m_name].append(item.file_name)
            child_count = item.childCount()
            if child_count > 0:  # Elemental Losses
                for j in range(child_count):
                    item_child = item.child(j)
                    if item_child.checkState(0):
                        checked_cuts.append(os.path.join(cut_elo,
                                                         item_child.file_name))
                        ElementLossesDialog.checked_cuts[m_name].append(
                            item_child.file_name)
        if y_axis_0_scale:
            y_scale = 0
        else:
            y_scale = 1

        ElementLossesDialog.reference_cut[m_name] = \
            self.ui.referenceCut.currentText()
        ElementLossesDialog.split_count = split_count
        ElementLossesDialog.y_scale = y_scale

        if checked_cuts:
            if self.parent.elemental_losses_widget:
                self.parent.del_widget(self.parent.elemental_losses_widget)

            self.parent.elemental_losses_widget = ElementLossesWidget(
                self.parent,
                reference_cut,
                checked_cuts,
                split_count,
                y_scale)
            icon = self.parent.icon_manager \
                .get_icon("elemental_losses_icon_16.png")
            self.parent.add_widget(self.parent.elemental_losses_widget,
                                   icon=icon)

            measurement_name = self.parent.obj.name
            msg = "Created Element Losses. Splits: {0} {1} {2}" \
                .format(split_count,
                        "Reference cut: {0}".format(reference_cut),
                        "List of cuts: {0}".format(checked_cuts))
            logging.getLogger(measurement_name).info(msg)

            log_info = "Elemental Losses split counts:\n"

            split_counts = self.parent.elemental_losses_widget.split_counts
            splitinfo = "\n".join(["{0}: {1}".format(key,
                                                     ", ".join(str(v) for v in
                                                               split_counts[
                                                                   key]))
                                   for key in split_counts.keys()])
            logging.getLogger(measurement_name).info(log_info + splitinfo)
            self.close()


class ElementLossesWidget(QtWidgets.QWidget):
    """Element losses widget which is added to measurement tab.
    """
    save_file = "widget_composition_changes.save"

    def __init__(self, parent, reference_cut_file, checked_cuts,
                 partition_count, y_scale, use_progress_bar=True,
                 ignore_ref_cut=None):
        """Inits widget.
        
        Args:
            parent: A MeasurementTabWidget.
            reference_cut_file: String representing reference cut file.
            checked_cuts: String list representing cut files.
            partition_count: Integer representing how many splits cut files 
                             are divided to.
            y_scale: Integer flag representing how Y axis is scaled.
            use_progress_bar: Whether to add a progress bar or not.
        """
        try:
            super().__init__()
            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.measurement = self.parent.obj
            self.reference_cut_file = reference_cut_file
            self.checked_cuts = checked_cuts
            self.partition_count = partition_count
            self.y_scale = y_scale
            if self.measurement.statusbar:
                if use_progress_bar:
                    self.progress_bar = QtWidgets.QProgressBar()
                    self.measurement.statusbar.addWidget(self.progress_bar, 1)
                    self.progress_bar.show()
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)
                    # Mac requires event processing to show progress bar and its
                    # process.
                else:
                    self.progress_bar = None
            else:
                self.progress_bar = None

            self.ui = uic.loadUi(os.path.join("ui_files",
                                              "ui_element_losses.ui"),
                                 self)
            title = "{0} - Reference cut: {1}".format(
                self.ui.windowTitle(),
                os.path.basename(self.reference_cut_file))
            self.ui.setWindowTitle(title)
            # Calculate elemental losses
            self.losses = ElementLosses(self.measurement.directory_cuts,
                                        self.measurement.
                                        directory_composition_changes,
                                        self.reference_cut_file,
                                        self.checked_cuts,
                                        self.partition_count,
                                        progress_bar=self.progress_bar)
            self.split_counts = self.losses.count_element_cuts()

            # Check for RBS selections.
            rbs_list = {}
            for cut in self.checked_cuts:
                filename = os.path.basename(cut)
                split = filename.split(".")
                if is_rbs(cut):
                    # This should work for regular cut and split.
                    key = "{0}.{1}.{2}.{3}".format(split[1], split[2],
                                                   split[3], split[4])
                    rbs_list[key] = get_scatter_element(cut)

            # Connect buttons
            self.ui.splitSaveButton.clicked.connect(self.__save_splits)

            self.matplotlib = MatplotlibElementLossesWidget(
                self, self.split_counts, legend=True, y_scale=y_scale,
                rbs_list=rbs_list, reference_cut_file=reference_cut_file)
        except:
            import traceback
            msg = "Could not create Elemental Losses graph. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[
                                     0].__name__ + ": " + traceback._some_str(
                sys.exc_info()[1]), err_file,
                                 str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.measurement.name).error(msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()
        finally:
            if self.progress_bar:
                self.measurement.statusbar.removeWidget(self.progress_bar)
                self.progress_bar.hide()

    def delete(self):
        """Delete variables and do clean up.
        """
        self.losses = None
        self.progress_bar = None
        self.matplotlib.delete()
        self.matplotlib = None
        self.ui.close()
        self.ui = None
        self.close()

    def __save_splits(self):
        if self.progress_bar:
            self.progress_bar = QtWidgets.QProgressBar()
            self.measurement.statusbar.addWidget(self.progress_bar, 1)
            self.progress_bar.show()
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.
        else:
            self.progress_bar = None
        self.losses.progress_bar = self.progress_bar  # Update this     
        self.losses.save_splits()
        if self.progress_bar:
            self.measurement.statusbar.removeWidget(self.progress_bar)
            self.progress_bar.hide()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget.
        """
        self.parent.elemental_losses_widget = None
        file = os.path.join(self.parent.obj.directory, self.save_file)
        try:
            if os.path.isfile(file):
                os.unlink(file)
        except:
            pass
        super().closeEvent(evnt)

    def update_cuts(self):
        """
        Update checked cuts and reference cut with Measurement cuts.
        """
        for file in os.listdir(self.parent.obj.directory_cuts):
            for i in range(len(self.checked_cuts)):
                cut = self.checked_cuts[i]
                cut_split = cut.split('.')  # There is one dot more (.potku)
                file_split = file.split('.')
                if cut_split[2] == file_split[1] and cut_split[3] == \
                        file_split[2] and cut_split[4] == file_split[3]:
                    cut_file = os.path.join(self.parent.obj.directory_cuts,
                                            file)
                    self.checked_cuts[i] = cut_file

        changes_dir = os.path.join(
            self.parent.obj.directory_composition_changes, "Changes")
        if os.path.exists(changes_dir):
            for file in os.listdir(changes_dir):
                for i in range(len(self.checked_cuts)):
                    cut = self.checked_cuts[i]
                    cut_split = cut.split('.')  # There is one dot more (.potku)
                    file_split = file.split('.')
                    if cut_split[2] == file_split[1] and cut_split[3] == \
                            file_split[2] and cut_split[4] == file_split[3]:
                        cut_file = os.path.join(changes_dir, file)
                        self.checked_cuts[i] = cut_file

        self.losses.checked_cuts = self.checked_cuts

        # Update reference cut
        reference_split = self.reference_cut_file.split('.')
        new_reference = self.parent.obj.name
        i = 2
        while i in range(len(reference_split)):
            new_reference = new_reference + "." + reference_split[i]
            i += 1
        self.reference_cut_file = os.path.join(
            self.parent.obj.directory_cuts, new_reference)
        self.losses.reference_cut_file = self.reference_cut_file

        self.losses.directory_composition_changes = changes_dir

        # Update title
        title = "{0} - Reference cut: {1}".format(
            "Composition changes",
            os.path.basename(self.reference_cut_file))
        self.ui.setWindowTitle(title)

    def save_to_file(self):
        """Save object information to file.
        """
        reference = os.path.relpath(self.reference_cut_file,
                                    self.parent.obj.directory)

        files = "\t".join([os.path.relpath(tmp, self.parent.obj.directory)
                           for tmp in self.checked_cuts])

        file = os.path.join(self.parent.obj.directory_composition_changes,
                            self.save_file)

        with open(file, "wt") as fh:
            fh.write("{0}\n".format(reference))
            fh.write("{0}\n".format(files))
            fh.write("{0}\n".format(self.partition_count))
            fh.write("{0}".format(self.y_scale))
