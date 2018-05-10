# coding=utf-8
# TODO: Add licence information
"""
Created on 27.3.2018
Updated on 10.5.2018
"""

import datetime
import os

from modules.element import Element

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import json
import time

from modules.layer import Layer


class Target:
    """Target object describes the target.
    """

    __slots__ = "name", "modification_time", "description", "target_type", \
                "image_size", "image_file", "scattering_element", "layers", \
                "target_theta"

    def __init__(self, name="", modification_time=time.time(), description="",
                 target_type="AFM", image_size=(1024, 1024),
                 image_file="", scattering_element=Element.from_string(
                "4He 3.0"), target_theta=70.0, layers=[]):
        """Initialize a target.

        Args:
            name: Target name.
            modification_time: Modification time.
            description: Target description.
            target_type: Target type.
            image_size: Target image size.
            image_file: Target image file.
            scattering_element: Scattering element.
            target_theta: Target angle # TODO: check how the other is
            calculated from the other,
            layers: Target layers.
        """
        self.name = name
        self.modification_time = modification_time
        self.description = description
        self.target_type = target_type
        self.image_size = image_size
        self.image_file = image_file
        self.scattering_element = scattering_element
        self.target_theta = target_theta
        self.layers = layers

    @classmethod
    def from_file(cls, target_file_path, measurement_file_path):
        """Initialize target from a JSON file.

        Args:
            target_file_path: A file path to JSON file containing the target
            parameters.
            measurement_file_path: A file path to JSON file containing target
            angles.

        Return:
            Returns a Target object with parameters read from files.
        """

        obj = json.load(open(target_file_path))

        # Below we do conversion from dictionary to Target object
        name = obj["name"]
        description = obj["description"]
        modification_time_unix = obj["modification_time_unix"]
        target_type = obj["target_type"]
        scattering_element = Element.from_string(obj["scattering_element"])
        image_size = obj["image_size"]
        image_file = obj["image_file"]
        layers = []

        for layer in obj["layers"]:
            layers.append(Layer(layer["name"],
                                layer["elements"],
                                layer["thickness"],
                                layer["density"]))

        obj = json.load(open(measurement_file_path))
        target_theta = obj["geometry"]["target_theta"]

        return cls(name=name, description=description,
                   modification_time=modification_time_unix,
                   target_type=target_type,
                   image_size=image_size, image_file=image_file,
                   scattering_element=scattering_element,
                   target_theta=target_theta,
                   layers=layers)

    def to_file(self, target_file_path, measurement_file_path):
        """
        Save target parameters into files.

        Args:
            target_file_path: File in which the target params will be saved.
            measurement_file_path: File in which target angles will be saved.
        """
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "modification_time_unix": time.time(),
            "target_type": self.target_type,
            "scattering_element": self.scattering_element.__str__(),
            "image_size": self.image_size,
            "image_file": self.image_file,
            "layers": []
        }

        for layer in self.layers:
            layer_obj = {
                "name": layer.name,
                "elements": [element.__str__() for element in layer.elements],
                "thickness": layer.thickness,
                "density": layer.density
            }
            obj["layers"].append(layer_obj)

        with open(target_file_path, "w") as file:
            json.dump(obj, file, indent=4)

        # Read .measurement to obj to update only target angles
        if os.path.exists(measurement_file_path):
            obj = json.load(open(measurement_file_path))
            try:
                obj["geometry"]["target_theta"] = self.target_theta
            except KeyError:
                obj["geometry"] = {
                    "target_theta": self.target_theta
                }
        else:
            obj = {
                "geometry": {
                    "target_theta": self.target_theta
                }
            }

        with open(measurement_file_path, "w") as file:
            json.dump(obj, file, indent=4)
