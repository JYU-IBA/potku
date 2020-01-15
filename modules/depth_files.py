# coding=utf-8
"""
Created on 5.4.2013
Updated on 28.8.2018

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

DepthFiles.py creates the files necessary for generating depth files.
Also handles several tasks necessary for operating with depth files.
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import math
import os
import platform
import re
import subprocess
from enum import Enum

from modules.general_functions import copy_cut_file_to_temp
from modules.element import Element
import modules.file_parsing as fp
import modules.list_integration as li


class DepthFiles(object):
    """DepthFiles handles calling the external programs to create depth files.
    """

    def __init__(self, file_paths, output_path):
        """Inits DepthFiles.

        Args:
            file_paths: Full paths of cut files to be used.
            output_path: Full path of where depth files are to be created.
        """
        self.__new_cut_files = []
        for cut in file_paths:
            new = copy_cut_file_to_temp(cut)
            self.__new_cut_files.append(new)

        file_paths_str = ' '.join(self.__new_cut_files)

        self.bin_dir = '%s%s%s' % ('external', os.sep, 'Potku-bin')
        self.command_win = 'cd ' + self.bin_dir + ' && tof_list.exe ' \
                           + file_paths_str + ' | erd_depth.exe ' \
                           + output_path + ' tof.in'
        self.command_linux = 'cd ' + self.bin_dir + ' && ./tof_list_linux ' \
                             + file_paths_str + ' | ./erd_depth_linux ' \
                             + output_path + ' tof.in'
        self.command_mac = 'cd ' + self.bin_dir + ' && ./tof_list_mac ' \
                           + file_paths_str + ' | ./erd_depth_mac ' \
                           + output_path + ' tof.in'

    def create_depth_files(self):
        """Generate the files necessary for drawing the depth profile
        """
        used_os = platform.system()

        if used_os == 'Windows':
            subprocess.call(self.command_win, shell=True)
        elif used_os == 'Linux':
            subprocess.call(self.command_linux, shell=True)
        elif used_os == 'Darwin':
            subprocess.call(self.command_mac, shell=True)
        else:
            print('It appears we do no support your OS.')


class DepthProfileType(Enum):
    total = 1
    element = 2


class DepthProfile:
    """Class used in depth profile analysis and graph plotting."""
    def __init__(self, depths, concentrations, absolute_counts, element=None):
        """Inits a new DepthProfile object.

        Args:
            depths: collection of depth values
            concentrations: collection of concentrations on each depth value
            absolute_counts: collections of events on each depth value
                element: element that the depth profile belongs to. If None,
                the depth profile is considered an aggregation of different
                element profiles
        """
        # TODO check that list length match
        # TODO maybe store bin width also
        self.depths = depths
        self.concentrations = concentrations
        self.absolute_counts = absolute_counts
        self.element = element
        self.type = DepthProfileType.element if self.element else \
            DepthProfileType.total

    @classmethod
    def from_file(cls, file_path, element=None):
        """Reads a depth profile from a file and returns it.

        Args:
            file_path: absolute path to a depth file
            element: element that the depth profile belongs to. If None,
                the depth profile is considered to be an aggregation of multiple
                elements
        Returns:
            DepthProfile object
        """
        if element:
            depths, cons, counts = fp.parse_file(
                file_path,
                [0, 3, -1],
                [float, lambda x: float(x) * 100, int])
            return DepthProfile(depths, cons, counts, element=element)

        depths, cons = fp.parse_file(
            file_path,
            [0, 3],
            [float, lambda x: float(x) * 100]
        )
        # TODO maybe add absolute counts for total DepthProfile too
        return DepthProfile(depths, cons, [])

    @classmethod
    def from_files(cls, file_paths, elements):
        """Reads an returns a list of DepthProfiles from depth files.

        Args:
            file_paths: absolute file paths to depth files
            elements: collection of elements that files will be matched to
        Returns:
            List of DepthProfiles. Depth profile is created for each given
            file path.
        """
        # Depth files are named as 'depth.[name of the element]'
        # TODO add exception handling
        elem_strs = (f.split(".")[-1] for f in file_paths)
        matches = dict(match_strs_to_elements(elem_strs, elements))
        profiles = []

        for file_path in file_paths:
            element_part = file_path.split('.')[-1]
            profiles.append(
                DepthProfile.from_file(file_path, element=matches[element_part]))

        return profiles

    def get_profile_name(self):
        """Returns the name of the depth profile.

        Returns:
            string representation of the element or 'total' if element is
                undefined.
        """
        return str(self.element) if self.type == DepthProfileType.element \
            else "total"

    def integrate_concentrations(self, a, b):
        return li.integrate(self.depths, self.concentrations, a, b,
                            t="concentrations") * 0.01  # Divide by 100 to get
                                                        # concentration per
                                                        # cm^2

    def integrate_absolute_counts(self, a, b):
        # TODO
        pass


def extract_from_depth_files(file_paths, elements, x_column, y_column):
    """Extracts two columns from each depth file.

    Args:
        file_paths: List of depth files
        elements: List of used elements
        x_column: Integer of which column is to be extracted for
        graph's x-axis
        y_column: Integer of which column is to be extracted for
        graph's y-axis

    Return:
        List of lists. Each of these lists contains the element
        of the file and two lists for graph plotting.
    """
    # TODO remove this function
    profiles = DepthProfile.from_files(file_paths, elements)
    return [
        [p.get_profile_name(), p.depths, p.concentrations, p.absolute_counts]
        for p in profiles
    ]


def match_strs_to_elements(element_strs, elements):
    """Matches strings to a collection of elements and yields a tuple that
    contains the string and its matching element for each given string.

    Args:
        element_strs: iterable of strings to be matched
        elements: iterable of elements that the strings will be matched to
    Yields:
        tuple that contains the element_str and matched element or None if
        element_str could not be matched
    """
    # TODO move this to general functions or somewhere else
    full = set(str(elem) for elem in elements)
    # TODO maybe allow multiple isotopes of same element to match
    just_symbols = dict((element.symbol, element) for element in elements)

    for elem_str in element_strs:
        if elem_str in full:
            yield elem_str, Element.from_string(elem_str)
        elif elem_str in just_symbols:
            yield elem_str, just_symbols[elem_str]
        else:
            yield elem_str, None


def create_relational_depth_files(read_files):
    """Creates a version of the loaded depth files, which contain
    the value of the y-axis in relation to the .total file's
    y-axis, instead of their absolute values

    Args:
        read_files: The original files with absolute values.

    Return:
        A list filled with relational values in accordance to the
        .total file.
    """
    rel_files = []
    total_file_axe = []
    for file in read_files:
        file_element, axe1, axe2, unused_axe3 = file
        if file_element == 'total':
            total_file_axe = axe2
            break
    for file in read_files:
        file_element, axe1, axe2, axe3 = file
        rel_axe = []
        for i in range(0, len(total_file_axe)):
            division = total_file_axe[i]
            if division != 0:
                rel_val = (axe2[i] / total_file_axe[i]) * 100
            else:
                rel_val = 0
            rel_axe.append(rel_val)
        rel_files.append([file_element, axe1, rel_axe, axe3])
    return rel_files


def merge_files_in_range(file_a, file_b, lim_a, lim_b):
    """Merges two lists that contain n amount of [str,[x],[y]] items.
    When within range [lim_a, lim_b] values from fil_b are used,
    otherwise values from fil_a.

    Args:
        file_a: First file to be merged.
        file_b: Second file to be merged.
        lim_a: The lower limit.
        lim_b: The higher limit.
    Return:
        A merged file.
    """
    file_c = []
    for i in range(len(file_a)):
        item = file_a[i]
        new_item = [item[0], item[1], []]
        for j in range(len(item[1])):
            if lim_a <= item[1][j] <= lim_b:
                new_item[2].append(file_b[i][2][j])
            else:
                new_item[2].append(file_a[i][2][j])
        file_c.append(new_item)
    return file_c


def integrate_lists(depth_files, ignore_elements, lim_a, lim_b,
                    systematic_error):
    """Calculates and returns the relative amounts of values within lists.

    Args:
        depth_files: List of lists containing float values, the first list
        is the one the rest are compared to.
        ignore_elements: A list of elements that are not counted.
        lim_a: The lower limit.
        lim_b: The higher limit.
        systematic_error: A double representing systematic error.

    Return:
        List of lists filled with percentages.
    """
    percentages = {}
    margin_of_errors = {}
    if not depth_files:
        return {}, {}
    # Extract the sum of data point within the [lim_a,lim_b]-range
    total_values = depth_files[0]
    total_values_sum = 0
    skip_values_sum = 0
    for n in range(1, len(total_values[1])):
        curr = total_values[1][n]           # current depth
        prev_val = total_values[2][n - 1]   # value at prev depth
        curr_val = total_values[2][n]       # value at current depth
        if lim_a <= curr <= lim_b:          # calculate running avg and add
            # it to total
            total_values_sum += (prev_val + curr_val) / 2
        elif curr > lim_b:
            total_values_sum += (prev_val + curr_val) / 2
            break
    for element in ignore_elements:
        for i in range(1, len(depth_files)):
            if depth_files[i][0] != element:
                continue
            for n in range(1, len(depth_files[i][1])):
                curr = depth_files[i][1][n]
                prev_val = depth_files[i][2][n - 1]
                curr_val = depth_files[i][2][n]
                if lim_a <= curr <= lim_b:
                    skip_values_sum += (prev_val + curr_val) / 2
                elif curr > lim_b:
                    skip_values_sum += (prev_val + curr_val) / 2
                    break
    total_values_sum -= skip_values_sum

    # Process all elements
    for i in range(1, len(depth_files)):
        element = depth_files[i][0]

        if element in ignore_elements: #TODO ignore_elements should be a set
            percentages[element] = None
            margin_of_errors[element] = None
            continue

        element_x = depth_files[i][1]  # Depth values
        element_y = depth_files[i][2]  # Element concentrations at each depth
        element_e = depth_files[i][3]  # Events at profile depth

        element_conc = []
        element_event = []
        for j in range(1, len(element_x)):
            curr = element_x[j]
            prev_val = element_y[j - 1]
            curr_val = element_y[j]
            if lim_a <= curr <= lim_b:
                element_conc.append((prev_val + curr_val) / 2)
                element_event.append(element_e[j])
            elif curr > lim_b:
                element_conc.append((prev_val + curr_val) / 2)
                element_event.append(element_e[j])
                break
        if total_values_sum == 0.0:
            percentages[element] = 0.0
        else:
            percentages[element] = (sum(element_conc) / total_values_sum) * 100
        if sum(element_event) > 0:
            stat_err = (1 / math.sqrt(sum(element_event))) * percentages[
                element]
        else:
            stat_err = 0
        syst_err = (systematic_error / 100) * percentages[element]
        margin_of_errors[element] = math.sqrt(stat_err * stat_err +
                                              syst_err * syst_err)
    return percentages, margin_of_errors


def get_depth_files(elements, dir_depth, cut_files):
    """Returns a list of depth files in a directory that match the cut files.

    Args:
        elements: List of Element objects that should have a
        corresponding depth file.
        dir_depth: Directory of the erd depth result files.
        cut_files: List of cut files that were used.
    Returns:
        A list of depth files which matched the elements.
    """
    depth_files = ['depth.total']

    # TODO these should probably be sets
    orig_elements = [str(elem) for elem in elements]
    strip_elements = [e.symbol for e in elements]
    for file in os.listdir(dir_depth):
        file_ending = file.split('.')[-1]
        if file_ending in orig_elements:
            depth_files.append(file)
            orig_elements.remove(file_ending)
            stripped = re.sub("\d+", "", file_ending)
            strip_elements.remove(stripped)
        else:
            if file_ending in strip_elements:
                depth_files.append(file)
                index = strip_elements.index(file_ending)
                orig_elements.remove(orig_elements[index])
                strip_elements.remove(file_ending)

    return depth_files


if __name__ == "__main__":
    # for testing purposes
    from timeit import default_timer as timer

    elems = [
        Element.from_string("12C"),
        Element.from_string("12C"),
        Element.from_string("16O"),
        Element.from_string("19F"),
        Element.from_string("1H"),
        Element.from_string("2H"),
        Element.from_string("Mn"),
        Element.from_string("6Li"),
        Element.from_string("7Li"),
        Element.from_string("Mn"),
        Element.from_string("Re"),
        Element.from_string("Si")
    ]
    dir_path = os.path.abspath("..\\..\\requests\\gradu_testi.potku\\Sample_01"
                               "-s1\\Measurement_01-m1\\Depth_profiles\\")

    print(dir_path)
    start = timer()
    fpaths = [os.path.join(dir_path, f) for f in get_depth_files(
        elems, dir_path, [])]
    stop = timer()
    print(stop - start, " seconds to get depth files")

    x_col = 0
    y_col = 3

    start = timer()

    df = extract_from_depth_files(fpaths, elems, x_col, y_col)

    stop = timer()
    print(stop - start, " seconds to read depth files")
    print(df)

    # replace the value of exp with expected values to test extraction
    exp = []

    for x, e in zip(df, exp):
        if x != e:
            print("here")

    print(exp == df)
