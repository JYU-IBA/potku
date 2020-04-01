# coding=utf-8
"""
Created on 8.2.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 TODO

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

These functions mainly aim to remove code duplication in dialogs.
"""
__author__ = "Juhani Sundell"
__version__ = ""    # TODO

import os
import copy
import itertools
import collections

import modules.masses as masses
import modules.general_functions as gf

from pathlib import Path

from modules.element import Element
from modules.detector import Detector
from dialogs.element_selection import ElementSelectionDialog

from PyQt5 import QtWidgets


def update_efficiency_files(detector):
    """Updates the efficiency files in the given detector by adding and
    removing files.
    """
    # TODO if a file is removed and new file with same name is added, this
    #      also removes the new file
    for file in detector.efficiencies:
        detector.add_efficiency_file(file)

    detector.efficiencies.clear()

    for file in detector.efficiencies_to_remove:
        detector.remove_efficiency_file(file)

    # Clear the list so same files do not get deleted over and over
    # again
    detector.efficiencies_to_remove.clear()


def check_for_red(widget):
    """Looks for invalid values in widgets tab collection
    and blocks signals if it finds one.
    """
    for i in range(widget.tabs.count()):
        tab_widget = widget.tabs.widget(i)
        valid = tab_widget.fields_are_valid
        if not valid:
            widget.tabs.blockSignals(True)
            widget.tabs.setCurrentWidget(tab_widget)
            widget.tabs.blockSignals(False)
            break


def update_cuts(cut_files, cut_dir, changes_dir):
    """Update used cuts list with new Measurement cuts.

    Args:
        cut_files: list of absolute paths to .cut files. This list will
                   be modified in place.
        cut_dir: directory where the .cut files are stored
        changes_dir: absolute path to measurement's
                     'Composition_changes/Changes' directory
    """
    _update_cuts(cut_files, cut_dir)

    if os.path.exists(changes_dir):
        # TODO check when the files get added to changes_dir as it seems
        #      to be empty most of the time
        _update_cuts(cut_files, changes_dir)


def _update_cuts(old_cut_files, directory):
    """Updates references to .cut files when name of the measurement
    (and thus the directory) has been changed.

    Args:
        old_cut_files: list of absolute paths to .cut files. List is modified
                       in place.
        directory: current directory that contains the .cut files
    """
    for file in os.listdir(directory):
        for i, cut in enumerate(old_cut_files):
            file_name = Path(cut).name

            cut_split = file_name.split(".")
            file_split = file.split(".")

            if len(file_split) != len(cut_split):
                continue

            if cut_split[1:5] == file_split[1:5]:
                old_cut_files[i] = Path(directory, file)


def get_updated_efficiency_files(qdialog, efficiency_files):
    """Returns a list of used efficiency files that can be used to update
    a GUI element

    Args:
        qdialog:
        efficiency_files:
    """
    eff_files_used = []
    root = qdialog.ui.treeWidget.invisibleRootItem()
    child_count = root.childCount()
    for eff in efficiency_files:
        str_element, _ = eff.split(".")
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

    return eff_files_used

# TODO stop_simulations and delete_energy_spectra are still work in progress
#      so the code looks untidy. The code should be left pretty much untouched
#      until duplicated code segments have been refactored.


def delete_optim_espe(qdialog, elem_sim):
    """Deletes energy spectra from optimized recoils"""
    # TODO refactor this wit delete_simu_espe
    for opt_rec in elem_sim.optimization_recoils:
        delete_recoil_espe(qdialog.tab, opt_rec.get_full_name())


def delete_recoil_espe(tab, recoil_name):
    """Deletes recoil's energy spectra.
    """
    for energy_spectra in tab.energy_spectrum_widgets:
        for element_path in energy_spectra.energy_spectrum_data:
            file_name = Path(element_path).name
            if file_name.startswith(recoil_name):
                if file_name[len(recoil_name)] == ".":
                    tab.del_widget(energy_spectra)
                    tab.energy_spectrum_widgets.remove(energy_spectra)
                    save_file_path = Path(tab.simulation.directory,
                                          energy_spectra.save_file)
                    if save_file_path.exists():
                        os.remove(save_file_path)
                    # TODO check if more files need to be deleted
                    break


# TODO common base class for settings dialogs


