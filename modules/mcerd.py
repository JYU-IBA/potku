# coding=utf-8
"""
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
import shutil

__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import platform
import subprocess

import hashlib
import os
import tempfile

import modules.masses as masses
from modules.element import Element
from modules.foil import CircularFoil


class MCERD:

    def __init__(self, settings):
        """Create an MCERD object. This automatically starts the simulation.

        Args:
            settings: All settings that MCERD needs in one dictionary.
        """
        self.__settings = settings

        # OS specific directory where temporary MCERD files will be stored.
        # In case of Linux and Mac this will be /tmp and in Windows this will
        # be the C:\Users\<username>\AppData\Local\Temp.
        self.__tmp = tempfile.gettempdir()

        # Create a unique hash for the temporary MCERD files. The name needs
        # to be unique because there can be several MCERD processes.
        # self.__hash = hashlib.sha1(str(settings).encode("utf-8")).hexdigest()
        self.__filename = Element.__str__(self.__settings[
                                              "recoil_element"].element) \
            .replace(" ", "_")

        # The recoil file and erd file are later passed to get_espe.
        self.recoil_file = self.__create_mcerd_files()
        self.result_file = os.path.join(self.__tmp, self.__filename + "." +
                                        str(self.__settings["seed_number"]) +
                                        ".erd")
        # self.result_file = os.path.join(self.__tmp, self.__hash + "." +
        #                                str(self.__settings["seed_number"]) +
        #                             ".erd")

        # The command that is used to start the MCERD process.
        mcerd_command = os.path.join("external", "Potku-bin", "mcerd" +
                               (".exe " if platform.system() == "Windows"
                                else " ") +
                               os.path.join(self.__tmp, self.__filename))

        # Start the MCERD process.
        # TODO: MCERD needs to be fixed so we can get rid of this ulimit.
        ulimit = "" if platform.system() == "Windows" else "ulimit -s 64000; "
        exec_command = "" if platform.system() == "Windows" else "exec "
        self.__process = subprocess.Popen(ulimit + exec_command + mcerd_command,
                                          shell=True)

    def stop_process(self):
        """Stop the MCERD process and delete the MCERD object."""
        self.__process.kill()

    def __create_mcerd_files(self):
        """
        Creates the temporary files needed for running MCERD. These files
        are placed to the directory of the temporary files of the operating
        system.

        Return: Path of the recoil file.
        """
        command_file = os.path.join(self.__tmp, self.__filename)
        target_file = os.path.join(self.__tmp, self.__filename + ".target")
        detector_file = os.path.join(self.__tmp, self.__filename + ".detector")
        foils_file = os.path.join(self.__tmp, self.__filename + ".foils")
        recoil_file = os.path.join(self.__tmp, self.__filename + ".recoil")
        presimulation_file = os.path.join(self.__tmp, self.__filename + ".pre")

        beam = self.__settings["beam"]
        target = self.__settings["target"]
        detector = self.__settings["detector"]
        recoil_element = (self.__settings["recoil_element"])

        # Create the main MCERD command file
        with open(command_file, "w") as file:

            file.write("Type of simulation: " +
                       self.__settings["simulation_type"] + "\n")

            file.write(
                "Beam ion: " + str(beam.ion.isotope) + beam.ion.symbol + "\n")

            file.write("Beam energy: " + str(beam.energy) + " MeV\n")

            file.write("Target description file: " + target_file + "\n")

            file.write("Detector description file: " + detector_file + "\n")

            file.write("Recoiling atom: " + str(recoil_element.element.isotope)
                       + recoil_element.element.symbol + "\n")

            file.write("Recoiling material distribution: " + recoil_file + "\n")

            file.write("Target angle: " + str(target.target_theta) + " deg\n")

            file.write(
                "Beam spot size: " + ("%0.1f %0.1f mm" % beam.spot_size) + "\n")

            file.write("Minimum angle of scattering: " +
                       str(self.__settings["minimum_scattering_angle"])
                       + "deg\n")

            file.write("Minimum main scattering angle: " +
                       str(self.__settings["minimum_main_scattering_angle"]) +
                       " deg\n")

            file.write("Minimum energy of ions: " +
                       str(self.__settings["minimum_energy_of_ions"])
                       + " MeV \n")

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
                    mass = masses.find_mass_of_isotope(element)
                    file_target.write("%0.2f %s" % (mass,
                                                    element.symbol) + "\n")

            # First layer is used for target surface calculation.
            file_target.write("\n"
                              "0.01 nm \n"
                              "ZBL \n"
                              "ZBL \n"
                              "0.000001 g/cm3 \n"
                              "0 1.0 \n")
            count = 0
            for layer in target.layers:
                file_target.write("\n")
                file_target.write(str(layer.thickness) + " nm" + "\n")
                file_target.write("ZBL" + "\n")
                file_target.write("ZBL" + "\n")
                file_target.write(str(layer.density) + " g/cm3" + "\n")
                for element in layer.elements:
                    file_target.write(str(count) +
                                      (" %0.3f" % element.amount) + "\n")
                    count += 1

        # Create the MCERD foils file
        with open(foils_file, "w") as file_foils:
            for foil in detector.foils:
                for layer in foil.layers:
                    for element in layer.elements:
                        mass = masses.find_mass_of_isotope(element)
                        file_foils.write("%0.2f %s" % (mass,
                                                       element.symbol) + "\n")
            count = 0
            for foil in detector.foils:
                for layer in foil.layers:
                    file_foils.write("\n")
                    file_foils.write(str(layer.thickness) + " nm" + "\n")
                    file_foils.write("ZBL" + "\n")
                    file_foils.write("ZBL" + "\n")
                    file_foils.write(str(layer.density) + " g/cm3" + "\n")
                    for element in layer.elements:
                        file_foils.write(str(count) +
                                         (" %0.3f" % element.amount) + "\n")
                        count += 1

        with open(recoil_file, "w") as file_rec:
            # MCERD requires the recoil atom distribution to start with these
            # points
            file_rec.write(
                "0.00 0.000001\n10.00 0.000001\n")

            for point in recoil_element.get_points():
                file_rec.write(
                    str(round(point.get_x() + 10.01, 2)) + " " +
                    str(round(point.get_y(), 4)) + "\n")

            # MCERD requires the recoil atom distribution to end with these
            # points
            file_rec.write(
                str(round(recoil_element.get_points()[-1].get_x() + 10.02, 2)) +
                " 0.0\n" +
                str(round(recoil_element.get_points()[-1].get_x() + 10.03, 2)) +
                " 0.0\n")

        return recoil_file

    def copy_result(self, destination):
        """Copies MCERD result file (.erd) into given destination.
        """
        try:
            shutil.copy(self.result_file, destination)
            shutil.copy(self.recoil_file, destination)
        except FileNotFoundError:
            pass
