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
__version__ = "2.0"

import os
import itertools
from collections import namedtuple, defaultdict
from typing import Union
from pathlib import Path

import widgets.gui_utils as gutils

from modules.base import ElementSimulationContainer
from modules.detector import Detector
from modules.measurement import Measurement
from modules.simulation import Simulation

from PyQt5 import QtWidgets
from PyQt5 import QtGui


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


def update_used_eff_file_label(qdialog, efficiency_files):
    """Updates the used efficiency file label of a qdialog

    Args:
        qdialog: qdialog whose label will be updated
        efficiency_files: list of efficiency files
    """
    eff_files_used = set()
    root = qdialog.treeWidget.invisibleRootItem()
    child_count = root.childCount()

    eff_elems = {
        Detector.get_used_efficiency_file_name(eff_file).stem: eff_file
        for eff_file in efficiency_files
    }

    for i in range(child_count):
        item = root.child(i)

        if not hasattr(item, "file_name"):
            continue

        # TODO check for RBS selection too
        cut_element_str = item.file_name.split(".")[1]

        if cut_element_str in eff_elems:
            eff_files_used.add(eff_elems[cut_element_str])

    if eff_files_used:
        eff_file_txt = "\t\n".join(str(f) for f in eff_files_used)
        qdialog.label_efficiency_files.setText(
           f"Efficiency files used:\t\n{eff_file_txt}")
    else:
        qdialog.label_efficiency_files.setText("No efficiency files.")


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
                    try:
                        save_file_path.unlink()
                    except OSError:
                        pass
                    break


# TODO common base class for settings dialogs


def update_detector_settings(entity: Union[Measurement, Simulation],
                             detector_folder: Path, measurement_file: Path):
    """

    Args:
        entity: either a Measurement or Simulation
        detector_folder: path to the detector's folder,
        measurement_file: path to .measurement file
    """
    # Create default Detector for Measurement
    detector_file_path = Path(detector_folder, "Default.detector")
    detector_folder.mkdir(exist_ok=True)

    entity.detector = Detector(
        detector_file_path, measurement_file)
    entity.detector.update_directories(detector_folder)

    # Transfer the default detector efficiencies to new
    # Detector
    for eff_file in entity.request.default_detector.get_efficiency_files(
            return_full_paths=True):
        entity.detector.add_efficiency_file(eff_file)


def update_tab(tab):
    for energy_spectra in tab.energy_spectrum_widgets:
        tab.del_widget(energy_spectra)
        save_file_path = Path(tab.simulation.directory,
                              energy_spectra.save_file)
        if os.path.exists(save_file_path):
            os.remove(save_file_path)
    tab.energy_spectrum_widgets = []


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


