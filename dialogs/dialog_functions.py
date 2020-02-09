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

import modules.masses as masses

from modules.element import Element


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
