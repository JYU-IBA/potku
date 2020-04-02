# coding=utf-8
"""
Created on 25.4.2018
Updated on 30.5.2018

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

from modules.element import Element


class Beam:
    """
    Class for handling beam information.
    """
    def __init__(self, ion=None, energy=10, charge=4,
                 energy_distribution=0, spot_size=(3.0, 5.0), divergence=0,
                 profile="Uniform"):
        """
        Initializes the Beam object.

        Args:
            ion: Beam ion Element.
            energy: Energy of the beam.
            charge: Charge of the beam.
            energy_distribution: Energy distribution of the beam.
            spot_size: Spot size of the beam.
            divergence: Beam divergence.
            profile: Profile of the beam.
        """
        if ion is None:
            self.ion = Element("Cl", 35)
        else:
            self.ion = ion

        self.energy = energy
        self.charge = charge
        self.energy_distribution = energy_distribution
        self.spot_size = spot_size
        self.divergence = divergence
        self.profile = profile

    def get_mcerd_params(self):
        """Returns a list of strings that are passed as parameters for MCERD.
        """
        return [
            f"Beam ion: {self.ion.get_prefix()}",
            f"Beam energy: {self.energy} MeV"
        ]

    def get_setting_parameters(self):
        d = dict(vars(self))
        d.pop("ion")
        return d

