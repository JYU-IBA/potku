# coding=utf-8
"""
Created on 27.3.2018
Updated on 17.12.2018

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
import time

from pathlib import Path

from modules.element import Element
from modules.layer import Layer


class Target:
    """Target object describes the target.
    """

    __slots__ = "name", "modification_time", "description", "target_type", \
                "image_size", "image_file", "scattering_element", "layers", \
                "target_theta"

    def __init__(self, name="Default", modification_time=None,
                 description="", target_type="AFM", image_size=(1024, 1024),
                 image_file="", scattering_element=None, target_theta=20.5,
                 layers=None):
        """Initialize a target.

        Args:
            name: Target name.
            modification_time: Modification time.
            description: Target description.
            target_type: Target type.
            image_size: Target image size.
            image_file: Target image file.
            scattering_element: Scattering element.
            target_theta: Target angle
            calculated from the other,
            layers: Target layers.
        """
        self.name = name
        if not modification_time:
            modification_time = time.time()
        self.modification_time = modification_time
        self.description = description
        self.target_type = target_type
        self.image_size = tuple(image_size)
        self.image_file = image_file
        self.target_theta = target_theta

        if scattering_element is None:
            self.scattering_element = Element.from_string("4He 3.0")
        else:
            self.scattering_element = scattering_element

        if layers is None:
            self.layers = []
        else:
            self.layers = layers

    @classmethod
    def from_file(cls, target_file_path: Path, measurement_file_path: Path,
                  request):
        """Initialize target from a JSON file.

        Args:
            target_file_path: A file path to JSON file containing the target
                parameters.
            measurement_file_path: A file path to JSON file containing target
                angles.
            request: Request object which has default target angles.

        Return:
            Returns a Target object with parameters read from files.
        """

        with target_file_path.open("r") as tgt_file:
            target = json.load(tgt_file)

        target["modification_time"] = target.pop("modification_time_unix")
        target["scattering_element"] = Element.from_string(
            target["scattering_element"])
        target["image_size"] = target["image_size"]

        layers = []
        for layer in target.pop("layers"):
            elements = [
                Element.from_string(e)
                for e in layer.pop("elements")
            ]
            layers.append(Layer(**layer, elements=elements))

        try:
            with measurement_file_path.open("r") as mesu:
                measurement = json.load(mesu)
            target_theta = measurement["geometry"]["target_theta"]
        # If keys do not exist or measurement_file_path is empty or file
        # doesn't exist:
        except (OSError, KeyError, AttributeError):
            try:
                target_theta = request.default_target.target_theta
            except AttributeError:
                return cls(**target, layers=layers)

        # Note: this way of using kwargs does make it harder to maintain
        # forward compatibility as there may be a need to add more fields
        # to the json file. This could be remedied by adding **kwargs to
        # the __init__ method.
        return cls(**target, target_theta=target_theta, layers=layers)

    def to_file(self, target_file_path: Path, measurement_file_path: Path):
        """
        Save target parameters into files.

        Args:
            target_file_path: File in which the target params will be saved.
            measurement_file_path: File in which target angles will be saved.
        """
        timestamp = time.time()
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                timestamp)),
            "modification_time_unix": timestamp,
            "target_type": self.target_type,
            "scattering_element": str(self.scattering_element),
            "image_size": self.image_size,
            "image_file": self.image_file,
            "layers": []
        }

        for layer in self.layers:
            layer_obj = {
                "name": layer.name,
                "elements": [str(element) for element in layer.elements],
                "thickness": layer.thickness,
                "density": layer.density,
                "start_depth": layer.start_depth
            }
            obj["layers"].append(layer_obj)

        if target_file_path is not None:
            with target_file_path.open("w") as file:
                json.dump(obj, file, indent=4)

        if measurement_file_path is not None:
            # Read .measurement to obj to update only target angles
            try:
                with measurement_file_path.open("r") as mesu:
                    obj = json.load(mesu)
                obj["geometry"]["target_theta"] = self.target_theta
            except (OSError, KeyError):
                obj["geometry"] = {
                        "target_theta": self.target_theta
                    }

            with measurement_file_path.open("w") as file:
                json.dump(obj, file, indent=4)
