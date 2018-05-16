# coding=utf-8
"""
Created on 25.4.2018
Updated on 6.5.2018
"""
from dialogs.energy_spectrum import EnergySpectrumWidget, \
    EnergySpectrumParamsDialog
from modules.energy_spectrum import EnergySpectrum

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import platform
import datetime
import json
import os
import math
import time

from widgets.matplotlib.simulation.recoil_atom_distribution import RecoilElement

from modules.beam import Beam
from modules.element import Element
from modules.run import Run
from modules.target import Target
from modules.mcerd import MCERD
from modules.get_espe import GetEspe
from modules.foil import CircularFoil


class ElementSimulation:
    """
    Class for handling the element specific simulation. Can have multiple
    MCERD objects, but only one GetEspe object.
    """

    __slots__ = "directory", "request", "name", \
                "modification_time", \
                "simulation_type", "number_of_ions", "number_of_preions", \
                "number_of_scaling_ions", "number_of_recoils", \
                "minimum_scattering_angle", \
                "minimum_main_scattering_angle", "minimum_energy", \
                "simulation_mode", "seed_number", \
                "recoil_element", "recoil_atoms", "mcerd_objects", "get_espe", \
                "channel_width", "reference_density", "beam", "target", \
                "detector", "__command", "__process", "settings", \
                "espe_settings", "description", "run", "spectra", "bin_width"

    def __init__(self, directory, request, recoil_element, beam=Beam(),
                 target=Target(),
                 detector=None,
                 run=Run(),
                 name="Default",
                 description="This is a default mcsimu setting file.",
                 modification_time=datetime.datetime.now(),
                 simulation_type="ERD",
                 number_of_ions=1000000, number_of_preions=100000,
                 number_of_scaling_ions=5, number_of_recoils=10,
                 minimum_scattering_angle=0.05,
                 minimum_main_scattering_angle=20,
                 simulation_mode="narrow", seed_number=101,
                 minimum_energy=1.0, channel_width=0.1,
                 reference_density=4.98e22):
        """ Initializes ElementSimulation.
        Args:
            directory: Folder of simulation that contains the ElementSimulation.
            request: Request object reference.
            recoil_element:
            beam: Beam object reference.
            target: Target object reference.
            detector: Detector object reference.
            run: Run object reference.
            name: Name of the element simulation.
            description: Description of the ElementSimulation
            modification_time: A modification time in ISO 8601 format, without
                               information about the timezone.
            simulation_type: Type of simulation
            number_of_ions: Number of ions to be simulated.
            number_of_preions: Number of ions in presimulation.
            number_of_scaling_ions: Number of scaling ions.
            number_of_recoils: Number of recoils.
            minimum_scattering_angle: Minimum angle of scattering.
            minimum_main_scattering_angle: Minimum main angle of scattering.
            simulation_mode: Mode of simulation.
            seed_number: Seed number to give unique value to one simulation.
            minimum_energy: Minimum energy.
            channel_width: Channel width.
            reference_density: Reference density.
        """
        self.directory = directory
        self.request = request
        self.name = name
        self.description = description
        self.modification_time = modification_time

        self.recoil_element = recoil_element
        self.beam = beam
        self.target = target
        if detector:
            self.detector = detector
        else:
            self.detector = self.request.default_detector
        self.run = run
        self.simulation_type = simulation_type

        self.simulation_mode = simulation_mode
        self.number_of_ions = number_of_ions
        self.number_of_preions = number_of_preions
        self.number_of_scaling_ions = number_of_scaling_ions
        self.number_of_recoils = number_of_recoils
        self.minimum_scattering_angle = minimum_scattering_angle
        self.minimum_main_scattering_angle = minimum_main_scattering_angle
        self.minimum_energy = minimum_energy
        self.seed_number = seed_number
        self.channel_width = channel_width

        self.mcsimu_to_file(os.path.join(self.directory, self.name + ".mcsimu"))
        self.recoil_to_file(os.path.join(self.directory, self.name + ".rec"))
        self.profile_to_file(os.path.join(self.directory,
                                          self.name + ".profile"))

        self.__command = os.path.join("external", "Potku-bin", "mcerd" +
                                      (".exe" if platform.system() == "Windows"
                                       else ""))
        self.__process = None
        # This has all the mcerd objects so get_espe knows all the element
        # simulations that belong together (with different seed numbers)
        self.mcerd_objects = {}
        self.get_espe = None
        self.spectra = []
        self.bin_width = 0.1

        self.settings = {
            "simulation_type": self.simulation_type,
            "number_of_ions": self.number_of_ions,
            "number_of_ions_in_presimu": self.number_of_preions,
            "number_of_scaling_ions": self.number_of_scaling_ions,
            "number_of_recoils": self.number_of_recoils,
            "minimum_scattering_angle": self.minimum_scattering_angle,
            "minimum_main_scattering_angle": self.minimum_main_scattering_angle,
            "minimum_energy_of_ions": self.minimum_energy,
            "simulation_mode": self.simulation_mode,
            "seed_number": self.seed_number,
            "beam": self.beam,
            "target": self.target,
            "detector": self.detector,
            "recoil_element": self.recoil_element
        }

        self.espe_settings = {
            "beam": self.beam,
            "detector": self.detector,
            "target": self.target,
            "ch": self.channel_width,
            "reference_density": self.recoil_element.reference_density,
            "fluence": self.run.fluence,
            "timeres": self.detector.timeres,
            "solid": self.calculate_solid(),
            "result_directory": self.directory
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
        try:
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
                    solid_angle = math.pi * radius ** 2 / foil.distance ** 2
                else:
                    solid_angle = foil.size[0] * foil.size[
                        1] / foil.distance ** 2
                    pass
                if smallest > solid_angle:
                    smallest = solid_angle
                i += 1
            return smallest * 1000  # usually the unit is millisteradian,
            # hence the multiplication by 1000
        except ZeroDivisionError:
            return 0

    @classmethod
    def from_file(cls, request, mcsimu_file_path, rec_file_path,
                  profile_file_path):
        """Initialize ElementSimulation from JSON files.

        Args:
            request: Request that ElementSimulation belongs to.
            mcsimu_file_path: A file path to JSON file containing the
            simulation parameters.
            rec_file_path: A file path to JSON file containing the recoil
            parameters.
            profile_file_path: A file path to JSON file containing the
            channel width.
        """

        obj = json.load(open(mcsimu_file_path))

        name = obj["name"]
        description = obj["description"]
        modification_time = obj["modification_time_unix"]
        simulation_mode = obj["simulation_mode"]
        number_of_ions = obj["number_of_ions"]
        number_of_preions = obj["number_of_preions"]
        seed_number = obj["seed_number"]
        number_of_recoils = obj["number_of_recoils"]
        number_of_scaling_ions = obj["number_of_scaling_ions"]
        minimum_scattering_angle = obj["minimum_scattering_angle"]
        minimum_main_scattering_angle = obj["minimum_main_scattering_angle"]
        minimum_energy = obj["minimum_energy"]

        obj = json.load(open(rec_file_path))
        simulation_type = obj["simulation_type"]
        element = RecoilElement(Element.from_string(obj["element"]),
                                obj["profile"])
        reference_density = obj["reference_density"]

        obj = json.load(open(profile_file_path))
        channel_width = obj["channel_width"]

        simulation_folder, filename = os.path.split(mcsimu_file_path)

        return cls(simulation_folder, request, element,
                   description=description,
                   modification_time=modification_time, name=name,
                   simulation_type=simulation_type,
                   number_of_ions=number_of_ions,
                   number_of_preions=number_of_preions,
                   number_of_scaling_ions=number_of_scaling_ions,
                   number_of_recoils=number_of_recoils,
                   minimum_scattering_angle=minimum_scattering_angle,
                   minimum_main_scattering_angle=minimum_main_scattering_angle,
                   simulation_mode=simulation_mode,
                   seed_number=seed_number,
                   minimum_energy=minimum_energy,
                   channel_width=channel_width,
                   reference_density=reference_density)

    def mcsimu_to_file(self, file_path):
        """Save mcsimu settings to file.

        Args:
            file_path: File in which the mcsimu settings will be saved.
            rec_file_path: File in which the recoil settings will be saved.
            profile_file_path: FIle in which channel width will be saved.
        """
        obj = {
            "name": self.name,
            "description": self.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "modification_time_unix": time.time(),
            "simulation_type": self.simulation_type,
            "simulation_mode": self.simulation_mode,
            "number_of_ions": self.number_of_ions,
            "number_of_preions": self.number_of_preions,
            "seed_number": self.seed_number,
            "number_of_recoils": self.number_of_recoils,
            "number_of_scaling_ions": self.number_of_scaling_ions,
            "minimum_scattering_angle": self.minimum_scattering_angle,
            "minimum_main_scattering_angle": self.minimum_main_scattering_angle,
            "minimum_energy": self.minimum_energy
        }

        with open(file_path, "w") as file:
            json.dump(obj, file, indent=4)

    def recoil_to_file(self, file_path):
        """Save recoil settings to file.

        Args:
            file_path: File in which the recoil settings will be saved.
        """
        element = self.recoil_element.element
        if element.isotope:
            element_str = "{0}{1}".format(element.isotope, element.symbol)
        else:
            element_str = element.symbol

        obj = {
            "name": self.recoil_element.name,
            "description": self.recoil_element.description,
            "modification_time": time.strftime("%c %z %Z", time.localtime(
                time.time())),
            "modification_time_unix": time.time(),
            "simulation_type": self.recoil_element.type,
            "element": element_str,
            "reference_density": self.recoil_element.reference_density *
                                 1e22,
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

    def profile_to_file(self, file_path):
        """Save profile settings (only channel width) to file.

        Args:
            file_path: File in which the channel width will be saved.
        """
        # Read .profile to obj to update only channel width
        if os.path.exists(file_path):
            obj_profile = json.load(open(file_path))
            obj_profile["modification_time"] = time.strftime("%c %z %Z",
                                                             time.localtime(
                                                                 time.time()))
            obj_profile["modification_time_unix"] = time.time()
            obj_profile["channel_width"] = self.channel_width
        else:
            obj_profile = {}
            obj_profile["channel_width"] = self.channel_width

        with open(file_path, "w") as file:
            json.dump(obj_profile, file, indent=4)

    def start(self):
        """ Start the simulation."""
        # TODO: fix this to have the real seed number
        self.mcerd_objects["seed number"] = MCERD(self.settings)

    def stop(self):
        """ Stop the simulation."""
        for sim in list(self.mcerd_objects.keys()):
            self.mcerd_objects[sim].stop_process()
            self.calculate_espe()
            del (self.mcerd_objects[sim])

    def pause(self):
        """Pause the simulation."""
        # TODO: Implement this sometime in the future.
        pass

    def calculate_espe(self):
        """
        Calculate the energy spectrum from the MCERD result file.
        """
        self.get_espe = GetEspe(self.espe_settings, self.mcerd_objects)

    def plot_spectrum(self):
        """
        Plots simulated energy spectrum.
        """
        dialog = EnergySpectrumParamsDialog(self)
        self.spectra = dialog.spectra
        self.bin_width = dialog.bin_width
