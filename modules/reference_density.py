# coding=utf-8
"""
Created on 3.1.2022
Updated on 3.1.2022

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2022 Joonas Kopoonen and Tuomas Pitkänen

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
__author__ = "Joonas Koponen \n Tuomas Pitkänen"
__version__ = "2.0"

from typing import List

from modules.general_functions import convert_amu_to_kg


class ReferenceDensity:
    """Recalculates the reference density when the user makes changes to the
    layer properties on the target composition tab on the simulation side.
    """
    def __init__(self, layers: List = None):
        """Initializes a ReferenceDensity object.

        Args:
            layers: The reference density will be updated on these element
            layers (such as Si, Au etc.)
        """

        self.layers = layers
        self.reference_density = 0.0
        self.thickness_limit = 10.0
        # Total thickness of the layers that are included in the calculation
        self.total_thickness = 0.0

    def update_reference_density(self):
        self.total_thickness = 0.0
        for layer in self.layers:
            self.add_layer_density(layer)
            if self.total_thickness >= self.thickness_limit:
                break
        self.reference_density /= self.total_thickness

    def add_layer_density(self, layer):
        layer_density = 0.0
        for element in layer.elements:
            mass = element.get_mass() * element.amount
            g_mass = convert_amu_to_kg(mass) * 1000
            layer_density += (layer.density / g_mass)
        effective_thickness = layer.thickness
        if self.total_thickness + effective_thickness > self.thickness_limit:
            effective_thickness = self.thickness_limit - self.total_thickness
        self.reference_density += layer_density * effective_thickness
        self.total_thickness += effective_thickness
