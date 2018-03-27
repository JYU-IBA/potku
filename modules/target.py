# coding=utf-8
# TODO: Add licence information
"""
Created on 27.3.2018
Updated on ...
"""

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__versio__ = "2.0"

import json
import os

from modules.layer import Layer

class Target:

    def __init__(self, name, angle, layers):
        """Initialize a target.

        Args:
            angle: Target angle.
            layers: Target layers.

        """
        self.name = name
        self.angle = angle
        self.layers = layers

    @classmethod
    def fromJSON(cls, file_path):
        """Initialize target from a JSON file.

        Args:
            file_path: A file path to JSON file containing the target
                       parameters.
        """

        obj = json.load(open(file_path))

        # Below we do conversion from dictionary to Target object
        name = os.path.splitext(os.path.split(file_path)[1])[0]
        angle = obj["angle"]
        layers = []

        for layer in obj["layers"]:
            layers.append(Layer(layer["elements"],
                                layer["thickness"],
                                layer["ion_stopping"],
                                layer["recoil_stopping"],
                                layer["density"]))

        return cls(name, angle, layers)