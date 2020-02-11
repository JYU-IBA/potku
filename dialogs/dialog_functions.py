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

import modules.masses as masses
import modules.general_functions as gf

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
    for i in range(widget.ui.tabs.count()):
        tab_widget = widget.ui.tabs.widget(i)
        valid = tab_widget.fields_are_valid
        if not valid:
            widget.ui.tabs.blockSignals(True)
            widget.tabs.setCurrentWidget(tab_widget)
            widget.ui.tabs.blockSignals(False)
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


def _update_cuts(cut_files, directory):
    for file in os.listdir(directory):
        for i in range(len(cut_files)):
            cut = cut_files[i]
            # TODO This does not work if there are extra '.' chars on the path

            cut_split = cut.split('.')  # There is one dot more (.potku)
            file_split = file.split('.')
            if cut_split[2] == file_split[1] and cut_split[3] == \
                    file_split[2] and cut_split[4] == file_split[3]:
                cut_file = os.path.join(directory, file)
                cut_files[i] = cut_file


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
        delete_recoil_espe(qdialog, opt_rec)


def delete_recoil_espe(qdialog, recoil):
    """Deletes recoil's energy spectra"""
    for energy_spectra in qdialog.tab.energy_spectrum_widgets:
        for element_path in energy_spectra. \
                energy_spectrum_data.keys():
            elem = recoil.prefix + "-" + recoil.name
            if elem in element_path:
                index = element_path.find(elem)
                if element_path[index - 1] == os.path.sep and \
                        element_path[index + len(elem)] == '.':
                    qdialog.tab.del_widget(energy_spectra)
                    qdialog.tab.energy_spectrum_widgets.remove(
                        energy_spectra)
                    save_file_path = os.path.join(
                        qdialog.tab.simulation.directory,
                        energy_spectra.save_file)
                    if os.path.exists(save_file_path):
                        os.remove(save_file_path)
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


def handle_element_simulation_stopping(qdialog, simulations_run,
                                       optimization_run):
    """

    Args:
        qdialog: settings dialog that calls this function
        simulations_run: list of element simulations
        optimization_run: list of element simulations used in optimization
    """
    for elem_sim in simulations_run:
        delete_simu_espe(qdialog, elem_sim)

        # Reset controls
        if elem_sim.controls:
            # TODO do not access controls via elem_sim. Use
            #      observation.
            elem_sim.controls.reset_controls()

        # Change full edit unlocked
        elem_sim.recoil_elements[0].widgets[0].parent. \
            edit_lock_push_button.setText("Full edit unlocked")
        elem_sim.simulations_done = False

    for elem_sim in optimization_run:
        qdialog.tab.del_widget(elem_sim.optimization_widget)
        elem_sim.simulations_done = False
        # Handle optimization energy spectra
        if elem_sim.optimization_recoils:
            # Delete energy spectra that use
            # optimized recoils
            delete_optim_espe(qdialog, elem_sim)


def delete_simu_espe(qdialog, elem_sim):
    """Deletes energy spectra related to the given element simulation as well
    as the simulation results.
    """
    for recoil in elem_sim.recoil_elements:
        gf.delete_simulation_results(elem_sim, recoil)
        # Delete energy spectra that use recoil
        delete_recoil_espe(qdialog, recoil)


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


def stop_simulations(qdialog, tmp_sims):
    for elem_sim in tmp_sims:
        if not elem_sim.optimization_running:
            elem_sim.stop()

            # Delete files
            delete_simu_espe(qdialog, elem_sim)

            # Reset controls
            if elem_sim.controls:
                # TODO do not access controls via elem_sim. Use
                #      observation.
                elem_sim.controls.reset_controls()

        else:
            # Handle optimization
            if elem_sim.optimization_recoils:
                elem_sim.stop(optimize_recoil=True)
            else:
                elem_sim.stop()
            elem_sim.optimization_stopped = True
            elem_sim.optimization_running = False

            qdialog.tab.del_widget(elem_sim.optimization_widget)
            # Handle optimization energy spectra
            if elem_sim.optimization_recoils:
                # Delete energy spectra that use
                # optimized recoils
                delete_optim_espe(qdialog, elem_sim)

        # Change full edit unlocked
        elem_sim.recoil_elements[0].widgets[0].parent. \
            edit_lock_push_button.setText("Full edit unlocked")
        elem_sim.simulations_done = False


def clear_element_simulation(qdialog):
    """Removes everything from the element simulation belonging to the
    given qdialog.
    """
    for recoil in qdialog.element_simulation.recoil_elements:
        # Delete files
        gf.delete_simulation_results(qdialog.element_simulation, recoil)

        # Delete energy spectra that use recoil
        delete_recoil_espe(qdialog, recoil)

    # Reset controls
    if qdialog.element_simulation.controls:
        # TODO do not access controls via elem_sim. Use
        #      observation.
        qdialog.element_simulation.controls.reset_controls()
    # Change full edit unlocked
    qdialog.element_simulation.recoil_elements[0].widgets[0]. \
        parent.edit_lock_push_button.setText(
        "Full edit unlocked")
    qdialog.element_simulation.simulations_done = False


def delete_existing_simulations(qdialog):
    qdialog.tab.del_widget(qdialog.element_simulation.optimization_widget)
    qdialog.element_simulation.simulations_done = False
    # Handle optimization energy spectra
    if qdialog.element_simulation.optimization_recoils:
        # Delete energy spectra that use
        # optimized recoils
        delete_optim_espe(qdialog, qdialog.element_simulation)


