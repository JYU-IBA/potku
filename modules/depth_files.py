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
import modules.file_parsing as fp
import modules.list_integration as li

from modules.general_functions import copy_cut_file_to_temp, \
                                      match_strs_to_elements
from modules.element import Element


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


class DepthProfile:
    """Class used in depth profile analysis and graph plotting."""
    def __init__(self, depths, concentrations, events=None, element=None):
        """Inits a new DepthProfile object.

        Args:
            depths: collection of depth values
            concentrations: collection of concentrations at each depth value
            events: collections of event counts at each depth value
            element: element that the depth profile belongs to. If None,
                     the depth profile is considered an aggregation of different
                     element profiles
        """
        # TODO use tuples or numpy arrays instead of lists
        # TODO check that depths are in order and values are numerical
        # TODO maybe clone input collections
        # TODO profile could have other types (relational, merged etc.)
        if element:
            if not (len(depths) == len(concentrations) == len(events)):
                raise ValueError("All profile lists must have same size")
        else:
            # Total type DepthProfile does should not have absolute counts
            # as they are not stored in depth.total files
            if not (len(depths) == len(concentrations)):
                raise ValueError("All profile lists must have same size")
            if events:
                raise ValueError("Total type depth profile does not have event"
                                 " counts")

        self.depths = depths
        self.concentrations = concentrations
        self.events = events
        self.element = element

    def __iter__(self):
        """Iterates over depths, concentrations and event counts

        Yield:
            tuple that contains a depth value, and DepthProfile's
            concentration and event counts at that depth.
        """
        if not self.element:
            for d, c in zip(self.depths, self.concentrations):
                # For total type profiles, event count is always 0
                yield d, c, 0
        else:
            for d, c, e in zip(self.depths, self.concentrations, self.events):
                yield d, c, e

    def __add__(self, other):
        """Adds concentrations of another depth profile to self concentrations
        and returns new DepthProfile.

        Args:
            other: another DepthProfile

        Return:
            DepthProfile
        """
        conc = [c1 + c2 for (_, c1, _), (_, c2, _)
                in zip(self, other)]
        return DepthProfile(self.depths, conc)

    def __sub__(self, other):
        """Subtracts concentrations of other DepthProfile from
        self.

        Args:
            other: another DepthProfile

        Return:
            DepthProfile
        """
        conc = [c1 - c2 for (_, c1, _), (_, c2, _)
                in zip(self, other)]
        return DepthProfile(self.depths, conc)

    def __str__(self):
        return str([
            self.get_profile_name(),
            self.depths,
            self.concentrations,
            self.events
        ])

    @classmethod
    def from_file(cls, file_path, element=None):
        """Reads a depth profile from a file and returns it.

        Args:
            file_path: absolute path to a depth file
            element: element that the depth profile belongs to. If None,
                     the depth profile is considered to be an aggregation of
                     multiple elements
        Return:
            DepthProfile object
        """
        if element:
            depths, cons, events = fp.parse_file(
                file_path,
                [0, 3, -1],
                [float, lambda x: float(x) * 100, int])
            return DepthProfile(depths, cons, events, element=element)

        depths, cons = fp.parse_file(
            file_path,
            [0, 3],
            [float, lambda x: float(x) * 100])
        return DepthProfile(depths, cons)

    @classmethod
    def from_files(cls, file_paths, elements):
        """Reads and returns a list of DepthProfiles from depth files.

        Args:
            file_paths: absolute file paths to depth files
            elements: collection of elements that files will be matched to
        Return:
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

        Return:
            string representation of the element or 'total' if element is
            undefined.
        """
        return str(self.element) if self.element else "total"

    def get_depth_range(self):
        """Returns minimum and maximum depths of the DepthProfile

        Return:
            tuple of floats
        """
        return self.depths[0], self.depths[-1]

    def integrate_concentrations(self, depth_a, depth_b):
        """Returns sum of concentrations between depths a and b.

        Args:
            depth_a: depth value
            depth_b: depth value

        Return:
            concentration per cm^2 as a float
        """
        # Multiply by 0.01 to get concentration per cm^2
        return li.integrate_bins(
            self.depths, self.concentrations, depth_a, depth_b) * 0.01

    def sum_running_avgs(self, depth_a, depth_b):
        """TODO"""
        return li.sum_running_avgs(
            self.depths, self.concentrations, depth_a, depth_b
        )

    def sum_events(self, depth_a, depth_b):
        """Returns the sum of events between depths a and b.

        Args:
            depth_a: first depth value to include in sum
            depth_b: last depth value to include in sum

        Return:
            sum of events
        """
        return int(li.sum_elements(self.depths, self.events, depth_a, depth_b))

    def get_relative_concentrations(self, other):
        """Calculates the concentrations relative to another DepthProfile

        Args:
            other: other DepthProfile object

        Return:
            list of relative concentrations
        """
        # TODO error handling if other and self are not same size, or
        #      or depths do not match
        conc = [c1 / c2 * 100 if c2 != 0 else 0.0
                for (_, c1, _), (_, c2, _) in zip(self, other)]
        return DepthProfile(
            self.depths, conc, events=self.events, element=self.element)

    def merge(self, other, depth_a, depth_b):
        """Merges the DepthProfile with other DepthProfile so that
        concentrations are taken from

        New total type DepthProfile is created and the merged DepthProfiles
        remain same.

        Args:
            other: another DepthProfile to merge with
            depth_a: depth value from which TODO
            depth_b: depth value from which TODO

        Return:
            new DepthProfile
        """
        # TODO check that depths match
        conc = [c2 if depth_a <= d <= depth_b else c1
                for (d, c1, _), (_, c2, _)
                in zip(self, other)]

        if self.element and self.element == other.element:
            elem = self.element
        else:
            elem = None

        events = self.events if elem else None
        return DepthProfile(
            self.depths, conc, events=events, element=elem)

    def calculate_margin_of_error(self, systematic_error, lim_a, lim_b,
                                  sum_of_running_avgs=None):
        """TODO"""
        event_count = self.sum_events(lim_a, lim_b)

        if not sum_of_running_avgs:
            sra = self.sum_running_avgs(lim_a, lim_b)
        else:
            sra = sum_of_running_avgs

        if event_count > 0:
            stat_err = (1 / math.sqrt(event_count)) * sra
        else:
            stat_err = 0.0

        syst_err = (systematic_error / 100) * sra
        return math.sqrt(stat_err * stat_err + syst_err * syst_err)

    def get_previous_fmt(self):
        """Returns the profile in the same data structure as was
        previously used. This is a temporary solution to maintain
        backwards compatibility during rewrite."""
        return [
            self.get_profile_name(),
            self.depths,
            self.concentrations,
            self.events
        ]


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
    # TODO test new merge implementation before removing this
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


