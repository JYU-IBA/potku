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

import logging
import modules.masses as masses
import os
import sys
import time

from modules.beam import Beam
from modules.cut_file import get_scatter_element
from modules.cut_file import is_rbs
from modules.depth_files import DepthFiles
from modules.detector import Detector
from modules.element import Element
from modules.run import Run
from modules.target import Target

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QLocale

from widgets.matplotlib.measurement.depth_profile import \
    MatplotlibDepthProfileWidget


class DepthProfileDialog(QtWidgets.QDialog):
    """
    Dialog for making a depth profile.
    """
    checked_cuts = {}
    x_unit = "1e15 at./cm²"
    line_zero = False
    line_scale = False
    systerr = 0.0
    
    def __init__(self, parent):
        """Inits depth profile dialog.
        
        Args:
            parent: A MeasurementTabWidget.
        """
        super().__init__()
        self.parent = parent
        self.ui = uic.loadUi(os.path.join("ui_files",
                                          "ui_depth_profile_params.ui"), self)
        self.measurement = parent.obj
        self.__statusbar = parent.obj.statusbar
        self.__global_settings = self.measurement.request.global_settings
        
        # Connect buttons
        self.ui.OKButton.clicked.connect(self.__accept_params)
        self.ui.cancelButton.clicked.connect(self.close)

        self.__reference_density_label = None
        self.__reference_density_spinbox = None

        self.locale = QLocale.c()

        self.ui.spin_systerr.setLocale(self.locale)

        self.ui.radioButtonNm.clicked.connect(self.__add_reference_density)
        self.ui.radioButtonAtPerCm2.clicked.connect(
            self.__remove_reference_density)

        m_name = self.parent.obj.name
        if m_name not in DepthProfileDialog.checked_cuts.keys():
            DepthProfileDialog.checked_cuts[m_name] = []
        self.measurement.fill_cuts_treewidget(
            self.ui.treeWidget,
            True,
            DepthProfileDialog.checked_cuts[m_name])
        
        x_unit = DepthProfileDialog.x_unit
        radio_buttons = self.findChildren(QtWidgets.QRadioButton)
        for radio_button in radio_buttons:
            radio_button.setChecked(radio_button.text() == x_unit)

        if x_unit == "nm":
            self.__add_reference_density()
        
        self.ui.check_0line.setChecked(DepthProfileDialog.line_zero)
        self.ui.check_scaleline.setChecked(DepthProfileDialog.line_scale)
        
        str_cross = self.__global_settings.get_cross_sections_text()
        self.ui.label_cross.setText(str_cross)
        self.ui.spin_systerr.setValue(DepthProfileDialog.systerr)

        self.__show_important_settings()
        self.exec_()
        
    def __accept_params(self):
        """Accept given parameters.
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
            # Mac requires event processing to show progress bar and its
            # process.
            
            # Get the filepaths of the selected items
            root = self.ui.treeWidget.invisibleRootItem()
            child_count = root.childCount()
            m_name = self.parent.obj.name
            DepthProfileDialog.checked_cuts[m_name].clear()
            for i in range(child_count): 
                item = root.child(i)
                if item.checkState(0):
                    use_cut.append(os.path.join(item.directory, item.file_name))
                    element = Element.from_string(item.file_name.split(".")[1])
                    elements.append(element)
                    DepthProfileDialog.checked_cuts[m_name].append(
                        item.file_name)
                child_count_2 = item.childCount()
                if child_count_2 > 0:  # Elemental Losses
                    for j in range(child_count_2):
                        item_child = item.child(j)
                        if item_child.checkState(0):
                            name = item_child.file_name
                            dir_e = os.path.join(
                                self.parent.obj
                                    .directory_composition_changes, "Changes")
                            use_cut.append(os.path.join(dir_e, name))
                            element = Element.from_string(item_child.file_name.
                                                          split(".")[1])
                            elements.append(element)
                            DepthProfileDialog.checked_cuts[m_name].\
                                append(item_child.file_name)
            progress_bar.setValue(20)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.
            
            # Get the x-axis unit to be used from the radio buttons
            x_unit = DepthProfileDialog.x_unit
            radio_buttons = self.findChildren(QtWidgets.QRadioButton)
            for radio_button in radio_buttons:
                if radio_button.isChecked():
                    x_unit = radio_button.text()
            DepthProfileDialog.x_unit = x_unit
            progress_bar.setValue(57)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            # Mac requires event processing to show progress bar and its
            # process.
            
            DepthProfileDialog.line_zero = self.ui.check_0line.isChecked()
            DepthProfileDialog.line_scale = self.ui.check_scaleline.isChecked() 
            DepthProfileDialog.systerr = self.ui.spin_systerr.value()
            
            # If items are selected, proceed to generating the depth profile
            if use_cut:
                self.ui.label_status.setText("Please wait. "
                                             "Creating depth profile.")
                QtCore.QCoreApplication.processEvents(
                    QtCore.QEventLoop.AllEvents)
                if self.parent.depth_profile_widget:
                    self.parent.del_widget(self.parent.depth_profile_widget)

                # If reference density changed, update value to measurement and
                # use_default_settings to False, all to_files.
                if self.__reference_density_spinbox:
                    self.parent.obj.reference_density = \
                        self.__reference_density_spinbox.value()
                    if self.parent.obj.reference_density != \
                            self.parent.obj.request.default_measurement\
                            .reference_density:
                        self.parent.obj.use_default_profile_settings = False
                        measurement_file_path = os.path.join(
                            self.parent.obj.directory,
                            self.parent.obj.measurement_setting_file_name +
                            ".measurement")
                        self.parent.obj.measurement_to_file(
                            measurement_file_path)
                        profile_file_path = os.path.join(
                            self.parent.obj.directory,
                            self.parent.obj.profile_name + ".profile")
                        self.parent.obj.profile_to_file(profile_file_path)

                        if self.parent.obj.detector is None:
                            default_det = self.parent.obj.\
                                request.default_detector
                            path = os.path.join(self.parent.obj.directory,
                                                "Detector")
                            if not os.path.exists(path):
                                os.makedirs(path)
                            path_to_det_file = os.path.join(path,
                                                            default_det.name
                                                            + ".detector")
                            self.parent.obj.detector = Detector(
                                path_to_det_file, measurement_file_path,
                                default_det.name, default_det.description,
                                time.time(), default_det.type,
                                default_det.foils, default_det.tof_foils,
                                default_det.virtual_size,
                                default_det.tof_slope,
                                default_det.tof_offset,
                                default_det.angle_slope,
                                default_det.angle_offset,
                                default_det.timeres, default_det.detector_theta)

                            self.parent.obj.detector.update_directories(path)
                            effs = default_det.get_efficiency_files()
                            for eff in effs:
                                self.parent.obj.detector.add_efficiency_file(
                                    os.path.join(default_det.
                                                 efficiency_directory, eff))
                            self.parent.obj.detector.to_file(os.path.join(
                                self.parent.obj.detector.path,
                                self.parent.obj.detector.name + ".detector"),
                                measurement_file_path)

                        if self.parent.obj.run is None:
                            default_run = \
                                self.parent.obj.request.default_measurement.run
                            beam = Beam(default_run.beam.ion,
                                        default_run.beam.energy,
                                        default_run.beam.charge,
                                        default_run.beam.energy_distribution,
                                        default_run.beam.spot_size,
                                        default_run.beam.divergence,
                                        default_run.beam.profile)
                            self.parent.obj.run = Run(beam,
                                                      default_run.fluence,
                                                      default_run.current,
                                                      default_run.charge,
                                                      default_run.time)
                            self.parent.obj.run.to_file(measurement_file_path)

                        if self.parent.obj.target is None:
                            default_target = \
                                self.parent.obj.request.default_measurement.\
                                target
                            self.parent.obj.target = Target(
                                default_target.name, time.time(),
                                default_target.description,
                                default_target.target_type,
                                default_target.image_size,
                                default_target.image_file,
                                default_target.scattering_element,
                                default_target.target_theta)
                            self.parent.obj.target.to_file(os.path.join(
                                self.parent.obj.directory,
                                self.parent.obj.name + ".target"),
                                measurement_file_path)
                
                self.parent.depth_profile_widget = \
                    DepthProfileWidget(self.parent,
                                       output_dir,
                                       use_cut,
                                       elements,
                                       x_unit,
                                       DepthProfileDialog.line_zero,
                                       DepthProfileDialog.line_scale,
                                       DepthProfileDialog.systerr)
                progress_bar.setValue(90)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.
                                                      AllEvents)
                # Mac requires event processing to show progress bar and its 
                # process.
                
                icon = self.parent.icon_manager.\
                    get_icon("depth_profile_icon_2_16.png")
                self.parent.add_widget(self.parent.depth_profile_widget,
                                       icon=icon)
                self.close()
            else:
                print("No cuts have been selected for depth profile.")
        except Exception as e:
            error_log = "Unexpected error: {0}".format(e)
            logging.getLogger(self.measurement.name).error(error_log)
        finally:
            self.__statusbar.removeWidget(progress_bar)
            progress_bar.hide()

    def __add_reference_density(self):
        """
        Add a filed for modifying the reference density.
        """
        layout = self.ui.horizontalAxisUnitsLayout

        ref_density_label = QtWidgets.QLabel(
            '<html><head/><body><p>Reference density [g/cm<span '
            'style=" vertical-align:super;">3</span>]:</p></body></html>')

        ref_density_spin_box = QtWidgets.QDoubleSpinBox()
        ref_density_spin_box.setMaximum(9999.00)
        ref_density_spin_box.setDecimals(2)
        ref_density_spin_box.setEnabled(True)
        ref_density_spin_box.setLocale(self.locale)

        ref_density_spin_box.setValue(self.measurement.reference_density)

        layout.insertWidget(3, ref_density_label)
        layout.insertWidget(4, ref_density_spin_box)

        self.__reference_density_label = ref_density_label
        self.__reference_density_spinbox = ref_density_spin_box

    def __remove_reference_density(self):
        """
        Remove reference density form dialog if it is there.
        """
        if self.__reference_density_spinbox and self.__reference_density_label:
            layout = self.ui.horizontalAxisUnitsLayout

            layout.removeWidget(self.__reference_density_label)
            self.__reference_density_label.deleteLater()

            layout.removeWidget(self.__reference_density_spinbox)
            self.__reference_density_spinbox.deleteLater()

            self.__reference_density_spinbox = None
            self.__reference_density_label = None

    def __update_eff_files(self):
        """Update efficiency files to UI which are used.
        """
        if self.parent.obj.detector is None:
            eff_files = self.parent.obj.request.default_detector\
                .get_efficiency_files()
        else:
            eff_files = self.parent.obj.detector.get_efficiency_files()
        eff_files_used = []
        root = self.ui.treeWidget.invisibleRootItem()
        child_count = root.childCount()
        for eff in eff_files:
            str_element = eff.split(".")[0]
            element = Element.from_string(str_element)
            for i in range(child_count): 
                item = root.child(i)
                # TODO: Perhaps make this update every time a cut file is
                # selected so user knows exactly what files are used instead
                # of what files match all the cut files.

                # TODO: Does not check elemental losses for efficiency files.
                if not hasattr(item, "file_name"):
                    continue
                cut_element = Element.from_string(item.file_name.split(".")[1])
                mass = cut_element.isotope
                if not mass:
                    mass = round(
                        masses.get_standard_isotope(cut_element.symbol), 0)
                if cut_element.symbol == element.symbol and \
                        mass == element.isotope:
                    eff_files_used.append(eff)
        if eff_files_used:
            self.ui.label_efficiency_files.setText(
               "Efficiency files used: \t\n{0}".format("\t\n".join(
                   eff_files_used)))
        else:
            self.ui.label_efficiency_files.setText("No efficiency files.")

    def __show_important_settings(self):
        """Show some important setting values in the depth profile parameter
        dialog for the user.
        """
        detector = self.measurement.get_detector_or_default()

        if self.measurement.use_default_profile_settings:
            depth_step_for_stopping = \
                self.measurement.request.default_measurement\
                    .depth_step_for_stopping
            number_of_depth_steps = \
                self.measurement.request.default_measurement\
                    .number_of_depth_steps
            depth_step_for_output = \
                self.measurement.request.default_measurement\
                    .depth_step_for_output
            depth_for_concentration_from = \
                self.measurement.request.default_measurement\
                    .depth_for_concentration_from
            depth_for_concentration_to = \
                self.measurement.request.default_measurement\
                    .depth_for_concentration_to
        else:
            depth_step_for_stopping = self.measurement.depth_step_for_stopping
            number_of_depth_steps = self.measurement.number_of_depth_steps
            depth_step_for_output = self.measurement.depth_step_for_output
            depth_for_concentration_from = self.measurement\
                .depth_for_concentration_from
            depth_for_concentration_to = self.measurement\
                .depth_for_concentration_to
        self.ui.label_calibslope.setText(str(detector.tof_slope))
        self.ui.label_caliboffset.setText(str(detector.tof_offset))
        self.ui.label_depthstop.setText(
            str(depth_step_for_stopping))
        self.ui.label_depthnumber.setText(
            str(number_of_depth_steps))
        self.ui.label_depthbin.setText(
            str(depth_step_for_output))
        self.ui.label_depthscale.setText("{0} - {1}".format(
            depth_for_concentration_from,
            depth_for_concentration_to))

        self.__update_eff_files()
        

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
            self.measurement = parent.obj
            self.output_dir = output_dir
            self.elements = elements
            self.x_units = x_units
            self.use_cuts = use_cuts
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
            dp = DepthFiles(self.use_cuts, output_files)
            # This has to be before create_depth_files()
            self.measurement.generate_tof_in()

            # Delete previous depth files to avoid mixup when assigning the
            # result files back to their cut files
            removed_files = []
            for file in os.listdir(self.output_dir):
                if file.startswith("depth"):
                    removed_files.append(os.path.join(self.output_dir, file))
            for f in removed_files:
                os.remove(f)
            dp.create_depth_files()
            
            # Check for RBS selections.
            rbs_list = {}
            for cut in self.use_cuts:
                filename = os.path.basename(cut)
                split = filename.split(".")
                element = Element.from_string(split[1])
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

            depth_scale_from = self.measurement.depth_for_concentration_from
            depth_scale_to = self.measurement.depth_for_concentration_to
            self.matplotlib = MatplotlibDepthProfileWidget(self,
                                                           self.output_dir,
                                                           self.elements,
                                                           rbs_list,
                                                           (depth_scale_from,
                                                            depth_scale_to),
                                                           self.use_cuts,
                                                           self.x_units,
                                                           True,  # legend
                                                           self.__line_zero,
                                                           self.__line_scale,
                                                           self.__systerr)
        except:
            import traceback
            msg = "Could not create Depth Profile graph. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[0].__name__ + ": " +
                                 traceback._some_str(sys.exc_info()[1]),
                                 err_file,
                                 str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.measurement.name).error(msg)
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
        self.parent.depth_profile_widget = None
        file = os.path.join(self.parent.obj.directory, self.save_file)
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
                         self.parent.obj.directory + "\\", "")
        file = os.path.join(self.parent.obj.directory_depth_profiles,
                            self.save_file)
        fh = open(file, "wt")
        fh.write("{0}\n".format(output_dir))
        fh.write("{0}\n".format("\t".join([str(element)
                                           for element in self.elements])))
        fh.write("{0}\n".format("\t".join([cut for cut in self.use_cuts])))
        fh.write("{0}\n".format(self.x_units))
        fh.write("{0}\n".format(self.__line_zero))
        fh.write("{0}\n".format(self.__line_scale))
        fh.write("{0}".format(self.__systerr))
        fh.close()

    def update_use_cuts(self):
        """
        Update used cuts list with new Measurement cuts.
        """
        for file in os.listdir(self.parent.obj.directory_cuts):
            for i in range(len(self.use_cuts)):
                cut = self.use_cuts[i]
                cut_split = cut.split('.')  # There is one dot more (.potku)
                file_split = file.split('.')
                if cut_split[2] == file_split[1] and cut_split[3] == \
                        file_split[2] and cut_split[4] == file_split[3]:
                    cut_file = os.path.join(self.parent.obj.directory_cuts,
                                            file)
                    self.use_cuts[i] = cut_file

        changes_dir = os.path.join(
            self.parent.obj.directory_composition_changes, "Changes")
        if os.path.exists(changes_dir):
            for file in os.listdir(changes_dir):
                for i in range(len(self.use_cuts)):
                    cut = self.use_cuts[i]
                    cut_split = cut.split('.')  # There is one dot more (.potku)
                    file_split = file.split('.')
                    if cut_split[2] == file_split[1] and cut_split[3] == \
                            file_split[2] and cut_split[4] == file_split[3]:
                        cut_file = os.path.join(changes_dir, file)
                        self.use_cuts[i] = cut_file

        self.output_dir = self.parent.obj.directory_depth_profiles
