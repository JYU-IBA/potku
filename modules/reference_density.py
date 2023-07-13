# coding=utf-8
"""
Created on 3.1.2022
Updated on 13.4.2023

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
from typing import Optional

from modules.general_functions import convert_amu_to_kg


class ReferenceDensity:
    """Class manages the reference density value of a target. Handles the
    dynamic calculation of the mean number density of a target up to the
    thickness limit.
    """

    def __init__(self, layers: List = None,
                 manual_density: Optional[float] = None,
                 use_user_value: Optional[bool] = None):
        """Initializes a ReferenceDensity object.

        Args:
            layers: a list of layer objects.
            manual_density: the user entered reference density value.
            use_user_value: boolean managing the usage of dynamic and manual
                reference density values.
        """
        self.layers = layers
        self.dynamic_density = 0.0
        self.thickness_limit = 10.0    # Limit up to which layers are included
        self._total_thickness = 0.0
        if use_user_value is not None:
            self.use_user_value = use_user_value
        else:
            self.use_user_value = False

        if manual_density is not None:
            self.manual_density = manual_density
        else:
            self.manual_density = 0.0

        self.update_dynamic_value()

    def get_value(self):
        """Returns either dynamic or manual reference density value based
        on use_user_value. This method should be used as a way to retrieve
        the reference density value elsewhere.
        """
        if self.use_user_value is True:
            return self.manual_density
        else:
            return self.dynamic_density

    def update_layers(self, layers):
        """Updates the layers used in dynamic reference density calculation.

        Args:
            layers: a list of layer objects.
        """
        self.layers = layers
        self.update_dynamic_value()

    def update_dynamic_value(self):
        """Calculates a new dynamic reference density value.
        """
        self.dynamic_density = 0.0
        if not self.layers:
            return

        self._total_thickness = 0.0
        for layer in self.layers:
            self._add_layer_density(layer)
            if self._total_thickness >= self.thickness_limit:
                break

        if self._total_thickness != 0.0:
            self.dynamic_density /= self._total_thickness
        else:
            self.dynamic_density = 0.0

    def _add_layer_density(self, layer):
        """Calculates and adds the number density of a single layer multiplied
        by its thickness.

        Args:
            layer: a single layer object.
        """
        mean_atomic_mass = 0.0

        for element in layer.elements:
            mean_atomic_mass += element.get_mass() * element.amount

        mean_atomic_mass = convert_amu_to_kg(mean_atomic_mass) * 1000

        if mean_atomic_mass == 0.0:
            layer_number_density = 0.0
        else:
            layer_number_density = (layer.density / mean_atomic_mass)

        effective_thickness = layer.thickness
        if self._total_thickness + effective_thickness > self.thickness_limit:
            effective_thickness = self.thickness_limit - self._total_thickness

        self.dynamic_density += layer_number_density * effective_thickness
        self._total_thickness += effective_thickness

    def __str__(self):
        return f'ReferenceDensity(dynamic_density={self.dynamic_density}, ' \
               f'use_user_value={self.use_user_value})'
