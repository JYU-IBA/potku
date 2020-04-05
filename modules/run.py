# coding=utf-8
"""
Created on 3.5.2018
Updated on 27.11.2018

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import json
import os
import time

from modules.beam import Beam
from modules.element import Element


class Run:
    """
    Class that handles parameters concerning a run.
    """

    def __init__(self, beam=None, fluence=1.00e+9, current=1.07,
                 charge=0.641, run_time=600):
        """
        Initializes the Run object.

        Args:
            beam: Beam object.
            fluence: Fluence.
            current: Current.
            charge: Charge.
            time: Time of the run.
        """
        self.beam = beam
        if not self.beam:
            self.beam = Beam()
        self.fluence = fluence
        self.current = current
        self.charge = charge
        self.time = run_time

        # List for undoing fluence values
        self.previous_fluence = []

    def to_file(self, measurement_file_path):
        """
        Saves Run object and Beam object parameters into a file.

        Args:
            measurement_file_path: Path to the .measurement file in which the
                                   parameters are written.
        """
        run_obj = {
            "fluence": self.fluence,
            "current": self.current,
            "charge": self.charge,
            "time": self.time
        }
        beam_obj = {
            "ion": str(self.beam.ion),
            "energy": self.beam.energy,
            "charge": self.beam.charge,
            "energy_distribution": self.beam.energy_distribution,
            "spot_size": self.beam.spot_size,
            "divergence": self.beam.divergence,
            "profile": self.beam.profile
        }

        if os.path.exists(measurement_file_path):
            with open(measurement_file_path) as mesu:
                obj = json.load(mesu)
            obj["general"]["modification_time"] = time.strftime("%c %z %Z",
                                                                time.localtime(
                                                                 time.time()))
            obj["general"]["modification_time_unix"] = time.time()
            obj["run"] = run_obj
            obj["beam"] = beam_obj
        else:
            obj = {"run": run_obj,
                   "beam": beam_obj}

        with open(measurement_file_path, "w") as file:
            json.dump(obj, file, indent=4)

    @classmethod
    def from_file(cls, measurement_file_path):
        """
        Reads parameter sfrom file and makes a Run object from them.
        Args:
             measurement_file_path: Filepath of the .measurement file.

        Return:
            Returns the created Run object.
        """
        with open(measurement_file_path) as mesu:
            mesu = json.load(mesu)

        run = mesu["run"]
        run["run_time"] = run.pop("time")
        beam = mesu["beam"]

        ion = Element.from_string(beam.pop("ion"))
        spot_size = tuple(beam.pop("spot_size"))

        beam_object = Beam(ion=ion, spot_size=spot_size, **beam)

        return cls(beam=beam_object, **run)

    def get_setting_parameters(self):
        d = dict(vars(self))
        d.pop("previous_fluence")
        d.pop("beam")
        return d


