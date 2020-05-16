# coding=utf-8
"""
Created on 11.05.2020

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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').
"""
__author__ = "Juhani Sundell"
__version__ = "2.0"


from enum import IntEnum
from enum import Enum


class OptimizationType(IntEnum):
    RECOIL = 1
    FLUENCE = 2


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


class IonDivision(IntEnum):
    """Enum that decides how the total number of ions is divided per
    simulation process.
    """
    # Ions are not divided, each simulation process uses the full number of
    # ions.
    NONE = 0

    # Simulation ions are divided per process, presimulation ions are not
    SIM = 1

    # Both simulation and presimulation ions are divided per process
    BOTH = 2

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
