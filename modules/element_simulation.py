# coding=utf-8
"""
Created on 25.4.2018
Updated on 27.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import subprocess
import platform
import datetime
import json
import os

from modules.mcerd import MCERD
from modules.get_espe import GetEspe


class ElementSimulation():

    __slots__ = "type", "element", "profile", "name", "description",\
                "modification_time", "__command", "__process", \
                "mcerd_objects", "get_espe"

    def __init__(self, type, element, profile, name="", description="",
                 modification_time=datetime.datetime.now()):
        """Initializes an ElementSimulation object.

        Args:
            type:              Type of the simulation (String, either
                               "recoiling" or "scattering").
            element:           An element (either recoiling or scattering) that
                               will
                               be used in the simulation.
            profile:           A recoil atom distribution profile for the
                               element.
            name:              Name of the particular element simulation.
            description:       A description given for the element simulation.
            modification_time: A modification time in ISO 8601 format, without
                               information about the timezone.
        """
        self.name = name
        self.description = description
        self.modification_time = modification_time
        self.type = type
        self.element = element
        self.profile = profile

        self.__command = os.path.join("external", "Potku-bin", "mcerd" +
            (".exe" if platform.system() == "Windows" else ""))
        self.__process = None
        # This has all the mcerd objects so get_espe knows all the element
        # simulations that belong together (with different seed numbers)
        self.mcerd_objects = {}
        self.get_espe = None

    @classmethod
    def from_file(cls, file_path):

        obj = json.load(open(file_path))

        name = obj["name"]
        description = obj["description"]

        # Convert string to datetime object. The string is assumed to be in
        # ISO 8601 format, without information about the timezone.
        # TODO: Add timezone.
        modification_time = datetime.datetime.strptime(obj["modification_time"],
                                                       "%Y-%m-%dT%H:%M:%S")

        type = obj["type"]
        element = obj["element"]
        profile = []  # TODO: Finish this.

        cls(type, element, profile, name, description, modification_time)

    def to_file(self, file_path):

        # Convert datetime object to string. Put the string in ISO 8601 format
        #  without information about the timezone. TODO: Add timezone
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": datetime.datetime.now().isoformat(
                timespec="seconds"),
            "type": self.type,
            "element": self.element,
            "profile": []  # TODO: Finish this.
        }

        with open(file_path, "w") as file:
            json.dump(obj, file)

    def start(self):
        """Start the simulation."""
        # TODO: fix this to have the real seed number
        self.mcerd_objects["seed number"] = MCERD(settings)

    def stop(self):
        """Stop the simulation."""
        for sim in self.mcerd_objects:
            del(sim)

    def pause(self):
        """Pause the simulation."""
        # TODO: Implement this sometime in the future.
        pass

    def calculate_espe(self):
        self.get_espe = GetEspe(espe_settings, self.mcerd_objects)
