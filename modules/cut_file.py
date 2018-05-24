# coding=utf-8
"""
Created on 26.3.2013
Updated on 24.5.2018

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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import os
import pathlib
from modules.element import Element


class CutFile:
    """
    Cut file_path object for when reading cut files is necessary.
    """
    def __init__(self, directory=None, elem_loss=False, weight_factor=1.0, split_number=0, split_count=1):
        """ Inits cut file_path object.
        
        Args:
            directory: String representing cut directory.
            elem_loss: Boolean representing whether cut file_path is made from
                       elemental losses splits.
            weight_factor: Float representing element weight factor. 
            split_number: Integer. Required for Elemental Losses, do not overwrite
                          splits.
            split_count: Integer. Required for Elemental Losses, total count of 
                         splits.
        """
        self.directory = directory
        self.element = None
        self.element_scatter = None
        self.count = 0
        self.is_elem_loss = elem_loss
        self.split_number = split_number
        self.split_count = split_count
        self.type = "ERD"
        self.weight_factor = weight_factor
        self.energy = None
        self.detector_angle = None
        self.data = []
        self.element_number = None
    
    def set_info(self, selection, data):
        """ Set selection information and data into CutFile.
        
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

    def load_file(self, file):
        """Load and parse cut file_path.
        
        Args:
            file: String representing cut file.
        """
        if not file:
            return
        # print("CutFile:load_file() : {0}".format(file))
        directory_cuts, file_name = os.path.split(file)
        self.directory = os.path.split(directory_cuts)[0]
        # os.path is not required for following.
        # Get number of element selection, i.e.
        # Two H selections -> numbers are 0 and 1
        # self.element_number = file.split('/')[-1].split('.')[1]
        # tof_e_01048.Pm.0 << Element count: 0, element_information: Pm
        # tof_e_01048.1H.0.2 << Element count: 0, element_information: 1H
        element_information = file_name.split('.')[1]
        self.element_number = file_name.split('.')[2] 
        
        self.element = Element.from_string(element_information)
        # print("Load cut: {0} {1}".format(self.element, self.isotope))
        with open(file) as fp:
            dirtyinteger = 0
            for line in fp:
                if dirtyinteger < 10:  # Probably not the best way.
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
                            self.is_elem_loss = bool(value)
                        elif key == "Split count":
                            self.split_count = int(value)
                else:
                    self.data.append([int(i) for i in line.split()])
                dirtyinteger += 1
    
    def save(self, element_count=0):
        """Save cut file_path.
        
        Saves data points into cut file_path with meta information.
        
        Args:
            element_count: Integer representing which selection was used of total
                           count of same element and isotope selection. This is so
                           that we do not overwrite first 2H selection with other
                           2H selection.
        """
        if self.element and self.directory and self.data:
            measurement_name_with_prefix = str(pathlib.Path(self.directory).parents[1])
            # First "-" is in sample name, second in measurement name
            measurement_name_start = measurement_name_with_prefix.find(
                "-", measurement_name_with_prefix.find("-") + 1)
            measurement_name = measurement_name_with_prefix[measurement_name_start + 1:]
            if self.is_elem_loss:
                if not os.path.exists(self.directory):
                    os.makedirs(self.directory)
                file = os.path.join(self.directory, "{0}.{1}.{2}.{3}.cut".format(
                                                 measurement_name,
                                                 self.element,
                                                 element_count, self.split_number))
            else:
                if not os.path.exists(self.directory):
                    os.makedirs(self.directory)
                while True:  # Has to run until file that doesn't exist is found.
                    file = os.path.join(self.directory, "{0}.{1}.{2}.cut".format(
                                                 measurement_name,
                                                 self.element, element_count))
                    try:
                        # Using of os.path is not allowed here. 
                        # http://stackoverflow.com/questions/82831/
                        # how-do-i-check-if-a-file-exists-using-python
                        with open(file): 
                            pass
                        element_count += 1
                    except IOError:
                        break
            my_file = open(file, 'wt')
            my_file.write("Count: {0}\n".format(self.count))
            my_file.write("Type: {0}\n".format(self.type))
            my_file.write("Weight Factor: {0}\n".format(self.weight_factor))
            my_file.write("Energy: {0}\n".format(0))
            my_file.write("Detector Angle: {0}\n".format(0))
            my_file.write("Scatter Element: {0}\n".format(self.element_scatter))
            my_file.write("Element losses: {0}\n".format(self.is_elem_loss))
            my_file.write("Split count: {0}\n".format(self.split_count))
            my_file.write("\n")
            my_file.write("ToF, Energy, Event number\n")
            for p in self.data:  # Write all points
                my_file.write(' '.join(map(str, p)))
                my_file.write('\n')
            my_file.close()
         
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
        cut_splits = [[] for unused_i in range(splits)]
        while split < splits and row_index < self_size:
            # Get last event number in first split
            max_event = reference_cut.data[((split + 1) * split_size) - 1][-1]  
            while row_index < self_size and self.data[row_index][-1] <= max_event:
                cut_splits[split].append(self.data[row_index])
                row_index += 1
            split += 1
        if save:
            self.__save_splits(splits, cut_splits)
        return cut_splits

    def __save_splits(self, splits, cut_splits):
        """Save splits into new CutFiles.
        
        Args:
            splits: Integer determining how many splits is cut splitted to.
            cut_splits: List of splitted data.
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
        self.element_scatter = Element(cut_file.element_scatter)


def is_rbs(file):
    """Check if cut file is RBS.
    
    Args:
        file: A string representing file to be checked.
        
    Return:
        Returns True if cut file is RBS and False if not.
    """
    with open(file) as fp:
        dirtyinteger = 0
        for line in fp:
            if dirtyinteger >= 10:
                break
            line_split = line.strip().split(':')
            if len(line_split) > 1: 
                key = line_split[0].strip()
                value = line_split[1].strip()
            if key == "Type":
                return value == "RBS"            
            dirtyinteger += 1
    return False


def get_scatter_element(file):
    """Check if cut file is RBS.
    
    Args:
        file: A string representing file to be checked.
        
    Return:
        Returns an Element class object of scatter element. Returns an empty 
        Element class object if there is no scatter element (in case of ERD).
    """
    with open(file) as fp:
        dirtyinteger = 0
        for line in fp:
            if dirtyinteger >= 10:
                break
            line_split = line.strip().split(':')
            if len(line_split) > 1: 
                key = line_split[0].strip()
                value = line_split[1].strip()
            if key == "Scatter Element":
                return Element(value)
    return None
