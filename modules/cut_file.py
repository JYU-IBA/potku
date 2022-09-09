# coding=utf-8
"""
Created on 26.3.2013
Updated on 20.11.2018

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

import itertools

from pathlib import Path
from typing import List
from typing import Dict
from typing import Optional
from typing import Any

from .element import Element
from . import file_paths as fp


class CutFile:
    """
    Cut file_path object for when reading cut files is necessary.
    """
    def __init__(self, directory: Optional[Path] = None, elem_loss=False,
                 weight_factor=1.0, split_number=0, split_count=1,
                 cut_file_path: Optional[Path] = None):
        """Inits CutFile object.
        
        Args:
            directory: String representing cut directory.
            elem_loss: Boolean representing whether cut file_path is made from
                elemental losses splits.
            weight_factor: Float representing element weight factor. 
            split_number: Integer. Required for Elemental Losses, do not
                overwrite splits.
            split_count: Integer. Required for Elemental Losses, total count of 
                splits.
        """
        self.directory = directory
        self.element = None  # If RBS, this holds beam ion
        self.element_scatter = None
        self.count = 0
        self.is_elem_loss = elem_loss
        self.split_number = split_number
        self.split_count = split_count
        self.type = "ERD"   # TODO type should be an enum
        self.weight_factor = weight_factor
        self.energy = None
        self.detector_angle = None
        self.data = []
        self.element_number = None

        if cut_file_path is not None:
            self.load_file(cut_file_path)
    
    def set_info(self, selection, data: List[Any]):
        """Set selection information and data into CutFile.
        
        Args:
            selection: Selection class object.
            data: Lists of data points.
        """
        self.data = data
        self.element = selection.element
        self.element_scatter = selection.element_scatter
        self.count = len(data)
        self.is_elem_loss = False
        self.type = selection.type
        self.weight_factor = selection.weight_factor
        # TODO: Is this meta information necessary?
        self.energy = 0
        self.detector_angle = 0

    def load_file(self, file: Path):
        """Load and parse cut file_path.
        
        Args:
            file: absolute path to .cut file
        """
        if not file:
            return
        directory_cuts, file_name = file.parent, file.name
        self.directory = directory_cuts     # TODO .parent
        # os.path is not required for following.
        # Get number of element selection, i.e.
        # Two H selections -> numbers are 0 and 1
        # self.element_number = file.split('/')[-1].split('.')[1]
        # tof_e_01048.Pm.0 << Element count: 0, element_information: Pm
        # tof_e_01048.1H.0.2 << Element count: 0, element_information: 1H
        element_information = file_name.split(".")[1]
        self.element_number = int(file_name.split(".")[3])

        self.element = Element.from_string(element_information)

        # print("Load cut: {0} {1}".format(self.element, self.isotope))
        with file.open("r") as cut_file:
            for i, line in enumerate(cut_file):
                if i < 10:  # Probably not the best way.
                    line_split = line.strip().split(':')
                    if len(line_split) > 1: 
                        key = line_split[0].strip()
                        value = line_split[1].strip()
                        if key == "Count":
                            self.count = int(value)
                        elif key == "Type":
                            self.type = value
                        elif key == "Weight Factor":
                            self.weight_factor = float(value)
                        elif key == "Energy":
                            self.energy = float(value)
                        elif key == "Detector Angle":
                            self.detector_angle = int(value)
                        elif key == "Scatter Element":
                            self.element_scatter = Element(value)
                        elif key == "Element losses":
                            self.is_elem_loss = value == "True"
                        elif key == "Split count":
                            self.split_count = int(value)
                else:
                    self.data.append([int(i) for i in line.split()])
    
    def save(self, element_count=0):
        """Save cut file_path.
        
        Saves data points into cut file_path with meta information.
        
        Args:
            element_count: Integer representing which selection was used of
            total count of same element and isotope selection. This is so
            that we do not overwrite first 2H selection with other
            2H selection.
        """
        element = self.element
        if element and self.directory and self.data:
            measurement_name_with_prefix = self.directory.parents[1]
            # First "-" is in sample name, second in measurement name
            # NOT IF THERE ARE - IN NAME PART!!
            name_with_number = measurement_name_with_prefix.name.split(
                "Measurement_")[1]
            measurement_name = name_with_number.split('-', 1)[1]
            if element != "":
                element = str(element)
            if self.type == "RBS":
                suffix = f"RBS_{self.element_scatter}"
            else:
                suffix = "ERD"

            self.directory.mkdir(exist_ok=True, parents=True)

            if self.is_elem_loss:
                file = Path(
                    self.directory,
                    "{0}.{1}.{2}.{3}.{4}.cut".format(
                        measurement_name, element, suffix, element_count,
                        self.split_number))
            else:
                file = self._find_available_cut_file_name(
                    measurement_name, element, suffix, element_count)
            if self.element_scatter != "":
                element_scatter = str(self.element_scatter)
            else:
                element_scatter = ""
            with file.open("w") as my_file:
                my_file.write(f"Count: {self.count}\n")
                my_file.write(f"Type: {self.type}\n")
                my_file.write(f"Weight Factor: {self.weight_factor}\n")
                my_file.write("Energy: 0\n")
                my_file.write("Detector Angle: 0\n")
                my_file.write(f"Scatter Element: {element_scatter}\n")
                my_file.write(f"Element losses: {self.is_elem_loss}\n")
                my_file.write(f"Split count: {self.split_count}\n")
                my_file.write("\n")
                my_file.write("ToF, Energy, Event number\n")
                for p in self.data:  # Write all points
                    my_file.write(" ".join(map(str, p)))
                    my_file.write("\n")
         
    def split(self, reference_cut, splits=10, save=True):
        """Splits cut file into X splits based on reference cut.
        
        Args:
            reference_cut: Cut file (of heavy element) which is used split.
            splits: Integer determining how many splits is cut splitted to.
            save: Boolean deciding whether or not to save splits.
            
        Return:
            Returns a list containing lists of the cut's splits' values.
        """
        # Cast to int to cut decimals.
        split_size = int(len(reference_cut.data) / splits)  
        self_size = len(self.data)
        row_index, split = 0, 0
        cut_splits = [[] for _ in range(splits)]
        while split < splits and row_index < self_size:
            # Get last event number in first split
            max_event = reference_cut.data[((split + 1) * split_size) - 1][-1]  
            while row_index < self_size and \
                    self.data[row_index][-1] <= max_event:
                cut_splits[split].append(self.data[row_index])
                row_index += 1
            split += 1
        if save:
            self.__save_splits(splits, cut_splits)
        return cut_splits

    def _find_available_cut_file_name(self, measurement_name, element, suffix,
                                      elem_count: int) -> Path:
        """Helper function for finding available file name.
        """
        def cut_file_generator():
            for i in itertools.count(start=elem_count):
                yield Path(
                    self.directory,
                    f"{measurement_name}.{element}.{suffix}.{i}.cut")
        return fp.find_available_file_path(cut_file_generator())

    def __save_splits(self, splits, cut_splits):
        """Save splits into new CutFiles.
        
        Args:
            splits: Integer determining how many splits is cut split to.
            cut_splits: List of split data.
        """
        split_number = 0
        for split in cut_splits:
            new_cut = CutFile(elem_loss=True,
                              split_number=split_number,
                              split_count=splits)
            new_cut.copy_info(self, split, splits)
            new_cut.save(self.element_number)
            split_number += 1

    def copy_info(self, cut_file, new_dir, data, additional_weight_factor=1.0):
        """Copy information from cut file_path object into this.
        
        Args:
            cut_file: CutFile class object.
            new_dir: New directory for cut file.
            data: List of data points.
            additional_weight_factor: Float
        """
        self.directory = new_dir
        self.data = data
        self.element = cut_file.element
        self.count = len(data)
        self.type = cut_file.type
        self.weight_factor = cut_file.weight_factor * additional_weight_factor
        self.energy = cut_file.energy
        self.detector_angle = cut_file.detector_angle
        self.element_scatter = cut_file.element_scatter


def is_rbs(file: Path) -> bool:
    """Check if cut file is RBS.
    
    Args:
        file: A string representing file to be checked.
        
    Return:
        Returns True if cut file is RBS and False if not.
    """
    with file.open("r") as cut_file:
        for i, line in enumerate(cut_file):
            if i >= 10:
                return False
            line_split = line.strip().split(':')
            if len(line_split) > 1: 
                key = line_split[0].strip()
                value = line_split[1].strip()
                if key == "Type":
                    return value == "RBS"


def get_scatter_element(file: Path) -> Optional[Element]:
    """Check if cut file is RBS.
    
    Args:
        file: A string representing file to be checked.
        
    Return:
        Returns an Element class object of scatter element. Returns an empty 
        Element class object if there is no scatter element (in case of ERD).
    """
    with file.open("r") as cut_file:
        for i, line in enumerate(cut_file):
            if i >= 10:
                return None
            line_split = line.strip().split(':')
            if len(line_split) > 1: 
                key = line_split[0].strip()
                value = line_split[1].strip()
                if key == "Scatter Element":
                    return Element.from_string(value)


def get_rbs_selections(cut_files: List[Path]) -> Dict[str, Element]:
    """Returns a dictionary where keys are cut file names without
    measurement name and values are Elements.

    Args:
        cut_files: list of absolute paths to cut files

    Return:
        dictionary
    """
    rbs_dict = {}
    for cut in cut_files:
        filename = cut.name
        split = filename.split(".")
        if is_rbs(cut):
            # This should work for regular cut and split.
            key = "{0}.{1}.{2}.{3}".format(
                split[1], split[2], split[3], split[4])
            rbs_dict[key] = get_scatter_element(cut)
    return rbs_dict
