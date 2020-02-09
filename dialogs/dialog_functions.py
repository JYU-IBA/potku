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


def update_efficiency_files(detector):
    """Updates the efficiency files in the given detector by adding and
    removing files.
    """
    added_files = set()
    for file in detector.efficiencies:
        detector.add_efficiency_file(file)
        added_files.add(file)

    detector.efficiencies.clear()

    for file in detector.efficiencies_to_remove:
        if file not in added_files:
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