def change_element(qdialog, button, combo_box):
    """ Opens element selection dialog and loads selected element's isotopes
    to a combobox.

    Args:
        qdialog: settings dialog that calls this function
        button: button whose text is changed accordingly to the made
        selection.
        combo_box: combo box to be filled
    """
    dialog = ElementSelectionDialog()
    if dialog.element:
        button.setText(dialog.element)
        # Enabled settings once element is selected
        qdialog.enabled_element_information()
        masses.load_isotopes(dialog.element, combo_box)

        # Check if no isotopes
        if combo_box.count() == 0:
            qdialog.measurement_settings_widget.ui.isotopeInfoLabel \
                .setVisible(True)
            qdialog.measurement_settings_widget.fields_are_valid = False
            gf.set_input_field_red(combo_box)
        else:
            qdialog.measurement_settings_widget.ui.isotopeInfoLabel \
                .setVisible(False)
            qdialog.measurement_settings_widget.check_text(
                qdialog.measurement_settings_widget.ui.nameLineEdit,
                qdialog.measurement_settings_widget)
            combo_box.setStyleSheet("background-color: %s" % "None")


def update_detector_settings(entity, det_folder_path,
                             measurement_settings_file_path):
    """

    Args:
        entity: either a Measurement or Simulation
        det_folder_path: path to the detector's folder,
        measurement_settings_file_path: TODO
    """
    # TODO this could be a function of Measurement and Simulation
    # Create default Detector for Measurement
    detector_file_path = os.path.join(det_folder_path,
                                      "Default.detector")
    if not os.path.exists(det_folder_path):
        os.makedirs(det_folder_path)
    entity.detector = Detector(
        detector_file_path, measurement_settings_file_path)
    entity.detector.update_directories(
        det_folder_path)

    # Transfer the default detector efficiencies to new
    # Detector
    entity.detector.efficiencies = list(
        entity.request.default_detector.efficiencies)
    # Default efficiencies are emptied because efficiencies
    # added in measurement specific dialog go by default in
    # the list. The list is only used for this transferring,
    # so emptying it does no harm.
    entity.request.default_detector. \
        efficiencies = []


def update_tab(tab):
    for energy_spectra in tab.energy_spectrum_widgets:
        tab.del_widget(energy_spectra)
        save_file_path = Path(tab.simulation.directory,
                              energy_spectra.save_file)
        if os.path.exists(save_file_path):
            os.remove(save_file_path)
    tab.energy_spectrum_widgets = []


def req_settings_stop(qdialog):
    tmp_sims = copy.copy(qdialog.request.running_simulations)
    for elem_sim in tmp_sims:
        if not elem_sim.optimization_running:
            elem_sim.stop()

            update_inner_recoils(qdialog, elem_sim)

        else:
            # Handle optimization
            elem_sim.reset()

            tab_del(qdialog, elem_sim)


def req_settings_optim_update(qdialog, tmp_sims):
    for elem_sim in tmp_sims:
        elem_sim.optimization_stopped = True
        elem_sim.optimization_running = False

        tab_del(qdialog, elem_sim)


def tab_del(qdialog, elem_sim):
    tab_id = elem_sim.simulation.tab_id
    if tab_id != -1:
        tab = qdialog.find_related_tab(tab_id)
        if tab:
            tab.del_widget(elem_sim.optimization_widget)
            elem_sim.simulations_done = False
            # Handle optimization energy spectra

            # TODO check that this is never None
            # Delete energy spectra that use optimized recoils
            for recoil in elem_sim.optimization_recoils:
                delete_recoil_espe(tab, recoil.get_full_name())


def reg_settings_del_sims(qdialog, simulations_run):
    for elem_sim in simulations_run:
        update_inner_recoils(qdialog, elem_sim)


def update_inner_recoils(qdialog, elem_sim):
    for recoil in elem_sim.recoil_elements:
        # Delete files
        gf.delete_simulation_results(elem_sim, recoil)
    # Change full edit unlocked
    if elem_sim.recoil_elements[0].widgets:
        elem_sim.recoil_elements[0].widgets[0].parent.full_edit_on = True

    elem_sim.simulations_done = False

    # Find element simulation's tab
    tab_id = elem_sim.simulation.tab_id
    if tab_id != -1:
        tab = qdialog.find_related_tab(tab_id)
        if tab:
            # Delete energy spectra that use recoil
            for recoil in elem_sim.recoil_elements:
                delete_recoil_espe(tab, recoil.get_full_name())

    # Reset controls
    if elem_sim.controls:
        # TODO do not access controls via elem_sim. Use
        #      observation.
        elem_sim.controls.reset_controls()


