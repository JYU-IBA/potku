# coding=utf-8
# TODO: Add licence information
"""
Created on 27.3.2018
Updated on 27.4.2018
"""
from enum import Enum
from json import JSONEncoder

import datetime

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import json
import os

from modules.layer import Layer


class TargetEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Target):
            layers = []
            target_dict = {
                "name": obj.name,
                "description": obj.description,
                "date": obj.date,
                "type": obj.topography_type.value,
                "image_size": obj.image_size,
                "image_file": obj.image_file,
                "layers": []
            }
            for l in obj.layers:
                layers.append(l)
            target_dict["layers"] = layers
            return target_dict
        return super(TargetEncoder, self).default(obj)


class TargetType(Enum):
    AFM = 0


class Target:
    """Target object describes the target.
    """

    __slots__ = "name", "date", "description", "topography_type", "image_size",\
                "image_file", "layers", "target_fii", "target_theta"

    def __init__(self, name="", date=datetime.date.today(), description="",
                 target_type=TargetType.AFM, image_size=(1024,1024),
                 image_file="", target_fii=0.0, target_theta=70.0, layers=[]):
        """Initialize a target.

        Args:
            name: Target name.
            date: Date of creation.
            description: Target description.
            target_type: Target type.
            image_size: Target image size.
            image_file: Target image file.
            scattering: Scattering element.
            target_fii: Target angle
            target_theta: Target angle # TODO: check how the other is
            calculated from the other,
            layers: Target layers.

        """
        self.name = name
        self.date = date
        self.description = description
        self.topography_type = target_type
        self.image_size = image_size
        self.image_file = image_file
        self.target_fii = target_fii
        self.target_theta = target_theta
        self.layers = layers

    @classmethod
    def from_file(cls, file_path):
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
                                layer["density"]))

        return cls(name, angle, layers)  # TODO: this needs to be updated

    def to_file(self, file_path):
        """
        Save target parameters into a file.

        Args:
            file_path: File in which the target params will be saved.
        """
        obj = {
            "name": self.name,
            "description": self.description,
            "date": self.date,
            "topograpy_type": self.topography_type,
            "image_size": self.image_size,
            "image_file": self.image_file,
            "target_fii": self.target_fii,
            "target_theta": self.target_theta,
            "layers": []
        }

        for layer in self.layers:
            layer_obj = {
                "name": layer.name,
                "elements": [str(element) for element in layer.elements],
                "thickness": layer.thickness,
                "density": layer.density
            }
            obj["layers"].append(layer_obj)

        with open(file_path, "w") as file:
            json.dump(obj, file)