def stop_simulations_layerprops(qdialog):
    tmp_sims = copy.copy(qdialog.simulation.running_simulations)
    for elem_sim in tmp_sims:
        if not elem_sim.optimization_running:
            elem_sim.stop()

            # Delete files
            for recoil in elem_sim.recoil_elements:
                gf.delete_simulation_results(elem_sim, recoil)
            # Change full edit unlocked
            elem_sim.recoil_elements[0].widgets[0].parent. \
                edit_lock_push_button.setText("Full edit unlocked")
            elem_sim.simulations_done = False

            # Reset controls
            if elem_sim.controls:
                # TODO do not access controls via elem_sim. Use
                #      observation.
                elem_sim.controls.reset_controls()
        else:
            # Handle optimization
            if elem_sim.optimization_recoils:
                elem_sim.stop(optimize_recoil=True)
            else:
                elem_sim.stop()
            elem_sim.optimization_stopped = True
            elem_sim.optimization_running = False

            if qdialog.tab:
                qdialog.tab.del_widget(elem_sim.optimization_widget)
            elem_sim.simulations_done = False

    if qdialog.tab:
        update_tab(qdialog.tab)


def update_tab(tab):
    for energy_spectra in tab.energy_spectrum_widgets:
        tab.del_widget(energy_spectra)
        save_file_path = os.path.join(
            tab.simulation.directory,
            energy_spectra.save_file)
        if os.path.exists(save_file_path):
            os.remove(save_file_path)
    tab.energy_spectrum_widgets = []


def update_tabs_after_stopping(qdialog, optimization_running, optimization_run):
    for elem_sim in optimization_running:
        elem_sim.optimization_stopped = True
        elem_sim.optimization_running = False

        if qdialog.tab:
            qdialog.tab.del_widget(elem_sim.optimization_widget)
        elem_sim.simulations_done = False

    if qdialog.tab:
        update_tab(qdialog.tab)

    for elem_sim in optimization_run:
        if qdialog.tab:
            qdialog.tab.del_widget(elem_sim.optimization_widget)
        elem_sim.simulations_done = False


def update_optim_running(qdialog, optimization_running):
    tmp_sims = copy.copy(optimization_running)
    for elem_sim in tmp_sims:
        # Handle optimization
        elem_sim.optimization_stopped = True
        elem_sim.optimization_running = False

        qdialog.tab.del_widget(elem_sim.optimization_widget)
        elem_sim.simulations_done = False
        # Handle optimization energy spectra
        if elem_sim.optimization_recoils:
            # Delete energy spectra that use
            # optimized recoils
            delete_optim_espe(qdialog, elem_sim)


def req_settings_stop(qdialog):
    tmp_sims = copy.copy(qdialog.request.running_simulations)
    for elem_sim in tmp_sims:
        if not elem_sim.optimization_running:
            elem_sim.stop()

            update_inner_recoils(qdialog, elem_sim)

        else:
            # Handle optimization
            if elem_sim.optimization_recoils:
                elem_sim.stop(optimize_recoil=True)
            else:
                elem_sim.stop()
            elem_sim.optimization_stopped = True
            elem_sim.optimization_running = False

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
            #if elem_sim.optimization_recoils:
            # Delete energy spectra that use optimized recoils
            del_espes_for_recs(tab, elem_sim.optimization_recoils)


def reg_settings_del_sims(qdialog, simulations_run):
    for elem_sim in simulations_run:
        update_inner_recoils(qdialog, elem_sim)


def update_inner_recoils(qdialog, elem_sim):
    for recoil in elem_sim.recoil_elements:
        # Delete files
        gf.delete_simulation_results(elem_sim, recoil)
    # Change full edit unlocked
    if elem_sim.recoil_elements[0].widgets:
        elem_sim.recoil_elements[0].widgets[0].parent. \
            edit_lock_push_button.setText("Full edit "
                                          "unlocked")
    elem_sim.simulations_done = False

    # Find element simulation's tab
    tab_id = elem_sim.simulation.tab_id
    if tab_id != -1:
        tab = qdialog.find_related_tab(tab_id)
        if tab:
            # Delete energy spectra that use recoil
            del_espes_for_recs(tab, elem_sim.recoil_elements)

    # Reset controls
    if elem_sim.controls:
        # TODO do not access controls via elem_sim. Use
        #      observation.
        elem_sim.controls.reset_controls()


def del_espes_for_recs(tab, recoils):
    for recoil in recoils:
        # Delete energy spectra that use recoil
        for energy_spectra in tab.energy_spectrum_widgets:
            for element_path in energy_spectra.energy_spectrum_data.keys():
                elem = recoil.prefix + "-" + recoil.name
                if elem in element_path:
                    index = element_path.find(elem)
                    if element_path[index - 1] == os.path.sep \
                            and element_path[index + len(elem)] == '.':
                        tab.del_widget(energy_spectra)
                        tab.energy_spectrum_widgets.remove(energy_spectra)
                        save_file_path = os.path.join(
                            tab.simulation.directory,
                            energy_spectra.save_file)
                        if os.path.exists(save_file_path):
                            os.remove(save_file_path)
                        break


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
