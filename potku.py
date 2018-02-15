# coding=utf-8
'''
Created on 21.3.2013
Updated on 27.8.2013

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import gc, os, shutil, sys, platform, subprocess
from datetime import datetime, timedelta
from PyQt5 import QtWidgets, QtCore, uic

from Dialogs.AboutDialog import AboutDialog
from Dialogs.GlobalSettingsDialog import GlobalSettingsDialog
from Dialogs.ImportMeasurementBinary import ImportDialogBinary
from Dialogs.ImportMeasurementDialog import ImportMeasurementsDialog
from Dialogs.MeasuringSettingsDialog import ProjectSettingsDialog
from Dialogs.ProjectNewDialog import ProjectNewDialog
from Modules.Functions import open_file_dialog
from Modules.GlobalSettings import GlobalSettings
from Modules.IconManager import IconManager
from Modules.Masses import Masses
from Modules.Project import Project
from Widgets.MeasurementTabWidget import MeasurementTabWidget


class Potku(QtWidgets.QMainWindow):
    '''Potku is main window class.
    '''
    
    def __init__(self):
        '''Init main window for Potku.
        '''
        super().__init__()
        self.ui = uic.loadUi(os.path.join("ui_files", "ui_main_window.ui"), self)
        self.title = self.ui.windowTitle()
        self.ui.treeWidget.setHeaderLabel("")
        
        self.icon_manager = IconManager()
        self.settings = GlobalSettings()
        self.project = None
        self.masses = Masses(os.path.join("external", "Potku-data", "masses.dat"))
        
        # Holds references to all the tab widgets in "tab_measurements" 
        # (even when they are removed from the QTabWidget)
        self.measurement_tab_widgets = {}  
        self.tab_id = 0  # identification for each tab

        # Set up connections within UI
        self.ui.actionNew_Measurement.triggered.connect(self.open_new_measurement)
        self.ui.projectSettingsButton.clicked.connect(self.open_project_settings)
        self.ui.globalSettingsButton.clicked.connect(self.open_global_settings)
        self.ui.tab_measurements.tabCloseRequested.connect(self.remove_tab)
        self.ui.treeWidget.itemDoubleClicked.connect(self.focus_selected_tab)
        
        self.ui.projectNewButton.clicked.connect(self.make_new_project)
        self.ui.projectOpenButton.clicked.connect(self.open_project)
        self.ui.actionNew_Project.triggered.connect(self.make_new_project)
        self.ui.actionOpen_Project.triggered.connect(self.open_project)
        self.ui.addNewMeasurementButton.clicked.connect(self.open_new_measurement)
        self.ui.actionNew_measurement_2.triggered.connect(self.open_new_measurement)
        self.ui.actionImport_pelletron.triggered.connect(self.import_pelletron)
        self.ui.actionBinary_data_lst.triggered.connect(self.import_binary)
        self.ui.action_manual.triggered.connect(self.__open_manual)
        
        self.ui.actionSave_cuts.triggered.connect(
                                self.current_measurement_save_cuts)
        self.ui.actionAnalyze_elemental_losses.triggered.connect(
                                self.current_measurement_analyze_elemental_losses)
        self.ui.actionCreate_energy_spectrum.triggered.connect(
                                self.current_measurement_create_energy_spectrum)
        self.ui.actionCreate_depth_profile.triggered.connect(
                                self.current_measurement_create_depth_profile)
        self.ui.actionGlobal_Settings.triggered.connect(self.open_global_settings)
        self.ui.actionProject_Settings.triggered.connect(self.open_project_settings)
        self.ui.actionAbout.triggered.connect(self.open_about_dialog)
        
        self.ui.actionNew_Project_2.triggered.connect(self.make_new_project)
        self.ui.actionOpen_Project_2.triggered.connect(self.open_project)
        self.ui.actionExit.triggered.connect(self.close)
        
        self.ui.menuImport.setEnabled(False)
        self.panel_shown = True
        self.ui.hidePanelButton.clicked.connect(lambda: self.hide_panel())
        
        # Add the context menu to the treewidget.
        delete_measurement = QtWidgets.QAction("Delete", self.ui.treeWidget)
        delete_measurement.triggered.connect(self.delete_selections)
        master_measurement = QtWidgets.QAction("Make master", self.ui.treeWidget)
        master_measurement.triggered.connect(self.__make_master_measurement)
        master_measurement_rem = QtWidgets.QAction("Remove master", self.ui.treeWidget)
        master_measurement_rem.triggered.connect(self.__remove_master_measurement)
        slave_measurement = QtWidgets.QAction("Exclude from slaves", self.ui.treeWidget)
        slave_measurement.triggered.connect(self.__make_nonslave_measurement)
        slave_measurement_rem = QtWidgets.QAction("Include as slave", self.ui.treeWidget)
        slave_measurement_rem.triggered.connect(self.__make_slave_measurement)
        self.ui.treeWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.ui.treeWidget.addAction(master_measurement)
        self.ui.treeWidget.addAction(master_measurement_rem)
        # self.ui.treeWidget.addSeparator() TODO: This should have separator
        # but doesn't work for QTreeWidget().
        self.ui.treeWidget.addAction(slave_measurement)
        self.ui.treeWidget.addAction(slave_measurement_rem)
        # self.ui.treeWidget.addSeparator() TODO: This should have separator
        # but doesn't work for QTreeWidget().
        self.ui.treeWidget.addAction(delete_measurement)
        
        # Set up styles for main window 
        bg_blue = "images/background_blue.svg"  # Cannot use os.path.join (PyQT+css)
        bg_green = "images/background_green.svg"
        style_intro = "QWidget#introduceTab {border-image: url(" + bg_blue + ");}"
        style_mesinfo = ("QWidget#measurementInfoTab {border-image: url(" + 
                         bg_green + ");}")
        self.ui.introduceTab.setStyleSheet(style_intro)
        self.ui.measurementInfoTab.setStyleSheet(style_mesinfo)
        self.__remove_measurement_info_tab()
        
        self.ui.setWindowIcon(self.icon_manager.get_icon("potku_icon.ico"))        
        
        # Set main window's icons to place
        self.__set_icons()
        self.ui.showMaximized()


    def current_measurement_create_depth_profile(self):
        """Opens the depth profile analyzation tool for the current open 
        measurement tab widget.
        """
        widget = self.ui.tab_measurements.currentWidget()
        if hasattr(widget, "measurement"):
            widget.open_depth_profile(widget)
        else:
            QtWidgets.QMessageBox.question(self,
              "Notification",
              "An open measurement is required to do this action.",
              QtWidgets.QMessageBox.Ok)
        
        
    def current_measurement_analyze_elemental_losses(self):
        """Opens the element losses analyzation tool for the current open 
        measurement tab widget.
        """
        widget = self.ui.tab_measurements.currentWidget()
        if hasattr(widget, "measurement"):
            widget.open_element_losses(widget)
        else:
            QtWidgets.QMessageBox.question(self,
              "Notification",
              "An open measurement is required to do this action.",
              QtWidgets.QMessageBox.Ok)
        
        
    def current_measurement_create_energy_spectrum(self):
        """Opens the energy spectrum analyzation tool for the current open 
        measurement tab widget.
        """
        widget = self.ui.tab_measurements.currentWidget()
        if hasattr(widget, "measurement"):
            widget.open_energy_spectrum(widget)
        else:
            QtWidgets.QMessageBox.question(self,
              "Notification",
              "An open measurement is required to do this action.",
              QtWidgets.QMessageBox.Ok)


    def current_measurement_save_cuts(self):
        """Saves the current open measurement tab widget's selected cuts 
        to cut files.
        """
        widget = self.ui.tab_measurements.currentWidget()
        if hasattr(widget, "measurement"):
            widget.measurement_save_cuts()
        else:
            QtWidgets.QMessageBox.question(self,
              "Notification",
              "An open measurement is required to do this action.",
              QtWidgets.QMessageBox.Ok)
    
    
    def delete_selections(self):
        '''Deletes the selected tree widget items.
        '''
        # TODO: Memory isn't released correctly. Maybe because of matplotlib.
        # TODO: Remove 'measurement_tab_widgets' variable and add tab reference
        # to treewidgetitem.
        selected_tabs = [self.measurement_tab_widgets[item.tab_id] for 
                         item in self.ui.treeWidget.selectedItems()]
        if selected_tabs:  # Ask user a confirmation.
            reply = QtWidgets.QMessageBox.question(self,
                   "Confirmation",
                   "Deleting selected measurements will " \
                   + "delete all files and folders under" \
                   + " selected measurement directories." + \
                   "\n\nAre you sure you want to delete selected measurements?",
                   QtWidgets.QMessageBox.Yes,
                   QtWidgets.QMessageBox.No,
                   QtWidgets.QMessageBox.Cancel)
            if reply == QtWidgets.QMessageBox.No or reply == QtWidgets.QMessageBox.Cancel:
                return  # If clicked Yes, then continue normally
        
        for tab in selected_tabs:
            measurement = self.project.measurements.get_key_value(tab.tab_id)
            try:
                # Close and remove logs
                measurement.remove_and_close_log(measurement.defaultlog)
                measurement.remove_and_close_log(measurement.errorlog)
                
                # Remove measurement's directory tree
                shutil.rmtree(measurement.directory)
                os.remove(os.path.join(self.project.directory,
                                       measurement.measurement_file))
            except:
                print("Error with removing files")
                QtWidgets.QMessageBox.question(self, "Confirmation",
                               "Problem with deleting files.",
                               QtWidgets.QMessageBox.Ok)
                measurement.set_loggers()
                return
            
            self.project.measurements.remove_by_tab_id(tab.tab_id)
            remove_index = self.ui.tab_measurements.indexOf(tab)
            self.remove_tab(remove_index)  # Remove measurement from open tabs 
            
            tab.histogram.matplotlib.delete()
            tab.elemental_losses_widget.matplotlib.delete()
            tab.energy_spectrum_widget.matplotlib.delete()
            tab.depth_profile_widget.matplotlib.delete()
            
            tab.mdiArea.closeAllSubWindows()
            del self.measurement_tab_widgets[tab.tab_id]
            tab.close() 
            tab.deleteLater()
            
        # Remove selected from tree widget
        root = self.ui.treeWidget.invisibleRootItem()
        for item in self.ui.treeWidget.selectedItems():
            (item.parent() or root).removeChild(item)
        gc.collect()  # Suggest garbage collector to clean.
            

    def focus_selected_tab(self, clicked_item):
        '''Focus to selected tab (in tree widget) and if it isn't open, open it.
        
        Args:
            clicked_item: TreeWidgetItem with tab_id attribute (int) that connects
            the item to the corresponding MeasurementTabWidget
        '''
        # TODO: This doesn't work. There is no list/dictionary of references to the
        # tab widgets once they are removed from the QTabWidget. 
        # tab = self.project_measurements[clicked_item.tab_id]
        tab = self.measurement_tab_widgets[clicked_item.tab_id]
        name = tab.measurement.measurement_name
        
        # Check that the data is read.
        if not tab.data_loaded:
            tab.data_loaded = True
            progress_bar = QtWidgets.QProgressBar()
            loading_bar = QtWidgets.QProgressBar()
            loading_bar.setMinimum(0)
            loading_bar.setMaximum(0)
            self.statusbar.addWidget(progress_bar, 1)
            self.statusbar.addWidget(loading_bar, 2)
            progress_bar.show()
            loading_bar.show()
            progress_bar.setValue(5)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
            
            tab.measurement.load_data()
            progress_bar.setValue(35)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
            
            tab.add_histogram()
            loading_bar.hide()
            self.statusbar.removeWidget(loading_bar)
            
            progress_bar.setValue(50)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
            tab.check_previous_state_files(progress_bar)  # Load previous states.
            self.statusbar.removeWidget(progress_bar)
            progress_bar.hide()
            self.__change_tab_icon(clicked_item)
            master_mea = tab.measurement.project.get_master()
            if master_mea and tab.measurement.measurement_name == \
                              master_mea.measurement_name:
                name = "{0} (master)".format(name)
        
        # Check that the tab to be focused exists.
        if not self.__tab_exists(clicked_item.tab_id): 
            self.ui.tab_measurements.addTab(tab, name)
        self.ui.tab_measurements.setCurrentWidget(tab)
  

    def hide_panel(self, enable_hide=None):
        """Sets the frame (including measurement navigation view, global 
        settings and project settings buttons) visible.
        
        Args:
            enable_hide: If True, sets the frame visible and vice versa. 
            If not given, sets the frame visible or hidden depending its 
            previous state.
        """
        if enable_hide != None:
            self.panel_shown = enable_hide
        else:
            self.panel_shown = not self.panel_shown    
        if self.panel_shown:
            self.ui.hidePanelButton.setText('<')
        else:
            self.ui.hidePanelButton.setText('>')

        self.ui.frame.setVisible(self.panel_shown)


    def import_pelletron(self):
        '''Import Pelletron's measurements into project.
        
        Import Pelletron's measurements from 
        '''
        if not self.project: 
            return
        import_dialog = ImportMeasurementsDialog(self.project,
                                                 self.icon_manager,
                                                 self.statusbar,
                                                 self)  # For loading measurements.
        if import_dialog.imported:
            self.__remove_measurement_info_tab()
            
            
    def import_binary(self):
        '''Import binary measurements into project.
        
        Import binary measurements from 
        '''
        if not self.project: 
            return
        import_dialog = ImportDialogBinary(self.project,
                                           self.icon_manager,
                                           self.statusbar,
                                           self)  # For loading measurements.
        if import_dialog.imported:
            self.__remove_measurement_info_tab()
                

    def load_project_measurements(self, measurements=[]):
        '''Load measurement files in the project.
        
        Args:
            measurements: A list representing loadable measurements when importing
                          measurements to the project.
        '''
        if measurements:
            measurements_in_project = measurements
            load_data = True
        else:
            measurements_in_project = self.project.get_measurements_files()
            load_data = False
        progress_bar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()
        
        count = len(measurements_in_project)
        dirtyinteger = 0
        for measurement_file in measurements_in_project:
            self.__add_new_tab(measurement_file, progress_bar,
                               dirtyinteger, count, load_data=load_data)
            dirtyinteger += 1

        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()
        

    def make_new_project(self):
        """Opens a dialog for creating a new project.
        """
        dialog = ProjectNewDialog(self)
        # TODO: regex check for directory. I.E. do not allow asd/asd
        if dialog.directory:
            self.__close_project()
            title = "{0} - Project: {1}".format(self.title, dialog.name)
            self.ui.setWindowTitle(title)
            self.ui.treeWidget.setHeaderLabel("Project: {0}".format(dialog.name))
            self.project = Project(dialog.directory, dialog.name, self.masses,
                                   self.statusbar, self.settings,
                                   self.measurement_tab_widgets)
            self.settings.set_project_directory_last_open(dialog.directory)
            # Project made, close introduction tab
            self.__remove_introduction_tab()
            self.__open_measurement_info_tab()
            self.__set_project_buttons_enabled(True)

       
    def open_about_dialog(self):
        '''Show Potku program about dialog.
        '''
        AboutDialog()
    
    
    def open_global_settings(self):
        """Opens global settings dialog.
        """
        GlobalSettingsDialog(self.masses, self.settings)
        
    
    def open_new_measurement(self):
        '''Opens file an open dialog and if filename is given opens new measurement 
        from it.
        '''
        if not self.project: 
            return
        filename = open_file_dialog(self,
                                    self.project.directory,
                                    "Select a measurement to load",
                                    "Raw Measurement (*.asc)")
        if filename:
            try:
                self.ui.tab_measurements.removeTab(self.ui.tab_measurements.indexOf(
                                                   self.measurement_info_tab))
            except: 
                pass  # If there is no info tab, no need to worry about.
                # print("Can't find an info tab to remove")
            progress_bar = QtWidgets.QProgressBar()
            self.statusbar.addWidget(progress_bar, 1)
            progress_bar.show()
            self.__add_new_tab(filename, progress_bar, load_data=True)
            self.__remove_measurement_info_tab()
            self.statusbar.removeWidget(progress_bar)
            progress_bar.hide()


    def open_project(self):
        '''Shows a dialog to open a project.
        '''
        file = open_file_dialog(self,
                                self.settings.get_project_directory_last_open(),
                                "Open an existing project", "Project file (*.proj)")
        if file:
            self.__close_project()
            folder = os.path.split(file)[0]
            tmp_name = os.path.splitext(os.path.basename(file))[0]
            self.project = Project(folder, tmp_name, self.masses,
                                   self.statusbar, self.settings,
                                   self.measurement_tab_widgets)
            self.ui.setWindowTitle("{0} - Project: {1}".format(
                                                       self.title,
                                                       self.project.get_name()))
            self.ui.treeWidget.setHeaderLabel(
                                 "Project: {0}".format(self.project.get_name()))
            self.settings.set_project_directory_last_open(folder)
            
            self.load_project_measurements()
            self.__remove_introduction_tab()
            self.__set_project_buttons_enabled(True)
            
            master_measurement_name = self.project.has_master()
            nonslaves = self.project.get_nonslaves()
            if master_measurement_name:
                master_measurement = None
                keys = self.project.measurements.measurements.keys()
                for key in keys:
                    measurement = self.project.measurements.measurements[key]
                    if measurement.measurement_name == master_measurement_name:
                        master_measurement = measurement
                        self.project.set_master(measurement)
                        break
            root = self.treeWidget.invisibleRootItem()
            root_child_count = root.childCount()
            for i in range(root_child_count):
                item = root.child(i)
                tab_widget = self.measurement_tab_widgets[item.tab_id]
                tab_name = tab_widget.measurement.measurement_name
                if master_measurement_name and \
                   item.tab_id == master_measurement.tab_id:
                    item.setText(0,
                                 "{0} (master)".format(master_measurement_name))
                elif tab_name in nonslaves or not master_measurement_name:
                    item.setText(0, tab_name)
                else:
                    item.setText(0, "{0} (slave)".format(tab_name))
                
                       
                

    def open_project_settings(self):
        """Opens project settings dialog.
        """
        ProjectSettingsDialog(self.masses, self.project)
          

    def remove_tab(self, tab_index):
        '''Remove tab which's close button has been pressed.
        
        Args:
            tab_index: Integer representing index of the current tab
        '''
        self.ui.tab_measurements.removeTab(tab_index)
    

    def __add_measurement_to_tree(self, measurement_name, load_data):
        '''Add measurement to tree where it can be opened.
        
        Args:
            measurement_name: A string representing measurement's name.
            load_data: A boolean representing if measurement data is loaded.
        '''
        tree_item = QtWidgets.QTreeWidgetItem()
        tree_item.setText(0, measurement_name)
        tree_item.tab_id = self.tab_id
        # tree_item.setIcon(0, self.icon_manager.get_icon("folder_open.svg"))
        if load_data:
            self.__change_tab_icon(tree_item, "folder_open.svg")
        else:
            self.__change_tab_icon(tree_item, "folder_locked.svg")
        self.ui.treeWidget.addTopLevelItem(tree_item)
        
        
    def __add_new_tab(self, filename, progress_bar=None,
                      file_current=0, file_count=1, load_data=False):
        '''Add new tab into measurement TabWidget.
        
        Adds a new tab into program's tabWidget. Makes a new measurement for 
        said tab.
        
        Args:
            filename: A string representing measurement file.
            progress_bar: A QtWidgets.QProgressBar to be updated.
            file_current: An integer representing which number is currently being
                          read. (for GUI)
            file_count: An integer representing how many files will be loaded.
            load_data: A boolean representing whether to load data or not. This is
                       to save time when loading a project and we do not want to
                       load every measurement.
        '''
        if progress_bar:
            progress_bar.setValue((100 / file_count) * file_current)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
        measurement = self.project.measurements.add_measurement_file(filename,
                                                                     self.tab_id)
        if measurement:  # TODO: Finish this (load_data)
            tab = MeasurementTabWidget(self.tab_id, measurement,
                                       self.masses, self.icon_manager)
            #self.connect(tab, QtCore.SIGNAL("issueMaster"), self.__master_issue_commands)
            tab.issueMaster.connect(self.__master_issue_commands)

            tab.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.measurement_tab_widgets[self.tab_id] = tab
            tab.add_log()
            tab.data_loaded = load_data
            if load_data:
                loading_bar = QtWidgets.QProgressBar()
                loading_bar.setMinimum(0)
                loading_bar.setMaximum(0)
                self.statusbar.addWidget(loading_bar, 1)
                loading_bar.show()
                
                measurement.load_data()  
                tab.add_histogram()  
                self.ui.tab_measurements.addTab(tab, measurement.measurement_name)
                self.ui.tab_measurements.setCurrentWidget(tab)
                
                loading_bar.hide()
                self.statusbar.removeWidget(loading_bar)
            self.__add_measurement_to_tree(measurement.measurement_name, load_data)
            self.tab_id += 1
    
    
    def __change_tab_icon(self, tree_item, icon="folder_open.svg"):
        '''Change tab icon in QTreeWidgetItem.
        
        Args:
            tree_item: A QtWidgets.QTreeWidgetItem class object.
            icon: A string representing the icon name.
        '''
        tree_item.setIcon(0, self.icon_manager.get_icon(icon))
    
    
    def __close_project(self):
        """Closes the project for opening a new one.
        """
        if self.project:
            # TODO: Doesn't release memory
            # Clear the treewidget
            self.ui.treeWidget.clear()
            self.ui.tab_measurements.clear()
            self.project = None
            self.measurement_tab_widgets = {}  
            self.tab_id = 0
        
        
    def __make_nonslave_measurement(self):
        """Exclude selected measurements from slave category.
        """
        items = self.ui.treeWidget.selectedItems()
        if not items:
            return
        master = self.project.get_master()
        # Remove (slave) text from tree titles
        for item in items:
            tab_widget = self.measurement_tab_widgets[item.tab_id]
            tab_measurement = tab_widget.measurement
            tab_name = tab_measurement.measurement_name
            if master and tab_name != master.measurement_name:
                self.project.exclude_slave(tab_measurement)
                item.setText(0, tab_name)
    
    
    def __make_slave_measurement(self):
        """Exclude selected measurements from slave category.
        """
        items = self.ui.treeWidget.selectedItems()
        if not items:
            return
        master = self.project.get_master()
        # Add (slave) text from tree titles
        for item in items:
            tab_widget = self.measurement_tab_widgets[item.tab_id]
            tab_measurement = tab_widget.measurement
            tab_name = tab_measurement.measurement_name
            if master and tab_name != master.measurement_name:
                self.project.include_slave(tab_measurement)
                item.setText(0, "{0} (slave)".format(tab_name))
        
               
    def __make_master_measurement(self):
        """Make selected or first of the selected measurements 
        a master measurement.
        """
        items = self.ui.treeWidget.selectedItems()
        if not items:
            return
        master_tree = items[0]
        master_tab = self.measurement_tab_widgets[master_tree.tab_id]
        self.project.set_master(master_tab.measurement)
        # old_master = self.project.get_master()
        nonslaves = self.project.get_nonslaves()
        
        # if old_master:
        #    old_master_name = old_master.measurement_name
        #    self.ui.tab_measurements.setTabText(old_master.tab_id, old_master_name)
        root = self.treeWidget.invisibleRootItem()
        root_child_count = root.childCount()
        for i in range(root_child_count):
            item = root.child(i)
            tab_widget = self.measurement_tab_widgets[item.tab_id]
            tab_name = tab_widget.measurement.measurement_name
            if item.tab_id == master_tab.tab_id:
                item.setText(0, "{0} (master)".format(tab_name))
            elif tab_name in nonslaves:
                item.setText(0, tab_name)
            else:
                item.setText(0, "{0} (slave)".format(tab_name))
            tab_widget.toggle_master_button()
        # master_tab.toggle_master_button()
        # QtGui.QTabWidget().count()
        for i in range(self.ui.tab_measurements.count()):
            tab = self.ui.tab_measurements.widget(i)
            tab_name = tab.measurement.measurement_name
            if tab.tab_id == master_tab.tab_id:
                tab_name = "{0} (master)".format(tab_name)
                self.ui.tab_measurements.setTabText(tab.tab_id, tab_name)
            else:
                self.ui.tab_measurements.setTabText(tab.tab_id, tab_name)
    
    
    def __master_issue_commands(self):
        """Issue commands from master measurement to all slave measurements in 
        the project.
        """
        reply = QtWidgets.QMessageBox.question(self,
                "Confirmation",
                "You are about to issue actions from master measurement to all " + \
                "slave measurements in the project. This can take several " + \
                "minutes. Please wait until notification is shown." + \
                "\nDo you wish to continue?",
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return
        
        time_start = datetime.now()
        progress_bar = QtWidgets.QProgressBar()
        self.statusbar.addWidget(progress_bar, 1)
        progress_bar.show()
        nonslaves = self.project.get_nonslaves()
        master = self.project.get_master()
        master_tab = self.measurement_tab_widgets[master.tab_id]
        master_name = master.measurement_name
        directory = master.directory
        progress_bar.setValue(1)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
        # Load selections and save cut files
        # TODO: Make a check for these if identical already -> don't redo.
        self.project.save_selection(master)
        progress_bar.setValue(10)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
        
        self.project.save_cuts(master)
        progress_bar.setValue(25)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
        
        root = self.treeWidget.invisibleRootItem()
        root_child_count = root.childCount()
        i = 1
        for i in range(root_child_count):
            item = root.child(i)
            tab = self.measurement_tab_widgets[item.tab_id]
            tab_measurement = tab.measurement
            tab_name = tab_measurement.measurement_name
            if tab_name == master_name or tab_name in nonslaves:
                continue
            # Load measurement data if the slave is
            if not tab.data_loaded:
                tab.data_loaded = True
                progress_bar_data = QtWidgets.QProgressBar()
                self.statusbar.addWidget(progress_bar_data, 1)
                progress_bar_data.show()
                progress_bar_data.setValue(5)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
                
                tab.measurement.load_data()
                progress_bar_data.setValue(35)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents) 
                
                tab.add_histogram()
                progress_bar_data.hide()
                self.statusbar.removeWidget(progress_bar_data)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
                # Update tree item icon to open folder
                tree_item = None
                root = self.treeWidget.invisibleRootItem()
                root_child_count = root.childCount()
                for i in range(root_child_count):
                    item = root.child(i)
                    if item.tab_id == tab.tab_id:
                        tree_item = item
                        break
                if tree_item:
                    self.__change_tab_icon(tree_item)
            # Check all widgets of master and do them for slaves.
            if master_tab.depth_profile_widget and tab.data_loaded:
                if tab.depth_profile_widget:
                    tab.del_widget(tab.depth_profile_widget)
                tab.make_depth_profile(directory, master_name)
                tab.depth_profile_widget.save_to_file()
            if master_tab.elemental_losses_widget and tab.data_loaded:
                if tab.elemental_losses_widget:
                    tab.del_widget(tab.elemental_losses_widget)
                tab.make_elemental_losses(directory, master_name)
                tab.elemental_losses_widget.save_to_file()
            if master_tab.energy_spectrum_widget and tab.data_loaded:
                if tab.energy_spectrum_widget:
                    tab.del_widget(tab.energy_spectrum_widget)
                tab.make_energy_spectrum(directory, master_name)
                tab.energy_spectrum_widget.save_to_file()
            progress_bar.setValue(25 + (i / root_child_count) * 75)
            QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
            i += 1
        self.statusbar.removeWidget(progress_bar)
        progress_bar.hide()
        time_end = datetime.now()
        time_duration = (time_end - time_start).seconds
        time_str = timedelta(seconds=time_duration)
        QtWidgets.QMessageBox.question(self,
                "Notification",
                "Master measurement's actions have been issued to slaves. " + \
                "\nElapsed time: {0}".format(time_str),
                QtWidgets.QMessageBox.Ok)
        
        
    def __open_measurement_info_tab(self):
        """Opens an info tab to the QTabWidget 'tab_measurements' that guides the 
        user to add a new measurement to the project.
        """
        self.ui.tab_measurements.addTab(self.ui.measurementInfoTab, "Info")
    

    def __remove_introduction_tab(self):
        """Removes an info tab from the QTabWidget 'tab_measurements' that guides
        the user to create a new project.
        """
        index = self.ui.tab_measurements.indexOf(self.ui.introduceTab)
        if index >= 0:
            self.ui.tab_measurements.removeTab(index)
    
    
    def __remove_master_measurement(self):
        """Remove master measurement
        """
        old_master = self.project.get_master()
        self.project.set_master()  # No master measurement
        root = self.treeWidget.invisibleRootItem()
        root_child_count = root.childCount()
        for i in range(root_child_count):
            item = root.child(i)
            tab_widget = self.measurement_tab_widgets[item.tab_id]
            tab_name = tab_widget.measurement.measurement_name
            item.setText(0, tab_name)
            tab_widget.toggle_master_button()
        if old_master:
            measurement_name = old_master.measurement_name
            self.ui.tab_measurements.setTabText(old_master.tab_id, measurement_name)
            old_master_tab = self.measurement_tab_widgets[old_master.tab_id]
            old_master_tab.toggle_master_button()
        self.project.set_master()  # No master measurement
        
             
    def __remove_measurement_info_tab(self):
        """Removes an info tab from the QTabWidget 'tab_measurements' that guides
        the user to add a new measurement to the project.
        """
        index = self.ui.tab_measurements.indexOf(self.ui.measurementInfoTab)
        if index >= 0:
            self.ui.tab_measurements.removeTab(index)
        
 
    def __set_icons(self):
        """Adds icons to the main window.
        """
        self.icon_manager.set_icon(self.ui.projectSettingsButton, "gear.svg")
        self.icon_manager.set_icon(self.ui.globalSettingsButton, "gear.svg")
        self.icon_manager.set_icon(self.ui.actionNew_Project, "file.svg")
        self.icon_manager.set_icon(self.ui.actionOpen_Project, "folder_open.svg")
        self.icon_manager.set_icon(self.ui.actionSave_Project, "amarok_save.svg")
        self.icon_manager.set_icon(self.ui.actionNew_Measurement, "log.svg")
        
               
    def __set_project_buttons_enabled(self, state=False):
        """Enables 'project settings', 'save project' and 'new measurement' buttons.
        
        Args:
            state: True/False enables or disables buttons
        """
        self.ui.projectSettingsButton.setEnabled(state)
        self.ui.actionSave_Project.setEnabled(state)
        self.ui.actionNew_Measurement.setEnabled(state)
        self.ui.actionNew_measurement_2.setEnabled(state)
        self.ui.menuImport.setEnabled(state)
        self.ui.actionProject_Settings.setEnabled(state)
        # TODO: Should these only be enabled when there is measurement open?
        self.ui.actionAnalyze_elemental_losses.setEnabled(state)
        self.ui.actionCreate_energy_spectrum.setEnabled(state)
        self.ui.actionCreate_depth_profile.setEnabled(state)


    def __tab_exists(self, tab_id):
        '''Check if there is an open tab with the tab_id (identifier).
        
        Args:
            tab_id: Identifier (int) for the MeasurementTabWidget
            
        Returns:
            True if tab is found, False if not
        '''
        # Try to find the clicked item from QTabWidget.
        for i in range(0, self.ui.tab_measurements.count()):
            if self.ui.tab_measurements.widget(i).tab_id == tab_id:
                return True
        return False
        
        
    def __open_manual(self):
        '''Open user manual.
        '''
        manual_filename = os.path.join('manual', 'Potku-manual.pdf');
        used_os = platform.system()
        if used_os == 'Windows':
            os.startfile(manual_filename)
        elif used_os == 'Linux':
            subprocess.call(('xdg-open', manual_filename))
        elif used_os == 'Darwin':
            subprocess.call(('open', manual_filename))


def main():
    """Main function
    """
    app = QtWidgets.QApplication(sys.argv)
    window = Potku()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    
