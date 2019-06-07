# coding=utf-8
"""
Created on 19.4.2013
Updated on 13.11.2018

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os

from modules.cut_file import CutFile
from modules.element import Element

from PyQt5 import QtCore


class ElementLosses:
    """Element Losses class.
    """

    def __init__(self, directory_cuts, directory_composition_changes,
                 reference_cut_file, checked_cuts, partition_count,
                 progress_bar=None):
        """Inits Element Losses class.

        Args:
            directory_cuts: String representing cut file directory.
            directory_composition_changes: String representing elemental losses
                                           directory.
            reference_cut_file: String representing reference cut file.
            checked_cuts: String list of cut files to be graphed.
            partition_count: Integer representing split count.
            progress_bar: QtWidgets.QProgressBar or None if not given.
        """
        self.directory_cuts = directory_cuts
        self.directory_composition_changes = directory_composition_changes
        self.partition_count = partition_count
        self.checked_cuts = checked_cuts
        self.progress_bar = progress_bar

        self.reference_cut_file = reference_cut_file
        filename_split = reference_cut_file.split('.')
        element = Element.from_string(filename_split[2])
        self.reference_key = "{0}.{1}".format(element, filename_split[2])
        self.cut_splits = ElementLossesSplitHolder()

    def count_element_cuts(self, save_splits=False):
        """Count data points in splits based on reference file.

        Args:
            save_splits: Boolean representing whether to save element losses
                         splits.

        Return:
            Returns dictionary of elements and their counts within splits.
        """
        self.__load_cut_splits(save_splits)
        split_counts = self.__count_element_cuts()
        return split_counts

    def save_splits(self):
        """Save element splits as new cut files.
        """
        self.__element_losses_folder_clean_up()
        dirtyinteger = 0
        count = self.cut_splits.count()
        for key in self.cut_splits.get_keys():
            # Do not split elemental losses again.
            # TODO: Should elemental losses be possible to split again?
            if len(key.split('.')) == 4:
                continue
            main_cut = self.cut_splits.get_cut(key)
            splits = self.cut_splits.get_splits(key)

            split_count = len(splits)
            split_number = 0
            for split in splits:
                new_cut = CutFile(elem_loss=True,
                                  split_number=split_number,
                                  split_count=split_count)
                new_dir = os.path.join(self.directory_composition_changes,
                                       "Changes")
                new_cut.copy_info(main_cut, new_dir, split, split_count)
                new_cut.save(main_cut.element_number)
                split_number += 1
                if self.progress_bar:
                    self.progress_bar.setValue(
                        (100 / count) * dirtyinteger + (100 / count)
                        * (split_number / split_count))
                    QtCore.QCoreApplication.processEvents(
                        QtCore.QEventLoop.AllEvents)
                    # Mac requires event processing to show progress bar and its
                    # process.
            dirtyinteger += 1

    def __load_cut_splits(self, save=False):
        """Loads the checked cut files and splits them in smaller cuts.

        Args:
            save: Boolean representing whether we save splits or not.
        """
        self.reference_cut = CutFile()
        self.reference_cut.load_file(self.reference_cut_file)

        # Remove old (element losses) cut files
        if save:
            self.__element_losses_folder_clean_up()

        dirtyinteger = 0
        count = len(self.checked_cuts)
        for file in self.checked_cuts:
            if self.progress_bar:
                self.progress_bar.setValue((dirtyinteger / count) * 80)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
                # Mac requires event processing to show progress bar
                # and its process.
            cut = CutFile()
            cut.load_file(file)
            filename_split = file.split('.')
            element = filename_split[2] + "." + filename_split[3]
            if len(filename_split) == 6:  # Regular cut file
                key = "{0}.{1}".format(element, filename_split[4])
            else:  # Elemental Losses cut file
                key = "{0}.{1}.{2}".format(element,
                                           filename_split[4],
                                           filename_split[5])
            self.cut_splits.add_splits(key, cut,
                                       cut.split(self.reference_cut,
                                                 self.partition_count,
                                                 save=save))
            dirtyinteger += 1

    def __element_losses_folder_clean_up(self):
        for the_file in os.listdir(
                os.path.join(self.directory_composition_changes, "Changes")):
            file_path = os.path.join(
                os.path.join(self.directory_composition_changes, "Changes"),
                the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception:
                # TODO: logger.error?
                print("HELP! File unlink does something bad (elemloss)")

    def __count_element_cuts(self):
        """
        Counts the number of sublists' elements to another list and puts it
        under corresponding dictionary's key value. For example:
        cuts['H'] = [[13,4,25,6],[1,3,4,1],[2,3,2]] -->
                    __count_element_cuts['H'] = [4,4,3]

        Return:
            Returns dictionary of elements and their counts within splits.
        """
        split_counts_dict = {}
        dirtyinteger = 0
        count = self.cut_splits.count()
        # for key in self.cut_splits_dict.keys():
        for key in self.cut_splits.get_keys():
            if self.progress_bar:
                self.progress_bar.setValue((dirtyinteger / count) * 20 + 80)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
                # Mac requires event processing to show progress bar
                # and its process.

            # Reference cut is not counted, excluded from graph.
            if key != self.reference_key:
                split_counts_dict[key] = [len(split)
                                          for split
                                          in self.cut_splits.get_splits(key)]
            dirtyinteger += 1
        return split_counts_dict


class ElementLossesSplitHolder:
    """Element Losses Split Holder class to hold information of cuts' splits.
    """

    def __init__(self):
        """Inits the class
        """
        self.__cut_mains = {}  # Might be unnecessary.
        self.__splits = {}

    def count(self):
        """Get count of splits.

        Return:
            Returns count of cut files split.
        """
        return len(self.__splits)

    def get_keys(self):
        """Get keys of splits.

        Return:
            Returns all keys that are currently used.
        """
        return self.__splits.keys()

    def get_cut(self, key):
        """Get cut file used to make splits.
        """
        if key not in self.__cut_mains.keys():
            return None
        return self.__cut_mains[key]

    def get_splits(self, key):
        """Get splits of a cut file.
        """
        if key not in self.__splits.keys():
            return []
        return self.__splits[key]

    def add_splits(self, key, cut, splits):
        """Add splits to a cut file
        """
        if key not in self.__cut_mains.keys():
            self.__cut_mains[key] = cut
        self.__splits[key] = splits
