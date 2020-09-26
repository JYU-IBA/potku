# coding=utf-8
"""
Created on 29.4.2013
Updated on 17.12.2018

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
"""
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n " \
             "Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import configparser
import functools

from .enums import CrossSection
from .enums import IonDivision
from .enums import ToFEColorScheme
from pathlib import Path


def handle_exceptions(return_value=None, attr=None):
    """Decorator that handles exceptions that can occur when values are read
    from configparser.

    Args:
        return_value: default return value if an error occurs
        attr: if return value is None, this function returns the value of the
            given attribute. This attribute must belong to the instance whose
            method is being decorated.
    """
    def outer(func):
        @functools.wraps(func)
        def inner(instance, *args, **kwargs):
            try:
                return func(instance, *args, **kwargs)
            except (configparser.NoSectionError, configparser.NoOptionError,
                    KeyError, ValueError, AttributeError):
                if return_value is not None:
                    return return_value
                return getattr(instance, attr)
        return inner
    return outer


class GlobalSettings:
    """Global settings class to handle portable software settings, i.e. these
    settings can be ported from one installation to another.
    """
    # Config file name. Number according to release.
    _CONFIG_FILE = "potku2.ini"

    # Section keys
    _DEFAULT = "default"
    _COLORS = "colors"
    _TIMING = "import_timing"
    _DEPTH_PROFILE = "depth_profile"
    _TOFE = "tof-e_graph"
    _SIMULATION = "simulation"

    # Hard-coded minimum and default values of recoil atom distribution
    # concentration
    MIN_CONC_LIMIT = 1e-6
    _DEFAULT_CONC_LIMIT = 1e-4

    def __init__(self, config_dir=None, save_on_creation=True):
        """Inits GlobalSettings class.
        """
        if config_dir is None:
            self._config_directory = Path.home() / "potku"
        else:
            self._config_directory = Path(config_dir).resolve()

        self._config = configparser.ConfigParser()

        self._request_directory = Path(self._config_directory, "requests")

        self._request_directory_last_open = self._request_directory

        self._create_sections()
        if not self.get_config_file().exists():
            # Set default request directory
            self.set_request_directory(self._request_directory)
            if save_on_creation:
                self.save_config()
        else:
            self._load_config()

    def _create_sections(self):
        """Creates sections for the configparser.
        """
        self._config.add_section(self._DEFAULT)
        self._config.add_section(self._COLORS)
        self._config.add_section(self._TIMING)
        self._config.add_section(self._DEPTH_PROFILE)
        self._config.add_section(self._TOFE)
        self._config.add_section(self._SIMULATION)

        self._config[self._COLORS] = GlobalSettings.get_default_colors()

    def set_config_dir(self, directory: Path):
        """Sets the directory of the config file.
        """
        self._config_directory = Path(directory).resolve()

    def get_config_dir(self) -> Path:
        """Returns the path to config directory.
        """
        return self._config_directory

    def get_config_file(self) -> Path:
        """Returns the path to the config file.
        """
        return self.get_config_dir() / self._CONFIG_FILE

    def _load_config(self):
        """Load old settings and set values.
        """
        try:
            self._config.read(self.get_config_file())
        except (configparser.ParsingError, configparser.DuplicateOptionError):
            pass

    def save_config(self):
        """Save current global settings.
        """
        config_file = self.get_config_file()
        config_file.parent.mkdir(exist_ok=True)
        with config_file.open("wt+") as file:
            self._config.write(file)

    @handle_exceptions(attr="_request_directory")
    def get_request_directory(self) -> Path:
        """Get default request directory.
        """
        return Path(self._config[self._DEFAULT]["request_directory"]).resolve()

    def set_request_directory(self, directory: Path):
        """Save default request directory.

        Args:
            directory: String representing folder where requests will be saved
            by default.
        """
        self._config[self._DEFAULT]["request_directory"] = str(
            directory.resolve())

    @handle_exceptions(attr="_request_directory_last_open")
    def get_request_directory_last_open(self) -> Path:
        """Get directory where last request was opened.
        """
        return Path(
            self._config[self._DEFAULT][
                "request_directory_last_open"]).resolve()

    def set_request_directory_last_open(self, directory: Path):
        """Save last opened request directory.

        Args:
            directory: String representing request folder.
        """
        # TODO use qsettings to do this
        self._config[self._DEFAULT]["request_directory_last_open"] = str(
            directory.resolve())
        self.save_config()

    def get_element_colors(self):
        """Get all elements' colors.

        Return:
            Returns a dictionary of elements' colors.
        """
        return self._config[self._COLORS]

    @handle_exceptions(return_value="red")
    def get_element_color(self, element):
        """Get a specific element's color.

        Args:
            element: String representing element name.

        Return:
            Returns a color (string) for a specific element.
        """
        return self._config[self._COLORS][element]

    def set_element_color(self, element, color):
        """Set default color for an element.

        Args:
            element: String representing element.
            color: String representing color.
        """
        self._config[self._COLORS][element] = color

    @handle_exceptions(return_value=(-1000, 1000))
    def get_import_timing(self, adc):
        """Get coincidence timings for specific ADC.

        Args:
            adc: An integer representing ADC channel.

        Return:
            Returns low & high values for coincidence timing.
        """
        low, high = self._config[self._TIMING][str(adc)].split(',')
        low, high = int(low), int(high)
        if low <= high:
            return low, high
        return high, low

    def set_import_timing(self, adc, low, high):
        """Set coincidence timings for specific ADC.

        Args:
            adc: An integer representing ADC channel.
            low: An integer representing timing low value.
            high: An integer representing timing high value.
        """
        if high < low:  # Quick fix just in case
            low, high = high, low
        self._config[self._TIMING][str(adc)] = f"{low},{high}"

    @handle_exceptions(return_value=10_000)
    def get_import_coinc_count(self) -> int:
        """Get how many coincidences will be collected for timing preview.

        Return:
            Returns an integer representing coincidence count.
        """
        return self._config.getint(self._DEFAULT, "preview_coincidence_count")

    def set_import_coinc_count(self, count: int):
        """Set coincidence timings for specific ADC.

        Args:
            count: An integer representing coincidence count.
        """
        self._config[self._DEFAULT]["preview_coincidence_count"] = str(count)

    @handle_exceptions(return_value=CrossSection.ANDERSEN)
    def get_cross_sections(self) -> CrossSection:
        """Get cross section model to be used in depth profile.

        Return:
            Returns an integer representing cross sections flag.
        """
        return CrossSection(
            self._config.getint(self._DEPTH_PROFILE, "cross_section"))

    def set_cross_sections(self, value: CrossSection):
        """Set cross sections used in depth profile to settings.

        Args:
            value: a CrossSection value.
        """
        self._config[self._DEPTH_PROFILE]["cross_section"] = str(int(value))

    @staticmethod
    def is_es_output_saved() -> bool:
        """Is Energy Spectrum output saved or not.

        Return:
            Returns a boolean representing will Potku save output or not.
        """
        # We want to always save energy spectra.
        return True

    def set_es_output_saved(self, flag: bool):
        """Set whether Energy Spectrum output is saved or not.

        Args:
            flag: A boolean representing will Potku save output or not.
        """
        self._config[self._DEFAULT]["es_output"] = str(flag)

    @handle_exceptions(return_value=False)
    def get_tofe_transposed(self) -> bool:
        """Get boolean if the ToF-E Histogram is transposed.

        Return:
            Returns a boolean if the ToF-E Histogram is transposed.
        """
        return self._config.getboolean(self._TOFE, "transpose")

    def set_tofe_transposed(self, value: bool):
        """Set if ToF-E histogram is transposed.

        Args:
            value: A boolean representing if the ToF-E Histogram's X axis
                   is inverted.
        """
        self._config[self._TOFE]["transpose"] = str(value)

    @handle_exceptions(return_value=False)
    def get_tofe_invert_x(self) -> bool:
        """Get boolean if the ToF-E Histogram's X axis is inverted.

        Return:
            Returns a boolean if the ToF-E Histogram's X axis is inverted.
        """

        return self._config.getboolean(self._TOFE, "invert_x")

    def set_tofe_invert_x(self, value: bool):
        """Set if ToF-E histogram's X axis inverted.

        Args:
            value: A boolean representing if the ToF-E Histogram's X axis
                   is inverted.
        """
        self._config[self._TOFE]["invert_x"] = str(value)

    @handle_exceptions(return_value=False)
    def get_tofe_invert_y(self) -> bool:
        """Get boolean if the ToF-E Histogram's Y axis is inverted.

        Return:
            Returns a boolean if the ToF-E Histogram's Y axis is inverted.
        """
        return self._config.getboolean(self._TOFE, "invert_y")

    def set_tofe_invert_y(self, value: bool):
        """Set if ToF-E histogram's Y axis inverted.

        Args:
            value: A boolean representing if the ToF-E Histogram's Y axis
                   is inverted.
        """
        self._config[self._TOFE]["invert_y"] = str(value)

    @handle_exceptions(return_value=4)
    def get_num_iterations(self) -> int:
        """Set the number of iterations erd_depth is to perform
        """
        return self._config.getint(self._DEPTH_PROFILE, "num_iter")

    def set_num_iterations(self, value: int):
        """Get the number of iterations erd_depth is to perform

        Return:
            Returns the number. As an integer.
        """
        self._config[self._DEPTH_PROFILE]["num_iter"] = str(value)

    @handle_exceptions(return_value=ToFEColorScheme.DEFAULT)
    def get_tofe_color(self) -> ToFEColorScheme:
        """Get color of the ToF-E Histogram.

        Return:
            ToFEColorSchemeValue.
        """
        return ToFEColorScheme.from_string(
            self._config[self._TOFE]["color_scheme"])

    def set_tofe_color(self, value: ToFEColorScheme):
        """Set color of the ToF-E Histogram.

        Args:
            value: a ToFEColorScheme value.
        """
        self._config[self._TOFE]["color_scheme"] = value.value

    @handle_exceptions(return_value=0)
    def get_tofe_bin_range_mode(self) -> int:
        """Get ToF-E Histogram bin range mode.

        Return:
            Returns an integer representing ToF-E histogram bin range mode.
        """
        return self._config.getint(self._TOFE, "bin_range_mode")

    def set_tofe_bin_range_mode(self, value: int):
        """Set ToF-E Histogram bin range automatic or manual.

        Args:
            value: An integer representing the mode.
                   Automatic = 0
                   Manual = 1
        """
        self._config[self._TOFE]["bin_range_mode"] = str(value)

    @handle_exceptions(return_value=(0, 8000))
    def get_tofe_bin_range_x(self) -> tuple:
        """Get ToF-E Histogram X axis bin range.

        Return:
            Returns an integer tuple representing ToF-E histogram X axis bin
            range.
        """
        rmin = self._config.getint(self._TOFE, "bin_range_x_min")
        rmax = self._config.getint(self._TOFE, "bin_range_x_max")
        if rmin > rmax:
            return rmax, rmin
        return rmin, rmax

    def set_tofe_bin_range_x(self, value_min: int, value_max: int):
        """Set ToF-E Histogram X axis bin range.

        Args:
            value_min: An integer representing the axis range minimum.
            value_max: An integer representing the axis range maximum.
        """
        if value_min < value_max:
            value_min, value_max = value_max, value_min
        self._config[self._TOFE]["bin_range_x_min"] = str(value_min)
        self._config[self._TOFE]["bin_range_x_max"] = str(value_max)

    @handle_exceptions(return_value=(0, 8000))
    def get_tofe_bin_range_y(self) -> tuple:
        """Get ToF-E Histogram Y axis bin range.

        Return:
            Returns an integer tuple representing ToF-E histogram Y axis bin
            range.
        """
        rmin = self._config.getint(self._TOFE, "bin_range_y_min")
        rmax = self._config.getint(self._TOFE, "bin_range_y_max")
        if rmin > rmax:
            return rmax, rmin
        return rmin, rmax

    def set_tofe_bin_range_y(self, value_min: int, value_max: int):
        """Set ToF-E Histogram Y axis bin range.

        Args:
            value_min: An integer representing the axis range minimum.
            value_max: An integer representing the axis range maximum.
        """
        if value_min < value_max:
            value_min, value_max = value_max, value_min
        self._config[self._TOFE]["bin_range_y_min"] = str(value_min)
        self._config[self._TOFE]["bin_range_y_max"] = str(value_max)

    @handle_exceptions(return_value=6)
    def get_tofe_compression_x(self) -> int:
        """Get ToF-E Histogram X axis compression.

        Return:
            Returns an integer representing ToF-E histogram Y axis compression.
        """
        return self._config.getint(self._TOFE, "compression_x")

    def set_tofe_compression_x(self, value: int):
        """Set ToF-E Histogram X axis compression.

        Args:
            value: An integer representing the axis compression.
        """
        self._config[self._TOFE]["compression_x"] = str(value)

    @handle_exceptions(return_value=6)
    def get_tofe_compression_y(self) -> int:
        """Get ToF-E Histogram Y axis compression.

        Return:
            Returns an integer representing ToF-E histogram Y axis compression.
        """
        return self._config.getint(self._TOFE, "compression_y")

    def set_tofe_compression_y(self, value: int):
        """Set ToF-E Histogram Y axis compression.

        Args:
            value: An integer representing the axis compression.
        """
        self._config[self._TOFE]["compression_y"] = str(value)

    @handle_exceptions(return_value=10_000)
    def get_min_presim_ions(self) -> int:
        """Returns the minimum number of presimulation ions.
        """
        return self._config.getint(self._SIMULATION, "min_presim_ions")

    def set_min_presim_ions(self, value: int):
        """Sets the minimum value of presimulation ions.
        """
        self._config[self._SIMULATION]["min_presim_ions"] = str(value)

    @handle_exceptions(return_value=100_000)
    def get_min_simulation_ions(self) -> int:
        """Returns the minimum number of simulation ions.
        """
        return self._config.getint(self._SIMULATION, "min_sim_ions")

    def set_min_simulation_ions(self, value: int):
        """Sets the minimum number of simulation ions.
        """
        self._config[self._SIMULATION]["min_sim_ions"] = str(value)

    @handle_exceptions(return_value=IonDivision.BOTH)
    def get_ion_division(self) -> IonDivision:
        """Returns the ion division mode used in simulation.
        """
        return IonDivision(
            self._config.getint(self._SIMULATION, "ion_division")
        )

    def set_ion_division(self, value: IonDivision):
        """Sets the value of ion division mode.
        """
        self._config[self._SIMULATION]["ion_division"] = str(int(value))

    @handle_exceptions(return_value=_DEFAULT_CONC_LIMIT)
    def get_minimum_concentration(self) -> float:
        """Returns the minimum concentration that can be set in recoil atom
        distribution.
        """
        return max(
            self._config.getfloat(self._SIMULATION, "min_concentration"),
            GlobalSettings.MIN_CONC_LIMIT)

    def set_minimum_concentration(self, value: float):
        """Sets the minimum concentration that can be set in recoil atom
        distribution. Must be a positive value.
        """
        self._config[self._SIMULATION]["min_concentration"] = str(
            max(value, GlobalSettings.MIN_CONC_LIMIT))

    @staticmethod
    def get_default_colors():
        """Returns a dictionary containing default color values for all
        elements.
        """
        return {
            "H": "#b4903c",
            "He": "red",
            "Li": "red",
            "Be": "red",
            "B": "red",
            "C": "#513c34",
            "N": "#00aa00",
            "O": "#0000ff",
            "F": "red",
            "Ne": "red",
            "Na": "red",
            "Mg": "red",
            "Al": "red",
            "Si": "#800080",
            "P": "red",
            "S": "red",
            "Cl": "#c200c2",
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
            "Cu": "#ffaa00",
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
            "Uuo": "red"
        }
