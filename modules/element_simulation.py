# coding=utf-8
"""
Created on 25.4.2018
Updated on 2.5.2018
"""
import math

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import platform
import datetime
import json
import os

from modules.mcerd import MCERD
from modules.get_espe import GetEspe
from modules.foil import CircularFoil


class ElementSimulation:
    """
    Class for handling the element specific simulation. Can have multiple
    MCERD objects, but only one GetEspe object.
    """

    __slots__ = "name", \
                "modification_time", \
                "simulation_type", "number_of_ions", "number_of_preions", \
                "number_of_scaling_ions", "number_of_recoils", \
                "minimum_scattering_angle", \
                "minimum_main_scattering_angle", "minimum_energy", \
                "simulation_mode", "seed_number", \
                "recoil_element", "recoil_atoms", "mcerd_objects", "get_espe", \
                "channel_width", "reference_density", "beam", "target", \
                "detector", "__command", "__process", "settings", \
                "espe_settings", "description", "run"

    def __init__(self, recoil_element, beam, target, detector, run, name="",
                 description="",
                 modification_time=datetime.datetime.now(),
                 simulation_type="rec",
                 number_of_ions=1000000, number_of_preions=100000,
                 number_of_scaling_ions=5, number_of_recoils=10,
                 minimum_main_scattering_angle=20,
                 simulation_mode="narrow", seed_number=101,
                 minimum_energy=1.0, channel_width=0.1,
                 reference_density=4.98e22):
        """ Initializes ElementSimulation.
        Args:
            beam: Beam object reference.
            target: Target object reference.
            detector: Detector object reference.
            run: Run object reference.
            name: Name of the element simulation.
            modification_time: A modification time in ISO 8601 format, without
                               information about the timezone.
            simulation_type: Type of simulation
            number_of_ions: Number of ions to be simulated.
            number_of_preions: Number of preions.
            number_of_scaling_ions: Number of scaling ions.
            number_of_recoils: Number of recoils.
            minimum_main_scattering_angle: Minimum angle of scattering.
            simulation_mode: Mode of simulation.
            seed_number: Seed number to give unique value to one simulation.
            minimum_energy: Minimum energy.
            channel_width: Channel width.
            reference_density: Reference density.
        """
        self.recoil_element = recoil_element
        self.beam = beam
        self.target = target
        self.detector = detector
        self.run = run
        self.name = name
        self.description = description
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

        self.__command = os.path.join("external", "Potku-bin", "mcerd" +
                                      (".exe" if platform.system() == "Windows"
                                       else ""))
        self.__process = None
        # This has all the mcerd objects so get_espe knows all the element
        # simulations that belong together (with different seed numbers)
        self.mcerd_objects = {}
        self.get_espe = None

        self.settings = {
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

        self.espe_settings = {
            "beam": self.beam,
            "detector": self.detector,
            "target": self.target,
            "ch": self.channel_width,
            "reference_density": self.recoil_element.get_reference_density(),
            "fluence": self.run.fluence,
            "timeres": self.detector.timeres,
            "solid": self.calculate_solid()
        }

    def calculate_solid(self):
        """
        Calculate the solid parameter.
        Return:
            Returns the solid parameter calculated.
        """
        transmissions = self.detector.foils[0].transmission
        for f in self.detector.foils:
            transmissions *= f.transmission

        smallest_solid_angle = self.calculate_smallest_solid_angle()

        return smallest_solid_angle * transmissions

    def calculate_smallest_solid_angle(self):
        """
        Calculate the smallest solid angle.
        Return:
            Smallest solid angle. (unit millisteradian)
        """
        foil = self.detector.foils[0]
        if type(foil) is CircularFoil:
            radius = foil.diameter / 2
            smallest = math.pi * radius ** 2 / foil.distance ** 2
        else:
            smallest = foil.size[0] * foil.size[1] / foil.distance ** 2
        i = 1
        while i in range(len(self.detector.foils)):
            foil = self.detector.foils[i]
            if type(foil) is CircularFoil:
                radius = foil.diameter / 2
                solid_angle = math.pi * radius**2 / foil.distance**2
            else:
                # TODO Foil.size[0] is tuple and breaks the math
#                solid_angle = foil.size[0] * foil.size[1] / foil.distance**2
                pass
            if smallest > solid_angle:
                smallest = solid_angle
            i += 1
        return smallest * 1000  # usually the unit is millisteradian,
        # hence the multiplication by 1000

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
        # TODO: update the cls call above

    def recoil_to_file(self, directory):
        file_path = os.path.join(directory, self.recoil_element.get_element().symbol + ".rec")
        # Convert datetime object to string. Put the string in ISO 8601 format
        #  without information about the timezone. TODO: Add timezone
        element = self.recoil_element.get_element()
        if element.isotope:
            element_str = str(element.isotope) + element.symbol
        else:
            element_str = element.symbol
        obj = {
            "name": self.recoil_element.get_name(),
            "description": self.recoil_element.get_description(),
            "modification_time": datetime.datetime.now().isoformat(
                timespec="seconds"),
            "type": self.simulation_type,
            "element": element_str,
            "density": self.recoil_element.get_reference_density() * 1e22,
            "profile": []
        }

        for point in self.recoil_element.get_points():
            point_obj = {
                "Point": str(round(point.get_x(), 2)) + " " +
                         str(round(point.get_y(), 4))
            }
            obj["profile"].append(point_obj)

        with open(file_path, "w") as file:
            json.dump(obj, file, indent=4)

    def start(self):
        """ Start the simulation."""
        # TODO: fix this to have the real seed number
        self.mcerd_objects["seed number"] = MCERD(self.settings)

    def stop(self):
        """ Stop the simulation."""
        for sim in self.mcerd_objects:
            del sim

    def pause(self):
        """Pause the simulation."""
        # TODO: Implement this sometime in the future.
        pass

    def calculate_espe(self):
        """
        Calculate the energy spectrum from the mcred result file.
        """
        self.get_espe = GetEspe(self.espe_settings, self.mcerd_objects)

    def get_recoil_element(self):
        return self.recoil_element
