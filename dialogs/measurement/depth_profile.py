# coding=utf-8
"""
Created on 5.4.2013
Updated on 9.4.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging
import os
import sys
from PyQt5 import uic, QtCore, QtWidgets

from modules.cut_file import is_rbs, get_scatter_element
from modules.depth_files import DepthFiles
from modules.element import Element
from modules.null import Null
from widgets.matplotlib.measurement.depth_profile import MatplotlibDepthProfileWidget


class DepthProfileDialog(QtWidgets.QDialog):
    checked_cuts = {}
    x_unit = "1e15 at./cm²"
    line_zero = False
    line_scale = False
    systerr = 0.0
    
    def __init__(self, parent):
        """Inits depth profile dialog
        
        Args:
            parent: MeasurementTabWidget
        """
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_depth_profile_params.ui"), self)
        self.measurement = parent.measurement
        self.__statusbar = parent.measurement.statusbar
        self.__global_settings = self.measurement.request.global_settings
        
        # Connect buttons
        self.ui.OKButton.clicked.connect(self.__accept_params)
        self.ui.cancelButton.clicked.connect(self.close)

        m_name = self.parent.measurement.measurement_name
        if not m_name in DepthProfileDialog.checked_cuts.keys():
            DepthProfileDialog.checked_cuts[m_name] = []
        self.measurement.fill_cuts_treewidget(
            self.ui.treeWidget,
            True,
            DepthProfileDialog.checked_cuts[m_name])
        
        x_unit = DepthProfileDialog.x_unit
        radio_buttons = self.findChildren(QtWidgets.QRadioButton)
        for radio_button in radio_buttons:
            radio_button.setChecked(radio_button.text() == x_unit)
        
        self.ui.check_0line.setChecked(DepthProfileDialog.line_zero)
        self.ui.check_scaleline.setChecked(DepthProfileDialog.line_scale)
        
        str_cross = self.__global_settings.get_cross_sections_text()
        self.ui.label_cross.setText(str_cross)
        self.ui.spin_systerr.setValue(DepthProfileDialog.systerr)
        
        if not hasattr(self.measurement, "measurement_settings"):
            QtWidgets.QMessageBox.question(self, "Warning",
                                           "Settings have not been set. Please set settings before continuing.",
                                           QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
        else:
            if not self.measurement.measurement_settings.has_been_set():
                reply = QtWidgets.QMessageBox.question(self, "Warning",
                                                       "Not all settings have been set. Do you want to continue?",
                                                       QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                       QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.No:
                    self.close()
                    return
            self.__update_eff_files()
            self.__show_important_settings()
            self.exec_()
        
    def __accept_params(self):
        """Accept given parameters
        """
        progress_bar = QtWidgets.QProgressBar()
        self.__statusbar.addWidget(progress_bar, 1) 
        progress_bar.show() 
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
        try:
            use_cut = []
            output_dir = self.measurement.directory_depth_profiles
            elements = []
                
            progress_bar.setValue(10)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its process.
            
            # Get the filepaths of the selected items
            root = self.ui.treeWidget.invisibleRootItem()
            child_count = root.childCount()
            m_name = self.parent.measurement.measurement_name
            DepthProfileDialog.checked_cuts[m_name].clear()
            for i in range(child_count): 
                item = root.child(i)
                if item.checkState(0):
                    use_cut.append(os.path.join(item.directory, item.file_name))
                    element = Element(item.file_name.split(".")[1])
                    elements.append(element)
                    DepthProfileDialog.checked_cuts[m_name].append(item.file_name)
                child_count_2 = item.childCount()
                if child_count_2 > 0:  # Elemental Losses
                    for j in range(child_count_2):
                        item_child = item.child(j)
                        if item_child.checkState(0):
                            name = item_child.file_name
                            dir_e = self.parent.measurement.directory_elemloss
                            use_cut.append(os.path.join(dir_e, name))
                            element = Element(item_child.file_name.split(".")[1])
                            elements.append(element)
                            DepthProfileDialog.checked_cuts[m_name].append(
                                                            item_child.file_name)
            progress_bar.setValue(20)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its process.
            
            # Get the x-axis unit to be used from the radio buttons
            x_unit = DepthProfileDialog.x_unit
            radio_buttons = self.findChildren(QtWidgets.QRadioButton)
            for radio_button in radio_buttons:
                if radio_button.isChecked():
                    x_unit = radio_button.text()
            DepthProfileDialog.x_unit = x_unit
            progress_bar.setValue(30)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its process.
            
            DepthProfileDialog.line_zero = self.ui.check_0line.isChecked()
            DepthProfileDialog.line_scale = self.ui.check_scaleline.isChecked() 
            DepthProfileDialog.systerr = self.ui.spin_systerr.value()
            
            # If items are selected, proceed to generating the depth profile
            if use_cut:
                self.ui.label_status.setText("Please wait. Creating depth profile.")
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
                if self.parent.depth_profile_widget:
                    self.parent.del_widget(self.parent.depth_profile_widget)
                
                self.parent.depth_profile_widget = DepthProfileWidget(self.parent,
                                                                      output_dir,
                                                                      use_cut,
                                                                      elements,
                                                                      x_unit,
                                                                      DepthProfileDialog.line_zero,
                                                                      DepthProfileDialog.line_scale,
                                                                      DepthProfileDialog.systerr)
                progress_bar.setValue(90)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
                # Mac requires event processing to show progress bar and its 
                # process.
                
                icon = self.parent.icon_manager.get_icon(
                                                     "depth_profile_icon_2_16.png")
                self.parent.add_widget(self.parent.depth_profile_widget, icon=icon)
                self.close()
            else:
                print("No cuts have been selected for depth profile.")
        except Exception as e:
            error_log = "Unexpected error: {0}".format(e)
            logging.getLogger(self.measurement.measurement_name).error(error_log)
        finally:
            self.__statusbar.removeWidget(progress_bar)
            progress_bar.hide()

    def __update_eff_files(self):
        """Update efficiency files to UI which are used.
        """
        # This is probably not the most effective way, or practical for 
        # that matter, to get all efficiency files from directory defined
        # in global settings that match the cut files of measurements.
        eff_files = self.__global_settings.get_efficiencies()
        masses = self.measurement.request.masses
        eff_files_used = []
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        for eff in eff_files:
            str_element, unused_ext = eff.split(".")
            element = Element(str_element)
            for i in range(child_count): 
                item = root.child(i)
                # TODO: Perhaps make this update every time a cut file is
                # selected so user knows exactly what files are used instead
                # of what files match all the cut files.
                # if not item.checkState(0): continue
                
                # TODO: Does not check elemental losses for efficiency files.
                if not hasattr(item, "file_name"):
                    continue
                cut_element = Element(item.file_name.split(".")[1])
                mass = cut_element.isotope.mass
                if not mass:
                    mass = round(masses.get_standard_isotope(cut_element.name),
                                 0)
                if cut_element.name == element.name and mass == element.isotope.mass:
                    eff_files_used.append(eff)
        if eff_files_used:
            self.ui.label_efficiency_files.setText(
               "Efficiency files used: \t\n{0}".format("\t\n".join(eff_files_used)))
        else:
            self.ui.label_efficiency_files.setText("No efficiency files.")

    def __show_important_settings(self):
        """Show some important setting values in the depth profile parameter
        dialog for the user.
        """
        settings = self.measurement.measurement_settings.get_measurement_settings()
        cs = settings.calibration_settings
        dps = settings.depth_profile_settings
        self.ui.label_calibslope.setText(str(cs.slope))
        self.ui.label_caliboffset.setText(str(cs.offset))
        self.ui.label_depthstop.setText(str(dps.depth_step_for_stopping))
        self.ui.label_depthnumber.setText(str(dps.number_of_depth_steps))
        self.ui.label_depthbin.setText(str(dps.depth_step_for_output))
        self.ui.label_depthscale.setText("{0} - {1}".format(
            dps.depths_for_concentration_from,
            dps.depths_for_concentration_to))
        

class DepthProfileWidget(QtWidgets.QWidget):
    """Depth Profile widget which is added to measurement tab.
    """
    save_file = "widget_depth_profile.save"
    
    def __init__(self, parent, output_dir, use_cuts, elements, x_units,
                 line_zero, line_scale, systematic_error):
        """Inits widget.
        
        Args:
            parent: A MeasurementTabWidget.
            output_dir: A string representing directory in which the depth files 
                        are located.
            use_cuts: A string list representing Cut files.
            elements: A list of Element objects that are used in depth profile.
            x_units: Units to be used for x-axis of depth profile.
            line_zero: A boolean representing if vertical line is drawn at zero.
            line_scale: A boolean representing if horizontal line is drawn at 
                        the defined depth scale.
            systematic_error: A double representing systematic error.
        """
        try:
            super().__init__()
            self.parent = parent
            self.icon_manager = parent.icon_manager
            self.measurement = parent.measurement
            self.output_dir = output_dir
            self.elements = elements
            self.x_units = x_units
            self.__use_cuts = use_cuts;
            self.__line_zero = line_zero
            self.__line_scale = line_scale
            self.__systerr = systematic_error
            self.ui = uic.loadUi(os.path.join("ui_files",
                                              "ui_depth_profile.ui"),
                                 self)
            
            # Make the directory for depth files
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            output_files = os.path.join(self.output_dir, "depth")
            dp = DepthFiles(self.__use_cuts, output_files)
            self.measurement.generate_tof_in()  # This has to be before create_depth_files()
            dp.create_depth_files()
            
            # Check for RBS selections.
            rbs_list = {}
            for cut in self.__use_cuts:
                filename = os.path.basename(cut)
                split = filename.split(".")
                element = Element(split[1])
                if is_rbs(cut):
                    # This should work for regular cut and split.
                    key = "{0}.{1}.{2}".format(split[1], split[2], split[3])
                    scatter_element = get_scatter_element(cut)
                    rbs_list[key] = scatter_element
                    index = 0
                    found_scatter = False
                    for elm in elements:  # Makeshift
                        if elm == element:
                            found_scatter = True
                            break
                        index += 1
                    # When loading request, the scatter element is already
                    # replaced. This is essentially done only when creating 
                    # a new Depth Profile graph.
                    if found_scatter:
                        elements[index] = scatter_element
            
            settings = self.measurement.measurement_settings.get_measurement_settings()
            ds = settings.depth_profile_settings
            depth_scale_from = ds.depths_for_concentration_from
            depth_scale_to = ds.depths_for_concentration_to
            self.matplotlib = MatplotlibDepthProfileWidget(self,
                                                           self.output_dir,
                                                           self.elements,
                                                           rbs_list,
                                                           (depth_scale_from, depth_scale_to),
                                                           self.x_units,
                                                           True,  # legend
                                                           self.__line_zero,
                                                           self.__line_scale,
                                                           self.__systerr)
        except:
            import traceback
            msg = "Could not create Depth Profile graph. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[0].__name__ + ": " + traceback._some_str(sys.exc_info()[1]), err_file,
                                 str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.measurement.measurement_name).error(msg)
            if hasattr(self, "matplotlib"):
                self.matplotlib.delete()

    def delete(self):
        """Delete variables and do clean up.
        """
        self.matplotlib.delete()
        self.matplotlib = None
        self.ui.close()
        self.ui = None
        self.close()

    def closeEvent(self, evnt):
        """Reimplemented method when closing widget.
        """
        self.parent.depth_profile_widget = Null()
        file = os.path.join(self.parent.measurement.directory, self.save_file)
        try:
            if os.path.isfile(file):
                os.unlink(file)
        except:
            pass
        super().closeEvent(evnt)

    def save_to_file(self):
        """Save object information to file.
        """
        output_dir = self.output_dir.replace(
                         self.parent.measurement.directory + "\\", "")
        file = os.path.join(self.parent.measurement.directory_depth_profiles, self.save_file)
        fh = open(file, "wt")
        fh.write("{0}\n".format(output_dir))
        fh.write("{0}\n".format("\t".join([str(element)
                                           for element in self.elements])))
        fh.write("{0}\n".format("\t".join([cut for cut in self.__use_cuts])))
        fh.write("{0}\n".format(self.x_units))
        fh.write("{0}\n".format(self.__line_zero))
        fh.write("{0}\n".format(self.__line_scale))
        fh.write("{0}".format(self.__systerr))
        fh.close()
