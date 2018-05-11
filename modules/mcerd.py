# coding=utf-8
"""
Created on 25.4.2018
Updated on 3.5.2018
"""
from modules.element import Element

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import hashlib
import os
import platform
import subprocess
import tempfile
from modules.foil import CircularFoil
import modules.masses as masses


class MCERD:

    def __init__(self, settings):
        """Create an MCERD object. This automatically starts the simulation.

        Args:
            settings: All settings that MCERD needs in one dictionary.
        """
        self.__settings = settings

        # OS specific directory where temporary MCERD files will be stored.
        self.__tmp = tempfile.gettempdir()

        # Create a unique hash for the temporary MCERD files. The name needs
        # to be unique because there can be several MCERD processes.
        self.__hash = hashlib.sha1(str(settings).encode("utf-8")).hexdigest()

        self.recoil_file = self.__create_mcerd_files()

        command = os.path.join("external", "Potku-bin", "mcerd" +
                               (".exe " if platform.system() == "Windows"
                                else " ") +
                               os.path.join(self.__tmp, self.__hash + ".main"))

        # TODO: MCERD needs to be fixed so we can get rid of this ulimit.
        ulimit = "" if platform.system() == "Windows" else "ulimit -s 64000; "
        exec = "" if platform.system() == "Windows" else "exec "
        self.__process = subprocess.Popen(ulimit + exec + command, shell=True)

        self.result_file = os.path.join(self.__tmp, self.__hash + ".erd")

    def stop_process(self):
        """Stop the MCERD process and delete the MCERD object."""
        self._MCERD__process.kill()

    def __create_mcerd_files(self):
        """
        Creates the files needed for running MCERD.
        Return: Path of the recoil file.
        """

        command_file = os.path.join(self.__tmp, self.__hash + ".main")
        target_file = os.path.join(self.__tmp, self.__hash + ".target")
        detector_file = os.path.join(self.__tmp, self.__hash + ".detector")
        foils_file = os.path.join(self.__tmp, self.__hash + ".foils")
        recoil_file = os.path.join(self.__tmp, self.__hash + ".recoil")
        presimulation_file = os.path.join(self.__tmp, self.__hash + ".pre")

        beam = self.__settings["beam"]
        target = self.__settings["target"]
        detector = self.__settings["detector"]
        recoil_element = self.__settings["recoil_element"]

        # Create the main MCERD command file
        with open(command_file, "w") as file:

            file.write("Type of simulation: " +
                       self.__settings["simulation_type"] + "\n")

            file.write(
                "Beam ion: " + str(beam.ion.isotope) + beam.ion.symbol + "\n")

            file.write("Beam energy: " + str(beam.energy) + "\n")

            file.write("Target description file: " + target_file + "\n")

            file.write("Detector description file: " + detector_file + "\n")

            file.write("Recoiling atom: " + str(
                (recoil_element.get_element().isotope
                 if recoil_element.get_element().isotope
                 else masses.get_most_common_isotope(
                    recoil_element.get_element().symbol))[0])
                       + recoil_element.get_element().symbol + "\n")

            file.write("Recoiling material distribution: " + recoil_file + "\n")

            file.write("Target angle: " + str(target.target_theta) + "\n")

            file.write(
                "Beam spot size: " + ("%0.1f %0.1f mm" % beam.spot_size) + "\n")

            file.write("Minimum angle of scattering: " +
                       str(self.__settings["minimum_scattering_angle"]) + "\n")

            file.write("Minimum main scattering angle: " +
                       str(self.__settings["minimum_main_scattering_angle"]) +
                       "\n")

            file.write("Minimum energy of ions: " +
                       str(self.__settings["minimum_energy_of_ions"]) + "\n")

            file.write("Average number of recoils per primary ion: " +
                       str(self.__settings["number_of_recoils"]) + "\n")

            file.write("Recoil angle width (wide or narrow): " +
                       self.__settings["simulation_mode"] + "\n")

            file.write("Presimulation * result file: " +
                       presimulation_file + "\n")

            file.write("Number of real ions per each scaling ion: " +
                       str(self.__settings["number_of_scaling_ions"]) + "\n")

            file.write("Number of ions: " +
                       str(self.__settings["number_of_ions"]) + "\n")

            file.write("Number of ions in the presimulation: " +
                       str(self.__settings["number_of_ions_in_presimu"]) + "\n")

            file.write("Seed number of the random number generator: " +
                       str(self.__settings["seed_number"]) + "\n")

            # MCERD doesn't use these parameters and they break the command
            # file.
