# coding=utf-8
"""
Created on 3.5.2018
Updated on 10.5.2018

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
# TODO: Add licence information

from modules.beam import Beam
import os
import json

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"


class Run:
    """
    Class that handles parameters concerning a run.
    """

    def __init__(self, beam=Beam(), fluence=1.00e+12, current=1.07,
                 charge=0.641, time=600):
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
        self.fluence = fluence
        self.current = current
        self.charge = charge
        self.time = time

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
                   "ion": self.beam.ion.__str__(),
                   "energy": self.beam.energy,
                   "charge": self.beam.charge,
                   "energy_distribution": self.beam.energy_distribution,
                   "spot_size": self.beam.spot_size,
                   "divergence": self.beam.divergence,
                   "profile": self.beam.profile
                   }

        if os.path.exists(measurement_file_path):
            obj = json.load(open(measurement_file_path))
            obj["run"] = run_obj
            obj["beam"] = beam_obj
        else:
            obj = {"run": run_obj,
                   "beam": beam_obj}

        with open(measurement_file_path, "w") as file:
            json.dump(obj, file, indent=4)
