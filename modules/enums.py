# coding=utf-8
"""
Created on 11.05.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2020 Juhani Sundell

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"

import enum

from enum import IntEnum
from enum import Enum


@enum.unique
class OptimizationType(IntEnum):
    RECOIL = 1
    FLUENCE = 2


@enum.unique
class OptimizationState(Enum):
    PREPARING = 1
    SIMULATING = 2
    RUNNING = 3
    FINISHED = 4
    ERROR = 5

    def __str__(self):
        """Returns a string representation of the SimulationState.
        """
        if self == OptimizationState.PREPARING:
            return "Preparing"
        if self == OptimizationState.SIMULATING:
            return "Simulating"
        if self == OptimizationState.RUNNING:
            return "Running"
        if self == OptimizationState.ERROR:
            return "Error"
        return "Finished"


@enum.unique
class SimulationState(Enum):
    """This enum is used to represent the state of simulation.
    """
    # No ERD files exist and simulation is not started
    NOTRUN = 1

    # MCERD is running
    RUNNING = 4

    # ERD files exist, MCERD not running
    DONE = 5

    def __str__(self):
        """Returns a string representation of the SimulationState.
        """
        if self == SimulationState.NOTRUN:
            return "Not run"
        if self == SimulationState.RUNNING:
            return "Running"
        return "Done"


@enum.unique
class IonDivision(IntEnum):
    """Enum that decides how the total number of ions is divided per
    simulation process.
    """
    # Ions are not divided, each simulation process uses the full number of
    # ions.
    NONE = 0

    # Simulation ions are divided per process, pre-simulation ions are not
    SIM = 1

    # Both simulation and pre-simulation ions are divided per process
    BOTH = 2

    def __str__(self):
        if self is IonDivision.NONE:
            return "Ions are not divided per process"
        if self is IonDivision.SIM:
            return "Simulation ions are divided per process"
        return "Both pre-simulation and simulation ions are divided per process"

    def get_ion_counts(self, presim, sim, processes):
        presim = presim if presim >= 0 else 0
        sim = sim if sim >= 0 else 0

        if self is IonDivision.NONE:
            return int(presim), int(sim)

        processes = processes if processes >= 1 else 1

        sim /= processes
        if self is IonDivision.BOTH:
            presim /= processes

        return int(presim), int(sim)


@enum.unique
class DetectorType(str, Enum):
    TOF = "TOF"

    def __str__(self):
        return self.value


@enum.unique
class SimulationType(str, Enum):
    ERD = "ERD"
    RBS = "RBS"

    def __str__(self):
        if self is SimulationType.ERD:
            return "REC"
        return "SCT"

    def get_recoil_type(self):
        return str(self).lower()

    def get_recoil_suffix(self):
        if self is SimulationType.ERD:
            return "recoil"
        return "scatter"


@enum.unique
class SimulationMode(str, Enum):
    NARROW = "narrow"
    WIDE = "wide"

    def __str__(self):
        return self.value.capitalize()


@enum.unique
class CrossSection(IntEnum):
    RUTHERFORD = 1
    LECUYER = 2
    ANDERSEN = 3

    def __str__(self):
        if self is CrossSection.RUTHERFORD:
            return "Rutherford"
        if self is CrossSection.LECUYER:
            return "L'Ecuyer"
        return "Andersen"


_TOFE_MAPPING = {
    "Default color": "jet",
    "Greyscale": "Greys",
    "Greyscale (inverted)": "gray",
}


@enum.unique
class ToFEColorScheme(str, Enum):
    """Color scheme used in ToF-E histogram. Values are strings that can be
    passed down to matplotlib.
    """
    DEFAULT = "jet"
    GREYSCALE = "Greys"
    INV_GREYSCALE = "gray"

    def __str__(self) -> str:
        """Returns a string representation of this ToFEColorScheme.

        The return value is a human-readable string that can be displayed in GUI
        applications.
        """
        if self is ToFEColorScheme.DEFAULT:
            return "Default color"
        if self is ToFEColorScheme.GREYSCALE:
            return "Greyscale"
        return "Greyscale (inverted)"

    @classmethod
    def from_string(cls, string: str) -> "ToFEColorScheme":
        """Returns a new ToFEColorScheme object.

        Args:
            string: either a valid value or a string representation of a
                ToFEColorScheme object.

        Return:
            ToFEColorScheme object
        """
        return cls(_TOFE_MAPPING.get(string, string))


@enum.unique
class Profile(str, Enum):
    UNIFORM = "uniform"
    GAUSSIAN = "gaussian"

    def __str__(self):
        return self.value.capitalize()


@enum.unique
class DepthProfileUnit(str, Enum):
    """X axis unit used for depth profiles.
    """
    ATOMS_PER_SQUARE_CM = "1e15 at./cm²"
    NM = "nm"

    def __str__(self):
        return self.value