def integrate_profiles(depth_profiles, lim_a, lim_b):
    return sum(dp.sum_running_avgs(lim_a, lim_b)
               for dp in depth_profiles)


def _integrate_lists(depth_profiles, ignored_profiles, total, lim_a, lim_b,
                     systematic_error):
    """TODO"""
    total_sum = total.sum_running_avgs(lim_a, lim_b)
    total_sum -= integrate_profiles(ignored_profiles, lim_a, lim_b)
    ignored = set(dp.get_profile_name() for dp in ignored_profiles)

    percentages = {}
    moes = {}
    for dp in depth_profiles:
        if dp.get_profile_name() == "total":
            continue
        if dp.get_profile_name() in ignored:
            percentages[dp.get_profile_name()] = None
            moes[dp.get_profile_name()] = None
            continue

        if total_sum == 0:
            percentages[dp.get_profile_name()] = 0.0
        else:
            percentages[dp.get_profile_name()] = \
                dp.sum_running_avgs(lim_a, lim_b) \
                / total_sum * 100

        # Calculate margin of errors for depth profile with given systematic
        # error
        dp_moe = dp.calculate_margin_of_error(
            systematic_error, lim_a, lim_b,
            sum_of_running_avgs=percentages[dp.get_profile_name()])
        moes[dp.get_profile_name()] = dp_moe

    return percentages, moes