def _get_confirmation_msg(msg="settings",
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
    tpl = namedtuple("MessageBoxText", ("title", "body"))
    if finished_simulations and running_simulations:
        return tpl("Simulated and running simulations",
                   f"There are simulations that use the current {msg}, "
                   "and either have been simulated or are currently "
                   "running.\n"
                   "If you save changes, the running simulations "
                   "will be stopped, and the result files of the simulated "
                   "and stopped simulations are deleted. This also affects "
                   "possible optimization.\n\n"
                   "Do you want to save changes anyway?")

    if running_simulations:
        return tpl("Simulations running",
                   "There are simulations running that use the current "
                   f"{msg}.\n"
                   "If you save changes, the running simulations will be "
                   "stopped, and their result files deleted. This also affects "
                   "possible optimization.\n\n"
                   "Do you want to save changes anyway?")

    if finished_simulations:
        return tpl("Finished simulations",
                   f"There are simulations that use the current {msg}, "
                   "and have been simulated.\n"
                   "If you save changes, the result files of the simulated "
                   "simulations are deleted. This also affects possible "
                   "optimization.\n\n"
                   "Do you want to save changes anyway?")

    if running_optimizations:
        return tpl("Optimization running",
                   "There are optimizations running that use the current "
                   f"{msg}.\n"
                   "If you save changes, the running optimizations will be "
                   "stopped, and their result files deleted.\n\n"
                   "Do you want to save changes anyway?")

    if finished_optimizations:
        return tpl("Optimization results",
                   "There are optimization results that use the current "
                   f"{msg}.\n"
                   "If you save changes, result files will be deleted.\n\n"
                   "Do you want to save changes anyway?")

    # No simulations are running or finished so no message needs to be shown
    return None


def _get_confirmation(qdialog, msg="settings", **kwargs):
    """Displays a MessageBox to user to get a confirmation on deleting
    existing simulations.
    """
    msg = _get_confirmation_msg(msg=msg, **kwargs)
    if msg is None:
        # No text to shown so there were no running or finished simulations.
        # Safe to return True.
        return True

    msg_box = QtWidgets.QMessageBox(
        QtWidgets.QMessageBox.Question, msg.title, msg.body,
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No |
        QtWidgets.QMessageBox.Cancel, qdialog
    )
    msg_box.setDetailedText(_element_simulations_to_list(**kwargs))

    return msg_box.exec_() == QtWidgets.QMessageBox.Yes


def _element_simulations_to_list(finished_simulations,
                                 running_simulations,
                                 finished_optimizations,
                                 running_optimizations):
    """Formulates the given lists of ElementSimulations into a roughly csv
    formatted string.
    """
    # Transform the lists into a nested dictionary to avoid duplicates
    # TODO simplify this
    d = defaultdict(lambda: defaultdict(dict))
    for elem_sim in itertools.chain(finished_simulations,
                                    running_simulations,
                                    finished_optimizations,
                                    running_optimizations):
        d[elem_sim.simulation.sample.name][elem_sim.simulation.name][
            elem_sim.main_recoil.get_full_name()] = \
            elem_sim.is_optimization_running() or \
            elem_sim.is_optimization_finished()

    # Transform the dictionary into CSV rows
    lst = "SAMPLE\tSIMULATION\tRECOIL\n"
    for sample, sims in d.items():
        for sim, elem_sims in sims.items():
            for elem_sim, b in elem_sims.items():
                # Add * to indicate that the ElementSimulation is used in
                # optimization
                lst += f"{sample}\t{sim}\t\t{elem_sim}{'*' if b else ''}\n"

    header = f"Affected simulations:"
    footer = f"Simulations marked with * are being used in optimization."
    return f"{header}\n\n{lst}\n{footer}"


def delete_element_simulations(qdialog,
                               container: ElementSimulationContainer,
                               msg="settings", tab=None, filter_func=None):
    """Deletes running and finished simulations if given confirmation by
    the user.
    
    Args:
        qdialog: TODO
        container: TODO
        msg: TODO
        tab: TODO
        filter_func: optional function to filter ElementSimulations

    Return:
        True if simulations were deleted, False otherwise.
    """
    # TODO add ability to start a new simulation instead of deleting old one
    all_sims = container.get_active_simulations()
    if filter_func is not None:
        for elem_sim_list in all_sims:
            elem_sim_list[:] = list(filter(filter_func, elem_sim_list))

    if not _get_confirmation(qdialog, msg=msg, **all_sims._asdict()):
        return False

    # Reset simulations. Using set here as one ElementSimulation could appear
    # on multiple lists.
    for elem_sim in set(itertools.chain(*all_sims)):
        elem_sim.reset()

        # Change full edit unlocked
        # TODO remove reference to GUI element from RecoilElement
        try:
            elem_sim.recoil_elements[0].widgets[0].parent.full_edit_on = True
        except IndexError:
            # widget had not yet been created, nothing to do
            pass

        if tab is None:
            tab = get_related_tab(qdialog, elem_sim)

        try:
            tab.del_widget(elem_sim.optimization_widget)
            elem_sim.optimization_widget = None
        except AttributeError:
            # tab is still None, nothing to do
            pass

    if tab is not None:
        update_tab(tab)

    return True


def get_related_tab(qdialog, elem_sim):
    tab_id = elem_sim.simulation.tab_id
    if tab_id != -1:
        return qdialog.find_related_tab(tab_id)


def set_up_side_panel(qwidget, key, side):
    """Sets up the side panel of a QWidget by either hiding it or showing it
    and connecting callbacks to change the visibility of the panel.

    Args:
        qwidget: QWidget that has a reference to a side panel and a button that
            shows or hides the panel.
        key: key used to store the visibility of the panel in QSettings object.
        side: which side of the QWidget the side panel is ('left' or 'right')
    """
    show_panel = gutils.get_potku_setting(key, True, bool)

    # Show or hide panel depending on previous settings
    gutils.change_visibility(qwidget.frame,
                             visibility=show_panel)
    qwidget.hidePanelButton.clicked.connect(
        lambda: gutils.change_visibility(qwidget.frame, key=key)
    )
    if side == "left":
        open_arr = ">"
        close_arr = "<"
    elif side == "right":
        open_arr = "<"
        close_arr = ">"
    else:
        raise ValueError(f"Side should either be 'left' or 'right', '{side}' "
                         "given")

    # Change the arrow icon accordingly
    gutils.change_arrow(qwidget.hidePanelButton,
                        arrow=close_arr if show_panel else open_arr)
    qwidget.hidePanelButton.clicked.connect(
        lambda: gutils.change_arrow(qwidget.hidePanelButton)
    )


def get_btn_stylesheet(color: QtGui.QColor):
    """Returns a stylesheet for a button based on the given color.
    """
    luminance = 0.2126 * color.red() + 0.7152 * color.green()
    luminance += 0.0722 * color.blue()
    if luminance < 50:
        text_color = "white"
    else:
        text_color = "black"
    return f"background-color: {color.name()}; color: {text_color};"


def set_btn_color(button: QtWidgets.QPushButton, color: QtGui.QColor, colormap,
                  element: str):
    """Sets the background and text color of a button depending on the given
    color, colormap and element.
    """
    button.setStyleSheet(get_btn_stylesheet(color))

    try:
        if color.name() == colormap[element]:
            button.setText(f"Automatic [{element}]")
        else:
            button.setText("")
    except KeyError:
        button.setText("")
