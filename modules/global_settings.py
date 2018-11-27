# coding=utf-8
"""
Created on 29.4.2013
Updated on 27.11.2018

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

import configparser
import os


class GlobalSettings:
    """Global settings class to handle software settings.
    """

    def __init__(self):
        """Inits GlobalSettings class.
        """
        self.__config_directory = os.path.join(os.path.expanduser("~"), "potku")
        self.__config_file = os.path.join(self.__config_directory, "potku2.ini")  # Number according to release!
        self.__config = configparser.ConfigParser()

        self.__request_directory = os.path.join(self.__config_directory,
                                             "requests")
        self.__make_directories(self.__config_directory)
        self.__make_directories(self.__request_directory)

        self.__request_directory_last_open = self.__request_directory
        self.__element_colors = {"H": "#b4903c",
                                 "He": "red",
                                 "Li": "red",
                                 "Be": "red",
                                 "B": "red",
                                 "C": "#513c34",
                                 "N": "red",
                                 "O": "#0000ff",
                                 "F": "red",
                                 "Ne": "red",
                                 "Na": "red",
                                 "Mg": "red",
                                 "Al": "red",
                                 "Si": "#800080",
                                 "P": "red",
                                 "S": "red",
                                 "Cl": "red",
                                 "Ar": "red",
                                 "K": "red",
                                 "Ca": "red",
                                 "Sc": "red",
                                 "Ti": "red",
                                 "V": "red",
                                 "Cr": "red",
                                 "Mn": "red",
                                 "Fe": "red",
                                 "Co": "red",
                                 "Ni": "red",
                                 "Cu": "red",
                                 "Zn": "red",
                                 "Ga": "red",
                                 "Ge": "red",
                                 "As": "red",
                                 "Se": "red",
                                 "Br": "red",
                                 "Kr": "red",
                                 "Rb": "red",
                                 "Sr": "red",
                                 "Y": "red",
                                 "Zr": "red",
                                 "Nb": "red",
                                 "Mo": "red",
                                 "Tc": "red",
                                 "Ru": "red",
                                 "Rh": "red",
                                 "Pd": "red",
                                 "Ag": "red",
                                 "Cd": "red",
                                 "In": "red",
                                 "Sn": "red",
                                 "Sb": "red",
                                 "Te": "red",
                                 "I": "red",
                                 "Xe": "red",
                                 "Cs": "red",
                                 "Ba": "red",
                                 "La": "red",
                                 "Ce": "red",
                                 "Pr": "red",
                                 "Nd": "red",
                                 "Pm": "red",
                                 "Sm": "red",
                                 "Eu": "red",
                                 "Gd": "red",
                                 "Tb": "red",
                                 "Dy": "red",
                                 "Ho": "red",
                                 "Er": "red",
                                 "Tm": "red",
                                 "Yb": "red",
                                 "Lu": "red",
                                 "Hf": "red",
                                 "Ta": "red",
                                 "W": "red",
                                 "Re": "red",
                                 "Os": "red",
                                 "Ir": "red",
                                 "Pt": "red",
                                 "Au": "red",
                                 "Hg": "red",
                                 "Tl": "red",
                                 "Pb": "red",
                                 "Bi": "red",
                                 "Po": "red",
                                 "At": "red",
                                 "Rn": "red",
                                 "Fr": "red",
                                 "Ra": "red",
                                 "Ac": "red",
                                 "Th": "red",
                                 "Pa": "red",
                                 "U": "red",
                                 "Np": "red",
                                 "Pu": "red",
                                 "Am": "red",
                                 "Cm": "red",
                                 "Bk": "red",
                                 "Cf": "red",
                                 "Es": "red",
                                 "Fm": "red",
                                 "Md": "red",
                                 "No": "red",
                                 "Lr": "red",
                                 "Rf": "red",
                                 "Db": "red",
                                 "Sg": "red",
                                 "Bh": "red",
                                 "Hs": "red",
                                 "Mt": "red",
                                 "Ds": "red",
                                 "Rg": "red",
                                 "Cn": "red",
                                 "Uut": "red",
                                 "Fl": "red",
                                 "Uup": "red",
                                 "Lv": "red",
                                 "Uus": "red",
                                 "Uuo": "red"}

        # These are for strings in Depth Profile Dialog.
        self.__flags_cross_section = {1: "Rutherford", 2: "L'Ecuyer",
                                      3: "Andersen"}

        if not os.path.exists(self.__config_file):
            self.__set_defaults()
            # Set default request directory
            self.set_request_directory(self.__request_directory)
            self.save_config()
        else:
            self.__load_config()

    def __make_directories(self, directory):
        """Make directories if it doesn't exist.

        Args:
            directory: A string representing a directory.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)

    def __set_defaults(self):
        """Set settings to default values.
        """
        self.__config.add_section("default")
        self.__config.add_section("colors")
        self.__config.add_section("import_timing")
        self.__config.add_section("depth_profile")
        self.__config.add_section("tof-e_graph")
        self.__config.set("default", "request_directory",
                          self.__request_directory)
        self.__config.set("default",
                          "request_directory_last_open",
                          self.__request_directory_last_open)
        keys = self.__element_colors.keys()
        for key in keys:
            self.__config.set("colors", key, self.__element_colors[key])
        self.__config.set("import_timing", "0", "-1000,1000")
        self.__config.set("import_timing", "1", "-1000,1000")
        self.__config.set("import_timing", "2", "-1000,1000")
        self.__config.set("default", "preview_coincidence_count", "10000")
        self.__config.set("default", "es_output", "False")
        self.__config.set("depth_profile", "cross_section", "3")
        self.__config.set("depth_profile", "num_iter", "3")
        self.__config.set("tof-e_graph", "transpose", "False")
        self.__config.set("tof-e_graph", "invert_x", "False")
        self.__config.set("tof-e_graph", "invert_y", "False")
        self.__config.set("tof-e_graph", "color_scheme", "Default color")
        self.__config.set("tof-e_graph", "bin_range_mode", "0")
        self.__config.set("tof-e_graph", "bin_range_x_max", "8000")
        self.__config.set("tof-e_graph", "bin_range_x_min", "0")
        self.__config.set("tof-e_graph", "bin_range_y_max", "8000")
        self.__config.set("tof-e_graph", "bin_range_y_min", "0")
        self.__config.set("tof-e_graph", "compression_x", "5")
        self.__config.set("tof-e_graph", "compression_y", "5")

    def __load_config(self):
        """Load old settings and set values.
        """
        self.__config.read(self.__config_file)

    def save_config(self):
        """Save current global settings.
        """
        with open(self.__config_file, 'wt+') as configfile:
            self.__config.write(configfile)

    def get_request_directory(self):
        """Get default request directory.
        """
        return self.__config["default"]["request_directory"]

    def set_request_directory(self, directory):
        """Save default request directory.

        Args:
            directory: String representing folder where requests will be saved
            by default.
        """
        folders = directory.split("/")
        os_dir = os.sep.join(folders)
        self.__config["default"]["request_directory"] = os_dir
        self.save_config()

    def get_request_directory_last_open(self):
        """Get directory where last request was opened.
        """
        return self.__config["default"]["request_directory_last_open"]

    def set_request_directory_last_open(self, directory):
        """Save last opened request directory.

        Args:
            directory: String representing request folder.
        """
        folders = directory.split("/")
        os_dir = os.sep.join(folders)
        self.__config["default"]["request_directory_last_open"] = os_dir
        self.save_config()

    def get_element_colors(self):
        """Get all elements' colors.

        Return:
            Returns a dictionary of elements' colors.
        """
        return self.__config["colors"]

    def get_element_color(self, element):
        """Get a specific element's color.

        Args:
            element: String representing element name.

        Return:
            Returns a color (string) for a specific element.
        """
        return self.__config["colors"][element]

    def set_element_color(self, element, color):
        """Set default color for an element.

        Args:
            element: String representing element.
            color: String representing color.
        """
        self.__config["colors"][element] = color

    def get_import_timing(self, adc):
        """Get coincidence timings for specific ADC.

        Args:
            adc: An integer representing ADC channel.

        Return:
            Returns low & high values for coincidence timing.
        """
        try:
            return self.__config["import_timing"][str(adc)].split(',')
        except:  # Default if doesn't exist.
            return (-1000, 1000)

    def set_import_timing(self, adc, low, high):
        """Set coincidence timings for specific ADC.

        Args:
            adc: An integer representing ADC channel.
            low: An integer representing timing low value.
            high: An integer representing timing high value.
        """
        if high < low:  # Quick fix just in case
            low, high = high, low
        self.__config["import_timing"][str(adc)] = "{0},{1}".format(low, high)

    def get_import_coinc_count(self):
        """Get how many coincidences will be collected for timing preview.

        Return:
            Returns an integer representing coincidence count.
        """
        try:
            return int(self.__config["default"]["preview_coincidence_count"])
        except:  # Default if doesn't exist.
            return 10000

    def set_import_coinc_count(self, count):
        """Set coincidence timings for specific ADC.

        Args:
            count: An integer representing coincidence count.
        """
        self.__config["default"]["preview_coincidence_count"] = str(count)

    def get_cross_sections_text(self):
        """Get cross sections flag as text.

        Return:
            Returns the cross sections flag as string
        """
        return self.__flags_cross_section[self.get_cross_sections()]

    def get_cross_sections(self):
        """Get cross section model to be used in depth profile.

        Return:
            Returns an integer representing cross sections flag.
        """
        try:
            return int(self.__config["depth_profile"]["cross_section"])
        except:  # Default if doesn't exist.
            return 1

    def set_cross_sections(self, flag):
        """Set cross sections used in depth profile to settings.

        Args:
            flag: An integer representing cross sections flag.
        """
        self.__config["depth_profile"]["cross_section"] = str(flag)

    def is_es_output_saved(self):
        """Is Energy Spectrum output saved or not.

        Return:
            Returns a boolean representing will Potku save output or not.
        """
        # try:
        #     return self.__config["default"]["es_output"] == "True"
        # except:  # Default if doesn't exist.
        #     return False

        # We want to always save energy spectra.
        return True

    def set_es_output_saved(self, flag):
        """Set whether Energy Spectrum output is saved or not.

        Args:
            flag: A boolean representing will Potku save output or not.
        """
        self.__config["default"]["es_output"] = str(flag)

    def get_tofe_transposed(self):
        """Get boolean if the ToF-E Histogram is transposed.

        Return:
            Returns a boolean if the ToF-E Histogram is transposed.
        """
        return self.__config["tof-e_graph"]["transpose"] == "True"

    def set_tofe_transposed(self, value):
        """Set if ToF-E histogram is transposed.

        Args:
            value: A boolean representing if the ToF-E Histogram's X axis
                   is inverted.
        """
        self.__config["tof-e_graph"]["transpose"] = str(str(value) == "True")

    def get_tofe_invert_x(self):
        """Get boolean if the ToF-E Histogram's X axis is inverted.

        Return:
            Returns a boolean if the ToF-E Histogram's X axis is inverted.
        """

        return self.__config["tof-e_graph"]["invert_x"] == "True"

    def set_tofe_invert_x(self, value):
        """Set if ToF-E histogram's X axis inverted.

        Args:
            value: A boolean representing if the ToF-E Histogram's X axis
                   is inverted.
        """
        self.__config["tof-e_graph"]["invert_x"] = str(str(value) == "True")

    def get_tofe_invert_y(self):
        """Get boolean if the ToF-E Histogram's Y axis is inverted.

        Return:
            Returns a boolean if the ToF-E Histogram's Y axis is inverted.
        """
        return self.__config["tof-e_graph"]["invert_y"] == "True"

    def set_tofe_invert_y(self, value):
        """Set if ToF-E histogram's Y axis inverted.

        Args:
            value: A boolean representing if the ToF-E Histogram's Y axis
                   is inverted.
        """
        self.__config["tof-e_graph"]["invert_y"] = str(str(value) == "True")

    def set_num_iterations(self, value):
        """Get the number of iterations erd_depth is to perform

        Return:
            Returns the number. As an integer.
        """
        self.__config["depth_profile"]["num_iter"] = str(value)

    def get_num_iterations(self):
        """Set the number of iterations erd_depth is to perform

        Args:
            value: An integer
        """
        try:
            return int(self.__config["depth_profile"]["num_iter"])
        except:  # Default
            return 3

    def get_tofe_color(self):
        """Get color of the ToF-E Histogram.

        Return:
            Returns a string representing ToF-E histogram color scheme.
        """
        return self.__config["tof-e_graph"]["color_scheme"]

    def set_tofe_color(self, value):
        """Set  color of the ToF-E Histogram.

        Args:
            value: A string representing ToF-E histogram color scheme.
        """
        self.__config["tof-e_graph"]["color_scheme"] = str(value)

    def get_tofe_bin_range_mode(self):
        """Get ToF-E Histogram bin range mode.

        Return:
            Returns an integer representing ToF-E histogram bin range mode.
        """
        return int(self.__config["tof-e_graph"]["bin_range_mode"])

    def set_tofe_bin_range_mode(self, value):
        """Set ToF-E Histogram bin range automatic or manual.

        Args:
            value: An integer representing the mode.
                   Automatic = 0
                   Manual = 1
        """
        self.__config["tof-e_graph"]["bin_range_mode"] = str(value)

    def get_tofe_bin_range_x(self):
        """Get ToF-E Histogram X axis bin range.

        Return:
            Returns an integer representing ToF-E histogram X axis bin range.
        """
        rmin = int(self.__config["tof-e_graph"]["bin_range_x_min"])
        rmax = int(self.__config["tof-e_graph"]["bin_range_x_max"])
        return rmin, rmax

    def set_tofe_bin_range_x(self, value_min, value_max):
        """Set ToF-E Histogram X axis bin range.

        Args:
            value_min: An integer representing the axis range minimum.
            value_max: An integer representing the axis range maximum.
        """
        self.__config["tof-e_graph"]["bin_range_x_min"] = str(value_min)
        self.__config["tof-e_graph"]["bin_range_x_max"] = str(value_max)

    def get_tofe_bin_range_y(self):
        """Get ToF-E Histogram Y axis bin range.

        Return:
            Returns an integer representing ToF-E histogram Y axis bin range.
        """
        rmin = int(self.__config["tof-e_graph"]["bin_range_y_min"])
        rmax = int(self.__config["tof-e_graph"]["bin_range_y_max"])
        return rmin, rmax

    def set_tofe_bin_range_y(self, value_min, value_max):
        """Set ToF-E Histogram Y axis bin range.

        Args:
            value_min: An integer representing the axis range minimum.
            value_max: An integer representing the axis range maximum.
        """
        self.__config["tof-e_graph"]["bin_range_y_min"] = str(value_min)
        self.__config["tof-e_graph"]["bin_range_y_max"] = str(value_max)

    def get_tofe_compression_x(self):
        """Get ToF-E Histogram X axis compression.

        Return:
            Returns an integer representing ToF-E histogram Y axis compression.
        """
        return int(self.__config["tof-e_graph"]["compression_x"])

    def set_tofe_compression_x(self, value):
        """Set ToF-E Histogram X axis compression.

        Args:
            value: An integer representing the axis compression.
        """
        self.__config["tof-e_graph"]["compression_x"] = str(value)

    def get_tofe_compression_y(self):
        """Get ToF-E Histogram Y axis compression.

        Return:
            Returns an integer representing ToF-E histogram Y axis compression.
        """
        return int(self.__config["tof-e_graph"]["compression_y"])

    def set_tofe_compression_y(self, value):
        """Set ToF-E Histogram Y axis compression.

        Args:
            value: An integer representing the axis compression.
        """
        self.__config["tof-e_graph"]["compression_y"] = str(value)
