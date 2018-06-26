# coding=utf-8
"""
Created on 25.4.2018
Updated on 26.6.2018

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

import platform
import subprocess

import shutil
import os

import modules.masses as masses
from modules.foil import CircularFoil

import tempfile
import threading


class MCERD:
    """
    An MCERD class that handles calling the mcerd binary and creating the
    files it needs.
    """

    def __init__(self, settings, parent):
        """Create an MCERD object. This automatically starts the simulation.

        Args:
            settings: All settings that MCERD needs in one dictionary.
            parent: ElementSimulation object.
        """
        self.__settings = settings
        self.parent = parent

        self.__filename = self.__settings["recoil_element"].prefix \
            + "-" + self.__settings["recoil_element"].name

        # OS specific directory where temporary MCERD files will be stored.
        # In case of Linux and Mac this will be /tmp and in Windows this will
        # be the C:\Users\<username>\AppData\Local\Temp.
        self.tmp = tempfile.gettempdir()

        # The recoil file and erd file are later passed to get_espe.
        self.recoil_file = os.path.join(self.tmp, self.__filename + ".recoil")
        self.result_file = os.path.join(self.tmp, self.__filename + "." +
                                        str(self.__settings["seed_number"]) +
                                        ".erd")
        self.__create_mcerd_files()

        # The command that is used to start the MCERD process.
        mcerd_command = os.path.join("external", "Potku-bin", "mcerd" +
                                     (".exe " if platform.system() == "Windows"
                                      else " ") +
                                     os.path.join(self.tmp, self.__filename))

        # Start the MCERD process.
        # TODO: MCERD needs to be fixed so we can get rid of this ulimit.
        ulimit = "" if platform.system() == "Windows" else "ulimit -s 64000; "
        exec_command = "" if platform.system() == "Windows" else "exec "
        self.__process = subprocess.Popen(ulimit + exec_command + mcerd_command,
                                          shell=True)
        # Use thread for checking if process has terminated
        thread = threading.Thread(target=self.check_if_mcerd_running)
        thread.daemon = True
        thread.start()

    def check_if_mcerd_running(self):
        """
        Check if MCERD process is still running. If not, notify parent.
        """
        while True:
            if self.__process.poll() == 0:
                self.parent.notify(self)
                break

    def stop_process(self):
        """Stop the MCERD process and delete the MCERD object."""
        used_os = platform.system()
        if used_os == "Windows":
            cmd = "TASKKILL /F /PID " + str(self.__process.pid) + " /T"
            subprocess.Popen(cmd)
            self.__process = None
        elif used_os == "Linux" or used_os == "Darwin":
            self.__process.kill()
            self.__process = None
        else:
            print("It appears we do not support your OS.")

    def __create_mcerd_files(self):
        """
        Creates the temporary files needed for running MCERD. These files
        are placed to the directory of the temporary files of the operating
        system.
        """
        self.__command_file = os.path.join(self.tmp, self.__filename)
        self.__target_file = os.path.join(self.tmp, self.__filename +
                                          ".erd_target")
        self.__detector_file = os.path.join(self.tmp, self.__filename +
                                            ".erd_detector")
        self.__foils_file = os.path.join(self.tmp, self.__filename + ".foils")
        self.__presimulation_file = os.path.join(
            self.tmp, self.__filename + ".pre")

        beam = self.__settings["beam"]
        target = self.__settings["target"]
        detector = self.__settings["detector"]
        recoil_element = (self.__settings["recoil_element"])

        # Create the main MCERD command file
        with open(self.__command_file, "w") as file:

            file.write("Type of simulation: " +
                       self.__settings["simulation_type"] + "\n")

            if not beam.ion.isotope:
                beam_isotope = ""
            else:
                beam_isotope = beam.ion.isotope
            file.write(
                "Beam ion: " + str(beam_isotope) + beam.ion.symbol + "\n")

            file.write("Beam energy: " + str(beam.energy) + " MeV\n")

            file.write("Target description file: " + self.__target_file + "\n")

            file.write("Detector description file: " + self.__detector_file +
                       "\n")

            if not recoil_element.element.isotope:
                isotope = ""
            else:
                isotope = recoil_element.element.isotope
            file.write("Recoiling atom: " + str(isotope)
                       + recoil_element.element.symbol + "\n")

            file.write("Recoiling material distribution: " + self.recoil_file
                       + "\n")

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
                       self.__presimulation_file + "\n")

            file.write("Number of real ions per each scaling ion: " +
                       str(self.__settings["number_of_scaling_ions"]) + "\n")

            file.write("Number of ions: " +
                       str(self.__settings["number_of_ions"]) + "\n")

            file.write("Number of ions in the presimulation: " +
                       str(self.__settings["number_of_ions_in_presimu"]) + "\n")

            file.write("Seed number of the random number generator: " +
                       str(self.__settings["seed_number"]) + "\n")

        # Create the MCERD detector file
        with open(self.__detector_file, "w") as file_det:

            file_det.write("Detector type: " + detector.type + "\n")

            file_det.write(
                "Detector angle: " + str(detector.detector_theta) + "\n")

            file_det.write("Virtual detector size: " +
                           ("%0.1f %0.1f" % detector.virtual_size) + "\n")

            file_det.write("Timing detector numbers: " +
                           str(detector.tof_foils[0]) + " " +
                           str(detector.tof_foils[1]) + "\n")

            file_det.write("Description file for the detector foils: " +
                           self.__foils_file + "\n")

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

        # Create the MCERD target file
        with open(self.__target_file, "w") as file_target:
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

            # An indexed list of all elements is written first.
            # Then layers and their elements referencing the index.
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
        with open(self.__foils_file, "w") as file_foils:
            for foil in detector.foils:
                for layer in foil.layers:
                    for element in layer.elements:
                        mass = masses.find_mass_of_isotope(element)
                        file_foils.write("%0.2f %s" % (mass,
                                                       element.symbol) + "\n")

            # An indexed list of all elements is written first.
            # Then layers and their elements referencing the index.
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

        recoil_element.write_recoil_file(self.recoil_file)

    def copy_results(self, destination):
        """Copies MCERD result file (.erd) and recoil file into given
        destination.

        Args:
            destination: Destination folder.
        """
        try:
            shutil.copy(self.result_file, destination)
            self.copy_recoil(destination)
        except FileNotFoundError:
            raise

    def copy_recoil(self, destination):
        """
        Copy recoil file into given destination.

        Args:
            destination: Destination folder.
        """
        try:
            shutil.copy(self.recoil_file, destination)
        except FileNotFoundError:
            raise