# TODO common base class for import dialogs


def add_imported_files_to_tree(qdialog, files):
    """

    Args:
        qdialog: import dialog
        files: list of files
    """
    if not files:
        return
    for file in files:
        if file in qdialog.files_added:
            continue
        directory, filename = os.path.split(file)
        name, unused_ext = os.path.splitext(filename)
        item = QtWidgets.QTreeWidgetItem([name])
        item.file = file
        item.name = name
        item.filename = filename
        item.directory = directory
        qdialog.files_added[file] = file
        qdialog.treeWidget.addTopLevelItem(item)


def _get_confirmation_msg(msg_str="settings",
                          finished_simulations=None,
                          running_simulations=None,
                          finished_optimizations=None,
                          running_optimizations=None):
    """Returns a message to be displayed on a MessageBox when simulations
    are about to be deleted.

    Keyword arguments are truthy values representing finished or running
    simulations or optimizations.

    Return:
        namedtuple with message title and body if at least one of the keyword
        arguments is True. Otherwise returns None.
    """
    msg = collections.namedtuple("Msg", ("title", "body"))
    if finished_simulations and running_simulations:
        return msg("Simulated and running simulations",
                   f"There are simulations that use the current {msg_str}, "
                   "and either have been simulated or are currently running.\n"
                   "If you save changes, the running simulations "
                   "will be stopped, and the result files of the simulated "
                   "and stopped simulations are deleted. This also affects "
                   "possible optimization.\n\n"
                   "Do you want to save changes anyway?")

    if running_simulations:
        return msg("Simulations running",
                   "There are simulations running that use the current "
                   f"{msg_str}.\n"
                   "If you save changes, the running simulations will be "
                   "stopped, and their result files deleted. This also affects "
                   "possible optimization.\n\n"
                   "Do you want to save changes anyway?")

    if finished_simulations:
        return msg("Finished simulations",
                   f"There are simulations that use the current {msg_str}, "
                   "and have been simulated.\n"
                   "If you save changes, the result files of the simulated "
                   "simulations are deleted. This also affects possible "
                   "optimization.\n\n"
                   "Do you want to save changes anyway?")

    if running_optimizations:
        return msg("Optimization running",
                   "There are optimizations running that use the current "
                   f"{msg_str}.\n"
                   "If you save changes, the running optimizations will be "
                   "stopped, and their result files deleted.\n\n"
                   "Do you want to save changes anyway?")

    if finished_optimizations:
        return msg("Optimization results",
                   "There are optimization results that use the current "
                   f"{msg_str}.\n"
                   "If you save changes, result files will be deleted.\n\n"
                   "Do you want to save changes anyway?")

    # No simulations are running or finished so no message needs to be shown
    return None


def _get_confirmation(qdialog, **kwargs):
    """Displays a MessageBox to user to get a confirmation on deleting
    existing simulations.
    """
    msg = _get_confirmation_msg(**kwargs)
    if msg is None:
        # No text to shown so there were no running or finished simulations.
        # Safe to return True.
        return True

    reply = QtWidgets.QMessageBox.question(
        qdialog, msg.title, msg.body,
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
        QtWidgets.QMessageBox.Cancel, QtWidgets.QMessageBox.Cancel)

    return reply == QtWidgets.QMessageBox.Yes


def delete_element_simulations(qdialog, tab, simulation,
                               element_simulation=None, msg_str="settings"):
    """Deletes running and finished simulations if given confirmation by
    the user.

    Return:
        True if simulations were deleted, False otherwise.
    """
    # TODO add ability to start a new simulation instead of deleting old one
    all_sims = simulation.get_active_simulations()
    if element_simulation is not None:
        for elem_sim_list in all_sims:
            elem_sim_list[:] = [elem_sim for elem_sim in elem_sim_list if
                                elem_sim is element_simulation]

    if not _get_confirmation(qdialog, msg_str=msg_str,
                             **all_sims._asdict()):
        return False

    # Reset simulations
    for elem_sim in itertools.chain(*all_sims):
        elem_sim.reset()

        # Change full edit unlocked
        # TODO remove reference to GUI element from RecoilElement
        elem_sim.recoil_elements[0].widgets[0].parent.full_edit_on = True

        tab.del_widget(elem_sim.optimization_widget)

    update_tab(tab)

    return True
