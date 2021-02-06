# coding=utf-8
"""
Created on 5.4.2013
Updated on 20.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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

depth_files.py contains classes to deal with depth files:
    DepthFileGenerator runs c-components to generate the files
    DepthProfile reads and calculates statistics from the files
    DepthProfileHandler manages multiple DepthProfiles
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import math
import os
import platform
import subprocess
import logging
import functools

from pathlib import Path
from typing import Optional
from typing import List

from . import math_functions as mf
from . import comparison as comp
from . import general_functions as gf
from .element import Element
from .parsing import CSVParser
from .measurement import Measurement
from .observing import ProgressReporter
from .enums import DepthProfileUnit


class DepthFileGenerator:
    """DepthFiles handles calling the external programs to create depth files.
    """
    DEPTH_PREFIX = "depth"

    def __init__(self, cut_files: List[Path], output_directory: Path,
                 prefix: str = DEPTH_PREFIX, tof_in_file: Optional[Path] =
                 None):
        """Inits DepthFiles.

        Args:
            cut_files: file paths of cut files to be used.
            output_directory: path to the directory where depth files are to be
                created.
            tof_in_file: path to tof.in file
        """
        self._cut_files = cut_files
        self._output_path = Path(output_directory, prefix)
        if tof_in_file is None:
            self._tof_in_file = Path("tof.in")
        else:
            self._tof_in_file = tof_in_file

    def get_command(self):
        """Returns the command(s) used to run both tof_list and erd_depth.
        """
        if platform.system() == "Windows":
            tof_bin = str(gf.get_bin_dir() / "tof_list.exe")
            erd_bin = str(gf.get_bin_dir() / "erd_depth.exe")
        else:
            tof_bin = "./tof_list"
            erd_bin = "./erd_depth"

        return (tof_bin, str(self._tof_in_file),
                *(str(f) for f in self._cut_files)), \
               (erd_bin, str(self._output_path), str(self._tof_in_file))

    def run(self):
        """Generate the files necessary for drawing the depth profile.
        """
        bin_dir = gf.get_bin_dir()
        tof, erd = self.get_command()
        # Pipe the output from tof_list to erd_depth
        tof_process = subprocess.Popen(tof, cwd=bin_dir, stdout=subprocess.PIPE)
        ret = subprocess.run(
            erd, cwd=bin_dir, stdin=tof_process.stdout).returncode
        if ret != 0:
            print(f"tof_list|erd_depth pipeline returned an error code: {ret}")


def generate_depth_files(cut_files: List[Path], output_dir: Path,
                         measurement: Measurement, tof_in_dir: Optional[Path]
                         = None, progress: Optional[ProgressReporter] = None):
    """Generates depth files from given cut files and writes them to output
    directory.

    Deletes any previous depth files in the given directory

    Args:
        cut_files: list of file paths to .cut files
        output_dir: directory where the depth files will be generated
        measurement: Measurement object to generate tof.in
        tof_in_dir: directory in which the tof.in is to be generated.
        progress: a ProgressReporter object
    """
    # TODO this could be a method of Measurement
    tof_in_file = measurement.generate_tof_in(directory=tof_in_dir)

    output_dir.mkdir(exist_ok=True)

    # Delete previous depth files to avoid mixup when assigning the
    # result files back to their cut files
    gf.remove_matching_files(
        output_dir,
        filter_func=lambda fn: Path(fn).stem == DepthFileGenerator.DEPTH_PREFIX)

    if progress is not None:
        progress.report(30)

    dp = DepthFileGenerator(cut_files, output_dir, tof_in_file=tof_in_file)
    dp.run()

    if progress is not None:
        progress.report(100)


class DepthProfile:
    """Class used in depth profile analysis and graph plotting."""
    def __init__(self, depths, concentrations, events=None, element=None):
        """Inits a new DepthProfile object.

        DepthProfile contains element concentrations at each depth level. If
        the profile represents data from a single element, it also has to have
        event counts for each depth.

        If the profile represents multiple elements, both events must be None.
        This is because the 'depth.total' file generated by the
        DepthProfileGenerator does not store event counts.

        Args:
            depths: collection of depth values
            concentrations: collection of concentrations at each depth value
            events: collection of event counts at each depth value
            element: Element that the depth profile belongs to. If None,
                     the depth profile is considered an aggregation of different
                     profiles
        """
        # TODO binary operations (__add__, merge, etc) could raise exception
        #      when depths of the two DepthProfiles do not line up
        if element is not None:
            if not isinstance(element, Element):
                raise TypeError("element should either be an Element or None")

            if events is None:
                raise ValueError("Element DepthProfile must have event counts")

            if not (len(depths) == len(concentrations) == len(events)):
                raise ValueError("All profile lists must have same size")
        else:
            if events is not None:
                raise ValueError("Total type depth profile does not have event"
                                 " counts")

            if not (len(depths) == len(concentrations)):
                raise ValueError("DepthProfile must have same number of depths "
                                 "and concentrations")

        self.depths = tuple(depths)
        self.concentrations = tuple(concentrations)

        if events is not None:
            events = tuple(events)
        self.events = events
        self.element = element

    def __iter__(self):
        """Iterates over depths, concentrations and event counts

        Yield:
            tuple that contains a depth value, and DepthProfile's
            concentration and event count at that depth.
        """
        if self.element is None:
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
            a new total type DepthProfile.
        """
        if not isinstance(other, DepthProfile):
            return NotImplemented

        if len(self) != len(other):
            raise ValueError("DepthProfile lengths must match when adding")

        conc = tuple(c1 + c2 for (_, c1, _), (_, c2, _)
                     in zip(self, other))

        return DepthProfile(self.depths, conc)

    def __sub__(self, other):
        """Subtracts concentrations of other DepthProfile from
        self.

        Args:
            other: another DepthProfile

        Return:
            a new total type DepthProfile
        """
        if not isinstance(other, DepthProfile):
            return NotImplemented

        if len(self) != len(other):
            raise ValueError("DepthProfile lengths must match when subtracting")

        conc = tuple(c1 - c2 for (_, c1, _), (_, c2, _)
                     in zip(self, other))

        return DepthProfile(self.depths, conc)

    def __len__(self):
        """Lengths of the DepthProfile is the length of its
        depth values."""
        return len(self.depths)

    @classmethod
    def from_file(
            cls,
            file_path: Path,
            element: Optional[Element] = None,
            depth_units: DepthProfileUnit = DepthProfileUnit.NM) -> "DepthProfile":
        """Reads a depth profile from a file and returns it.

        Args:
            file_path: absolute path to a depth file
            element: element that the depth profile belongs to. If None,
                     the depth profile is considered to be an aggregation
                     of multiple elements
            depth_units: unit in which depths are measured

        Return:
            DepthProfile object
        """
        if depth_units == DepthProfileUnit.NM:
            x_column = 2
        else:
            x_column = 0

        if element is not None:
            # If element is defined, read event counts too
            parser = CSVParser((x_column, float),
                               (3, lambda x: float(x) * 100),
                               (-1, int))
            depths, conc, events = tuple(parser.parse_file(file_path,
                                                           method="col"))
            return cls(depths, conc, events, element=element)

        # Otherwise read just depths and concentrations
        parser = CSVParser((x_column, float),
                           (3, lambda x: float(x) * 100))
        depths, conc = tuple(parser.parse_file(file_path, method="col"))
        return cls(depths, conc)

    def get_profile_name(self):
        """Returns the name of the depth profile.

        Return:
            string representation of the element or 'total' if element
            is undefined.
        """
        return str(self.element) if self.element else "total"

    def get_depth_range(self):
        """Returns minimum and maximum depths of the DepthProfile

        Return:
            minimum and maximum depths as a tuple of floats or
            (None, None) if no depth values are stored.
        """
        if len(self.depths) == 0:
            return None, None
        return self.depths[0], self.depths[-1]

    def integrate_concentrations(self, depth_a=-math.inf, depth_b=math.inf):
        """Returns sum of concentrations between depths a and b.

        Args:
            depth_a: lower limit of the integration range depth value
            depth_b: upper limit of the integration range depth value

        Return:
            concentration per cm^2 as a float.
        """
        # Multiply by 0.01 to get concentration per cm^2
        return mf.integrate_bins(
            self.depths, self.concentrations, a=depth_a, b=depth_b) * 0.01

    def sum_running_avgs(self, depth_a=-math.inf, depth_b=math.inf):
        """Returns the sum of running concentration averages between
        depths a and b.

        Args:
            depth_a: first depth value to include in average
            depth_b: last depth value to include in average

        Return:
            sum of running concentration averages as a float.
        """
        return mf.sum_running_avgs(
            self.depths, self.concentrations, a=depth_a, b=depth_b)

    def sum_events(self, depth_a=-math.inf, depth_b=math.inf):
        """Returns the sum of events between depths a and b.

        Args:
            depth_a: first depth value to include in sum
            depth_b: last depth value to include in sum

        Return:
            sum of events as int.
        """
        return int(mf.sum_y_values(
            self.depths, self.events, a=depth_a, b=depth_b))

    def get_relative_concentrations(self, other):
        """Calculates the concentrations relative to another DepthProfile

        Args:
            other: other DepthProfile object

        Return:
            list of relative concentrations
        """
        if not isinstance(other, DepthProfile):
            return NotImplemented

        if len(self) != len(other):
            raise ValueError("DepthProfile lengths must match when "
                             "calculating relative concentrations")

        conc = tuple(c1 / c2 * 100 if c2 != 0 else 0.0
                     for (_, c1, _), (_, c2, _) in zip(self, other))

        return DepthProfile(
            self.depths, conc, events=self.events, element=self.element)

    def merge(self, other, depth_a=-math.inf, depth_b=math.inf):
        """Merges DepthProfile with another instance of DepthProfile.
        Concentrations outside the range between depths a and b are taken
        from this DepthProfile, concentrations inside the range are taken
        from other DepthProfile.

        New DepthProfile is created and the merged DepthProfiles remain
        unchanged.

        Args:
            other: another DepthProfile to merge with
            depth_a: depth value at which merging begins
            depth_b: depth value at which merging ends

        Return:
            new DepthProfile object.
        """
        if not isinstance(other, DepthProfile):
            return NotImplemented

        if len(self) != len(other):
            raise ValueError("DepthProfile lengths must match when merging")

        conc = tuple(c2 if depth_a <= d <= depth_b else c1
                     for (d, c1, _), (_, c2, _)
                     in zip(self, other))

        if self.element and self.element == other.element:
            events = self.events
            elem = self.element
        else:
            events = None
            elem = None

        return DepthProfile(self.depths, conc, events=events, element=elem)

    def calculate_margin_of_error(self, systematic_error, depth_a=-math.inf,
                                  depth_b=math.inf, sum_of_running_avgs=None):
        """Calculates the margin of error for given range of values and
        systematic error.

        Args:
            systematic_error: systematic error used in calculation
            depth_a: lowest depth value to include in calculation
            depth_b: highest depth value to include in calculation
            sum_of_running_avgs: if not given, DepthProfile calculates
                                 the average itself

        Return:
            margin of error as float
        """
        event_count = self.sum_events(depth_a, depth_b)

        if sum_of_running_avgs is None:
            sra = self.sum_running_avgs(depth_a, depth_b)
        else:
            sra = sum_of_running_avgs

        if event_count > 0:
            stat_err = (1 / math.sqrt(event_count)) * sra
        else:
            stat_err = 0.0

        syst_err = (systematic_error / 100) * sra
        return math.sqrt(stat_err * stat_err + syst_err * syst_err)


