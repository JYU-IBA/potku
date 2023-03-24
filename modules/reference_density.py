# coding=utf-8
"""
Created on 3.1.2022
Updated on 24.3.2023

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2022 Joonas Koponen and Tuomas Pitkänen, 2023 Sami Voutilainen

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
__author__ = "Joonas Koponen \n Tuomas Pitkänen \n Sami Voutilainen"
__version__ = "2.0"

from typing import List

from modules.general_functions import convert_amu_to_kg


class ReferenceDensity:
    """Class handles the calculation of the mean number density of a target up
    to the thickness limit.
    """

    def __init__(self, layers: List = None):
        """Initializes a ReferenceDensity object.

        Args:
            layers: a list of layer objects.
        """
        self.layers = layers
        self.reference_density = 0.0
        self.thickness_limit = 10.0    # Limit up to which layers are included
        self.total_thickness = 0.0

    def update_layers(self, layers):
        """Updates the layers used in reference density calculation.

        Args:
            layers: a list of layer objects.
        """
        self.layers = layers
        self.update_reference_density()

    def update_reference_density(self):
        """Calculates a new reference_density value.
        """
        self.reference_density = 0.0
        if not self.layers:
            return

        self.total_thickness = 0.0
        for layer in self.layers:
            self.add_layer_density(layer)
            if self.total_thickness >= self.thickness_limit:
                break

        if self.total_thickness != 0.0:
            self.reference_density /= self.total_thickness
        else:
            self.reference_density = 0.0

    def add_layer_density(self, layer):
        """Calculates and adds the number density of a single layer multiplied
        by its thickness.
        """
        mean_atomic_mass = 0.0

        for element in layer.elements:
            mean_atomic_mass += element.get_mass() * element.amount

        mean_atomic_mass = convert_amu_to_kg(mean_atomic_mass) * 1000
        layer_number_density = (layer.density / mean_atomic_mass)

        effective_thickness = layer.thickness
        if self.total_thickness + effective_thickness > self.thickness_limit:
            effective_thickness = self.thickness_limit - self.total_thickness

        self.reference_density += layer_number_density * effective_thickness
        self.total_thickness += effective_thickness