def sanitize_depth_file_names(file_names):
    """Checks that a list of strings is in the expected
    format of depth.[element name or total]. Valid values
    are returned as a dictionary.

    Note that the function does not check if the string
    is actually a valid file name.

    Args:
        file_names: iterable of strings.

    Return:
        dict that has the element names as keys and
        valid file names as values
    """
    def splitter_function(file_name):
        # Splitter function splits the function into
        # full name and element name, as long as the
        # name is in format 'depth.[element]'
        if not file_name.startswith("depth"):
            return None, None
        parts = file_name.split(".")
        if len(parts) != 2:
            return None, None
        return file_name, parts[-1]

    # Use the function to create a file name splitting generator
    split_generator = (splitter_function(f) for f in file_names)

    # Use list comprehension to create a dict that contains only
    # valid depth files and elements
    return {
        elem: fname for (fname, elem) in split_generator if fname
    }


def get_depth_files(elements, dir_depth, cut_files):
    """Returns a list of depth files in a directory that match the cut files.

    Args:
        elements: List of Element objects that should have a
                  corresponding depth file.
        dir_depth: Directory of the erd depth result files.
        cut_files: List of cut files that were used.

    Return:
        A list of depth files which matched the elements.
    """
    # TODO implement or remove cut_files parameter

    # Check which file paths in the director are valid depth file paths
    file_paths = os.listdir(dir_depth)
    sanitized_files = sanitize_depth_file_names(file_paths)

    # By default, add 'depth.total' to the list
    depth_files = ["depth.total"]
    for s, elem in match_strs_to_elements(sanitized_files.keys(), elements):
        # Add all file names that matched an element in the element collection
        if elem:
            depth_files.append(sanitized_files[s])

    return depth_files


class DepthProfileHandler:
    def __init__(self):
        self.depth_profiles = {}
        self.relative_profiles = {}
        self.hybrid_profiles = {}

    def read_directory(self, directory_path, elements):
        file_paths = get_depth_files(elements, directory_path, [])
        self.read_files(file_paths, elements)

    def read_files(self, file_paths, elements):
        self.depth_profiles = {
            dp.get_profile_name(): dir_path
            for dp in DepthProfile.from_files(file_paths, elements)
        }

    def integrate_profiles(self, ignored, depth_a, depth_b):
        ignored_dict = self.depth_profiles.fromkeys(ignored)
        return _integrate_lists(
            self.depth_profiles.values(), ignored_dict, depth_a, depth_b)

    def get_depth_range(self):
        """Returns the minimum and maximum depth values in the total depth
        profile.

        Return:
            tuple of floats or (None, None) if handler does not have total
            depth profile
        """
        if "total" in self.depth_profiles:
            return self.depth_profiles["total"].get_depth_range()
        return None, None

    def remove(self, profile_name):
        try:
            del(self.depth_profiles[profile_name])
        except KeyError:
            # Tried to remove nonexistent DepthProfile
            pass


if __name__ == "__main__":
    # for testing purposes
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

    fpaths = [os.path.join(dir_path, f) for f in get_depth_files(
        elems, dir_path, [])]

    profiles = DepthProfile.from_files(fpaths, elems)
    old_profiles = [p.get_previous_fmt() for p in profiles]
    new_integration, new_moe = _integrate_lists(
        profiles, {},
        next(p for p in profiles if p.get_profile_name() == "total"),
        0, 1000, 0.5)

    profiles = DepthProfile.from_files(fpaths, elems)
    total = next(p for p in profiles if p.get_profile_name() == "total")

    new_rel = {
        p.get_profile_name(): p.get_relative_concentrations(total). \
                              get_previous_fmt()
        for p in profiles
    }