def validate_depth_file_names(file_names):
    """Checks that a list of strings is in the expected
    format of depth.[element name or total]. Valid values
    are returned as a dictionary.

    Note that the function does not check if the string
    is actually a valid file name.

    Args:
        file_names: iterable of strings.

    Return:
        dictionary that has the element names as keys and
        valid file names as values
    """
    def splitter_function(file_name):
        # Splitter function splits the function into
        # full name and element name, as long as the
        # name is in format 'depth.[element]'
        if not file_name.startswith("depth."):
            return None, None
        parts = file_name.split(".")
        if len(parts) != 2 or parts[1] == "":
            return None, None
        return file_name, parts[-1]

    # Use the function to create a file name splitting generator
    split_generator = (splitter_function(f) for f in file_names)

    # Use list comprehension to create a dict that contains only
    # valid depth files and elements
    return {
        elem: fname for (fname, elem) in split_generator if fname
    }


def get_depth_files(elements, dir_depth):
    """Returns a list of depth files in a directory that match the
    elements.

    Args:
        elements: List of Element objects that should have a
                  corresponding depth file.
        dir_depth: Directory of the erd depth result files.

    Return:
        A list of full depth file paths which matched the given
        elements.
    """
    # Check which file paths in the director are valid depth file paths
    file_paths = os.listdir(dir_depth)
    validated_filenames = validate_depth_file_names(file_paths)

    # By default, add 'depth.total' to the list
    depth_files = [Path(dir_depth, "depth.total")]
    for s, elem in comp.match_strs_to_elements(
            validated_filenames.keys(), elements):
        # Add all file names that matched an element in the element collection
        if elem:
            depth_files.append(Path(dir_depth, validated_filenames[s]))

    return depth_files


