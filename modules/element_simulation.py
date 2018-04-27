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

    __slots__ = "name", \
                "modification_time", \
                "simulation_type", "number_of_ions", "number_of_preions", \
                "number_of_scaling_ions", "number_of_recoils", \
                "minimum_scattering_angle", \
                "minimum_main_scattering_angle", "minimum_energy", \
                "simulation_mode", "seed_number", \
                "element", "recoil_atoms", "mcerd_objects", "get_espe", \
                "channel_width", "reference_density", "beam", "target", \
                "detector", "__command", "__process",

    def __init__(self, name="",
                 modification_time=datetime.datetime.now(),
                 simulation_type="rec",
                 number_of_ions=1000000, number_of_preions=100000,
                 number_of_scaling_ions=5, number_of_recoils=10,
                 minimum_main_scattering_angle=20,
                 simulation_mode="narrow", seed_number=101,
                 minimum_energy=1.0, channel_width=0.1,
                 reference_density=4.98e22):
        """Inits Simulation.
        Args:
            request: Request class object.
            modification_time: A modification time in ISO 8601 format, without
                               information about the timezone.
        """
        self.name = name
        self.modification_time = modification_time

        self.simulation_type = simulation_type
        self.simulation_mode = simulation_mode
        self.number_of_ions = number_of_ions
        self.number_of_preions = number_of_preions
        self.number_of_scaling_ions = number_of_scaling_ions
        self.number_of_recoils = number_of_recoils
        self.minimum_main_scattering_angle = minimum_main_scattering_angle
        self.minimum_energy = minimum_energy
        self.seed_number = seed_number
        self.channel_width = channel_width
        self.reference_density = reference_density

        self.__command = os.path.join("external", "Potku-bin", "mcerd" +
                                      (".exe" if platform.system() == "Windows" else ""))
        self.__process = None
        # This has all the mcerd objects so get_espe knows all the element
        # simulations that belong together (with different seed numbers)
        self.mcerd_objects = {}
        self.get_espe = None

        settings = {
            "simulation_type": self.simulation_type,
            "number_of_ions": self.number_of_ions,
            "number_of_preions_in_presimu": self.number_of_preions,
            "number_of_scaling_ions": self.number_of_scaling_ions,
            "number_of_recoils": self.number_of_recoils,
            "minimum_main_scattering_angle": self.minimum_main_scattering_angle,
            "minimum_energy_of_ions": self.minimum_energy,
            "simulation_mode": self.simulation_mode,
            "seed_number": self.seed_number,
            "beam": self.beam,
            "target": self.target,
            "detector": self.detector,
            "recoil": None
        }

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
        self.mcerd_objects.append = MCERD(settings)

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
