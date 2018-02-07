# coding=utf-8
'''
Created on 21.3.2013
Updated on 23.5.2013

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli KÃ¤rkkÃ¤inen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import gc
import os
import sys
import shutil
from PyQt5 import QtWidgets, QtCore, uic
# from PyQt5 import uic

from Dialogs.AboutDialog import AboutDialog
from Dialogs.GlobalSettingsDialog import GlobalSettingsDialog
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
        
        self.panel_shown = True
        self.ui.hidePanelButton.clicked.connect(lambda: self.hide_panel())
        
        # Add delete button to the context menu of the treewidget.
        delete_measurement = QtWidgets.QAction("Delete", self.ui.treeWidget)
        self.ui.treeWidget.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.ui.treeWidget.addAction(delete_measurement)
        delete_measurement.triggered.connect(self.delete_selections)
        
        # Set up styles for main window 
        bg_blue = "images/background_blue.svg"  # Cannot use os.path.join
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

        
    def open_about_dialog(self):
        '''Show Potku program about dialog.
        '''
        AboutDialog()
        
        
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

        self.ui.frame.setShown(self.panel_shown)


    def current_measurement_save_cuts(self):
        """Saves the current open measurement tab widget's selected cuts 
        to cut files.
        """
        widget = self.ui.tab_measurements.currentWidget()
        widget.measurement_save_cuts()

    

    def current_measurement_analyze_elemental_losses(self):
        """Opens the element losses analyzation tool for the current open 
        measurement tab widget.
        """
        widget = self.ui.tab_measurements.currentWidget()
        widget.open_element_losses(widget)


    def current_measurement_create_energy_spectrum(self):
        """Opens the energy spectrum analyzation tool for the current open 
        measurement tab widget.
        """
        widget = self.ui.tab_measurements.currentWidget()
        widget.open_energy_spectrum(widget)


    def current_measurement_create_depth_profile(self):
        """Opens the depth profile analyzation tool for the current open 
        measurement tab widget.
        """
        widget = self.ui.tab_measurements.currentWidget()
        widget.open_depth_profile(widget)

    
    def delete_selections(self):
        '''Deletes the selected tree widget items.
        '''
        # TODO: Memory isn't released correctly. Maybe because of matplotlib.
        # TODO: Remove 'measurement_tab_widgets' variable and add tab reference
        # to treewidgetitem.
        selected_tabs = [self.measurement_tab_widgets[item.tab_id] for 
                         item in self.ui.treeWidget.selectedItems()]
        if selected_tabs: # Ask user a confirmation.
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
                return # If clicked Yes, then continue normally
        
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
        # check that the tab to be focused exists
        if not self.__tab_exists(clicked_item.tab_id): 
            self.ui.tab_measurements.addTab(tab, tab.measurement.measurement_name)
        self.ui.tab_measurements.setCurrentWidget(tab)    
  
        
    def __tab_exists(self, tab_id):
        '''Check if there is an open tab with the tab_id (identifier).
        
        Args:
            tab_id: Identifier (int) for the MeasurementTabWidget
            
        Returns:
            True if tab is found, False if not
        '''
        # Try to find the clicked item from tabwidget
        for i in range(0, self.ui.tab_measurements.count()):  
            # print(str(self.ui.tab_measurements.widget(i)))
            if self.ui.tab_measurements.widget(i).tab_id == tab_id:
                return True
        return False


    def remove_tab(self, tab_index):
        '''Remove tab which's close button has been pressed.
        
        Args:
            tab_index: Integer representing index of the current tab
        '''
        self.ui.tab_measurements.removeTab(tab_index)
        # self.ui.tab_measurements.removeTab(self.ui.tab_measurements.indexOf(tab))
    
    
    def open_project_settings(self):
        """Opens project settings dialog.
        """
        ProjectSettingsDialog(self.masses, self.project)
           
           
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
            self.__add_new_tab(filename, progress_bar)
            self.__remove_measurement_info_tab()
            self.statusbar.removeWidget(progress_bar)
            progress_bar.hide()
    
    
    def __add_new_tab(self, filename, progress_bar=None,
                      file_current=0, file_count=1):
        '''Add new tab into measurement TabWidget.
        
        Adds a new tab into program's tabWidget. Makes a new measurement for 
        said tab.
        
        Args:
            filename: String representing measurement file.
            progress_bar: Progress bar to be updated
            file_current: Integer representing which number is currently being
            read. (for GUI)
            file_count: Integer representing how many files will be loaded.
        '''
        if progress_bar:
            progress_bar.setValue((100 / file_count) * file_current)
        measurement = self.project.measurements.add_measurement_file(filename,
                                                                     self.tab_id)
        if measurement:
            tab = MeasurementTabWidget(self.tab_id, measurement, self.icon_manager)
            tab.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.measurement_tab_widgets[self.tab_id] = tab
            
            tab.add_log()      
            
            self.ui.tab_measurements.addTab(tab, measurement.measurement_name)
            self.ui.tab_measurements.setCurrentWidget(tab)
    
            tree_item = QtWidgets.QTreeWidgetItem()
            tree_item.setText(0, measurement.measurement_name)
            tree_item.tab_id = self.tab_id
            tree_item.setIcon(0, self.icon_manager.get_icon("folder_open.svg"))
            
            self.ui.treeWidget.addTopLevelItem(tree_item)
            self.tab_id += 1
  
        
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
            self.project = Project(dialog.directory, self.masses,
                                   self.statusbar, self.settings)
            self.settings.set_project_directory_last_open(dialog.directory)
            # Project made, close introduction tab
            self.__remove_introduction_tab()
            self.__open_measurement_info_tab()
            self.__set_project_buttons_enabled(True)
            

    def __set_project_buttons_enabled(self, state=False):
        """Enables 'project settings', 'save project' and 'new measurement' buttons.
        
        Args:
            state: True/False enables or disables buttons
        """
        self.ui.projectSettingsButton.setEnabled(state)
        self.ui.actionSave_Project.setEnabled(state)
        self.ui.actionNew_Measurement.setEnabled(state)
        self.ui.actionNew_measurement_2.setEnabled(state)
        self.ui.actionProject_Settings.setEnabled(state)
        

    def __open_measurement_info_tab(self):
        """Opens an info tab to the QTabWidget 'tab_measurements' that guides the 
        user to add a new measurement to the project.
        """
        self.ui.tab_measurements.addTab(self.ui.measurementInfoTab, "Info")
    
    
    def open_project(self):
        '''Shows a dialog to open a project.
        '''
        file = open_file_dialog(self,
                                self.settings.get_project_directory_last_open(),
                                "Open an existing project", "Project file (*.proj)")
        if file:
            self.__close_project()
            folder = os.path.split(file)[0]
            name = os.path.splitext(os.path.basename(file))[0]
            self.ui.setWindowTitle("{0} - Project: {1}".format(
                                                           self.title,
                                                           name))
            self.ui.treeWidget.setHeaderLabel("Project: {0}".format(name))
            self.project = Project(folder, self.masses,
                                   self.statusbar, self.settings)
            self.settings.set_project_directory_last_open(folder)
            measurements_in_project = self.project.get_measurements_files()
            
            progress_bar = QtWidgets.QProgressBar()
            self.statusbar.addWidget(progress_bar, 1)
            progress_bar.show()
            
            count = len(measurements_in_project)
            dirtyinteger = 0
            for measurement_file in measurements_in_project:
                self.__add_new_tab(measurement_file, progress_bar,
                                   dirtyinteger, count)
                dirtyinteger += 1
            
            self.__remove_introduction_tab()
            self.__set_project_buttons_enabled(True)
            
            self.statusbar.removeWidget(progress_bar)
            progress_bar.hide()
    
    
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
    
    
    def __remove_introduction_tab(self):
        """Removes an info tab from the QTabWidget 'tab_measurements' that guides
        the user to create a new project.
        """
        index = self.ui.tab_measurements.indexOf(self.ui.introduceTab)
        if index >= 0:
            self.ui.tab_measurements.removeTab(index)
            
            
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
        
        


def main():
    """Main function
    """
    app = QtWidgets.QApplication(sys.argv)
    window = Potku()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    