class DepthProfileHandler:
    """Handles multiple DepthProfiles. Keeps a dictionary of absolute
    and corresponding relative DepthProfiles."""
    def __init__(self):
        """Inits a new DepthProfileHandler
        """
        self.__absolute_profiles = {}
        self.__relative_profiles = {}

    def read_directory(
            self,
            directory_path: Path,
            elements,
            depth_units: DepthProfileUnit = DepthProfileUnit.NM):
        """Reads depth files from the given directory that match the given
        set of elements and stores them internally as DepthProfiles.

        Currently stored profiles will be removed.

        Args:
            directory_path: absolute path to a directory that contains
                            depth files
            elements: collection of elements that will be matched to
                      depth files
            depth_units: unit in which depths are measured
        """
        file_paths = get_depth_files(elements, directory_path)
        self.read_files(file_paths, elements, depth_units=depth_units)

    def read_files(
            self,
            file_paths,
            elements,
            depth_units: DepthProfileUnit = DepthProfileUnit.NM,
            logger_name=None):
        """Reads depth files from given list of file paths that
        match the given set of elements.

        Currently stored profiles will be removed.

        Args:
            file_paths: absolute paths to depth files
            elements: collection of elements that will be matched to
                      depth files
            depth_units: unit in which depths are measured
            logger_name: name of a Logger entity that will be used to create a
                         log message if something goes wrong when reading files
        """
        # Clear currently stored profiles and cache for merging
        self.merge_profiles.cache_clear()
        self.__absolute_profiles.clear()
        self.__relative_profiles.clear()

        # Depth files are named as 'depth.[name of the element]'
        elem_strs = (f.name.split(".")[-1] for f in file_paths)

        # Match each 'depth' file to an element
        matches = dict(comp.match_strs_to_elements(elem_strs, elements))

        for file_path in file_paths:
            # Read files and generate DepthProfiles
            element_part = file_path.name.split('.')[-1]

            try:
                profile = DepthProfile.from_file(
                    file_path, element=matches[element_part],
                    depth_units=depth_units)

                self.__absolute_profiles[profile.get_profile_name()] = profile

            except Exception as e:
                if logger_name is not None:
                    logging.getLogger(logger_name).info(
                        f"Could not create depth profiled .depth file: {e}")

    def get_depth_range(self):
        """Returns the minimum and maximum depth values in the total depth
        profile.

        Return:
            tuple of floats or (None, None) if handler does not have total
            depth profile
        """
        if "total" in self.__absolute_profiles:
            return self.__absolute_profiles["total"].get_depth_range()
        return None, None

    def get_absolute_profiles(self):
        """Returns DepthProfiles with absolute concentrations.

        Return:
            dictionary where keys are the names of the DepthProfiles
            and values are DepthProfiles.
        """
        return self.__absolute_profiles

    def get_relative_profiles(self):
        """Returns DepthProfiles relative to the total DepthProfile.

        Return:
            dictionary where keys are the names of the DepthProfiles
            and values are DepthProfiles.
        """
        # If relative profiles have not yet been calculated, they are now
        if not self.__relative_profiles:
            if "total" in self.__absolute_profiles:
                # Relative profiles are created in relation to the total
                # profile
                total_profile = self.__absolute_profiles["total"]
                self.__relative_profiles = {
                    p: self.__absolute_profiles[p].get_relative_concentrations(
                        total_profile)
                    for p in self.__absolute_profiles if p != "total"
                }

        return self.__relative_profiles

    # It is likely that this function gets called many times with same args so
    # results are cached
    @functools.lru_cache(maxsize=32)
    def merge_profiles(self, depth_a=-math.inf, depth_b=math.inf,
                       method="abs_rel_abs"):
        """Combines absolute and relative DepthProfiles so that
        concentrations outside the range between depth_a and depth_b
        are taken from one profile and concentrations inside the range
        are taken from another profile.

        Whether absolute values are outside and relative values are inside
        the range or vice versa depends on the given method.

        Args:
            depth_a: depth value where merging begins
            depth_b: depth value where merging ends
            method: either 'abs_rel_abs' or 'rel_abs_rel' depending
                    on how the profiles should be merged

        Return:
            dictionary where keys are the names of the DepthProfiles
            and values are DepthProfiles.
        """
        # Do this to calculate the relative profiles first
        rel = self.get_relative_profiles()

        if method == "abs_rel_abs":
            return {
                p: self.__absolute_profiles[p].merge(rel[p],
                                                     depth_a,
                                                     depth_b)
                for p in self.__absolute_profiles if p != "total" and p in rel
            }

        if method == "rel_abs_rel":
            return {
                p: rel[p].merge(self.__absolute_profiles[p],
                                depth_a,
                                depth_b)
                for p in rel if p != "total" and p in self.__absolute_profiles
            }

        raise ValueError("Unknown merge method")

    def calculate_ratios(self, ignored, depth_a=-math.inf, depth_b=math.inf,
                         systematic_error=3.0):
        """Calculates the ratios and margins of error for DepthProfiles
        currently stored in the DepthProfileHandler.

        Args:
            ignored: set of DepthProfile names that will be ignored from
                     calculations
            depth_a: lowest depth value that is included in the ratio
                     calculation
            depth_b: highest depth value that is included in the ratio
                     calculation
            systematic_error: systematic error used in calculation

        Return:
            tuple of two dictionaries, first of which contains the
            names and ratios of the DepthProfiles, second of which
            contains the margins of error at given systematic error
            for each ratio calculation.
        """
        if "total" in self.__absolute_profiles:
            total_profile = self.__absolute_profiles["total"]
        else:
            return {}, {}

        total_sum = total_profile.sum_running_avgs(depth_a, depth_b)

        # TODO seems unnecessary to calculate the ignored values
        ignored_profiles = {
            p: self.__absolute_profiles[p]
            for p in self.__absolute_profiles
            if p in ignored and p != "total"
        }
        total_sum -= sum(p.sum_running_avgs(depth_a, depth_b)
                         for p in ignored_profiles.values())

        percentages = {}
        moes = {}
        for profile_name in self.__absolute_profiles:
            if profile_name == "total":
                continue
            if profile_name in ignored_profiles:
                percentages[profile_name] = None
                moes[profile_name] = None
                continue

            profile = self.__absolute_profiles[profile_name]

            if total_sum == 0:
                percentages[profile_name] = 0.0
            else:
                percentages[profile_name] = \
                    profile.sum_running_avgs(depth_a, depth_b) \
                    / total_sum * 100

            # Calculate margin of errors for depth profile with given
            # systematic error
            profile_moe = profile.calculate_margin_of_error(
                systematic_error, depth_a, depth_b,
                sum_of_running_avgs=percentages[profile_name])
            moes[profile_name] = profile_moe

        return percentages, moes

    def integrate_concentrations(self, depth_a=-math.inf, depth_b=math.inf):
        """Calculates an integral of the total amount of concentrations
        between the given depth range.

        Args:
            depth_a: lowest depth value included in range
            depth_b: highest depth value included in range

        Return:
            dictionary where keys are the names of the DepthProfiles and
            values are integrals of their concentrations.
        """
        return {
            p: self.__absolute_profiles[p].integrate_concentrations(
                depth_a, depth_b)
            for p in self.__absolute_profiles if p != "total"
        }