#            file.write("Beam divergence: " + str(beam.divergence) + "\n")

#            file.write("Beam profile: " + str(beam.profile) + "\n")

#            file.write("Surface topography file: " + target.image_file + "\n")

#            file.write("Side length of the surface topography image: "
#                       + "%0.1f %0.1f" % (target.image_size[0],
#                                          target.image_size[1]) + "\n")

        # Create the MCERD detector file
        with open(detector_file, "w") as file_det:

            file_det.write("Detector type: " + detector.type + "\n")

            file_det.write(
                "Detector angle: " + str(detector.detector_theta) + "\n")

            file_det.write("Virtual detector size: " +
                           ("%0.1f %0.1f" % detector.virtual_size) + "\n")

            file_det.write("Timing detector numbers: " +
                           str(detector.tof_foils[0]) + " " +
                           str(detector.tof_foils[1]) + "\n")

            file_det.write("Description file for the detector foils: " +
                           foils_file + "\n")

            file_det.write("==========" + "\n")

            # Write foils from first to second to last
            for foil in detector.foils[:-1]:

                if type(foil) == CircularFoil:
                    file_det.write("Foil type: circular" + "\n")
                    file_det.write(
                        "Foil diameter: " + str(foil.diameter) + "\n")
                    file_det.write(
                        "Foil distance: " + str(foil.distance) + "\n")
                else:
                    file_det.write("Foil type: rectangular" + "\n")
                    file_det.write("Foil size: " +
                                   ("%0.1f %0.1f" % foil.size) + "\n")
                    file_det.write(
                        "Foil distance: " + str(foil.distance) + "\n")

                file_det.write("----------" + "\n")

            # Write the last foil separately to avoid writing "------" after it
            last_foil = detector.foils[len(detector.foils) - 1]
            if type(last_foil) == CircularFoil:
                file_det.write("Foil type: circular" + "\n")
                file_det.write("Foil diameter: " + str(
                    last_foil.diameter) + "\n")
                file_det.write("Foil distance: " + str(
                    last_foil.distance) + "\n")
            else:
                file_det.write("Foil type: rectangular" + "\n")
                file_det.write("Foil size: " +
                               ("%0.1f %0.1f" % last_foil.size) + "\n")
                file_det.write("Foil distance: " + str(last_foil.distance)
                               + "\n")

        # There will be a list of all used elements at the top of the file,
        # also duplicates (the count can be running)
        # Create the MCERD target file
        with open(target_file, "w") as file_target:
            for layer in target.layers:
                for element in layer.elements:
                    element_obj = Element.from_string(element)
                    mass = masses.find_mass_of_isotope(element_obj)
                    file_target.write("%0.2f %s" % (mass,
                                                    element_obj.symbol) + "\n")
            count = 0
            for layer in target.layers:
                file_target.write("\n")
                file_target.write(str(layer.thickness) + " nm" + "\n")
                file_target.write("ZBL" + "\n")
                file_target.write("ZBL" + "\n")
                file_target.write(str(layer.density) + " g/cm3" + "\n")
                for element in layer.elements:
                    element_obj = Element.from_string(element)
                    file_target.write(str(count) +
                                      (" %0.3f" % element_obj.amount) + "\n")
                    count += 1

        # Create the MCERD foils file
        with open(foils_file, "w") as file_foils:
            for foil in detector.foils:
                for layers in foil.layers:
                    for element in layers.elements:
#                        element_obj = element.from_string(element)
                        mass = masses.find_mass_of_isotope(element)
                        file_foils.write("%0.2f %s" % (mass, element.symbol) +
                                         "\n")
            count = 0
            for layer in target.layers:
                file_foils.write("\n")
                file_foils.write(str(layer.thickness) + " nm" + "\n")
                file_foils.write("ZBL" + "\n")
                file_foils.write("ZBL" + "\n")
                file_foils.write(str(layer.density) + " g/cm3" + "\n")
                for element in layer.elements:
                    element_obj = Element.from_string(element)
                    file_foils.write(str(count) +
                                     (" %0.3f" % element_obj.amount) + "\n")
                    count += 1

        with open(recoil_file, "w") as file_rec:
            for point in recoil_element.get_points():
                file_rec.write(
                    str(point.get_x()) + " " + str(point.get_y()) + "\n")

        return recoil_file
