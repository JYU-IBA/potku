# coding=utf-8
"""
Created on 25.4.2018
Updated on 8.2.2020

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
             "Sinikka Siironen \n Juhani Sundell"
__version__ = "2.0"

import modules.masses as masses
import os
import platform
import shutil
import subprocess
import threading
import time

from pathlib import Path


class MCERD:
    """
    An MCERD class that handles calling the mcerd binary and creating the
    files it needs.
    """

    def __init__(self, settings, parent, optimize_fluence=False):
        """Create an MCERD object.

        Args:
            settings: All settings that MCERD needs in one dictionary.
            parent: ElementSimulation object.
        """
        self.__settings = settings

        # TODO rather than having a direct reference to parent, MCERD could
        #      be an Observable
        self.parent = parent

        rec_elem = self.__settings["recoil_element"]

        if optimize_fluence:
            recoil_name = "optfl"
        else:
            recoil_name = rec_elem.name

        self.__rec_filename = f"{rec_elem.prefix}-{recoil_name}"
        self.__filename = f"{self.parent.name_prefix}-{self.parent.name}"

        # TODO rename self.tmp to sim_dir
        self.tmp = self.__settings["sim_dir"]
        simulation_type = self.__settings["simulation_type"]

        if simulation_type == "ERD":
            suffix = ".recoil"
        else:
            suffix = ".scatter"

        # The recoil file and erd file are later passed to get_espe.
        # TODO difference between suffixed rec_file and nonsuffixed?
        # TODO use pathlib
        self.recoil_file = os.path.join(self.tmp, self.__rec_filename +
                                        suffix)
        self.result_file = os.path.join(self.tmp, self.__rec_filename + "." +
                                        str(self.__settings["seed_number"]) +
                                        ".erd")

        self.__command_file = os.path.join(self.tmp, self.__rec_filename)
        self.__target_file = os.path.join(self.tmp, self.__filename +
                                          ".erd_target")
        self.__detector_file = os.path.join(self.tmp, self.__filename +
                                            ".erd_detector")
        self.__foils_file = os.path.join(self.tmp, self.__filename + ".foils")
        self.__presimulation_file = os.path.join(self.tmp, self.__filename +
                                                 ".pre")

        self.__process = None

    def get_command(self):
        """Returns the command that is used to start the MCERD process.
        """
        mcerd_path = os.path.join("external", "Potku-bin", "mcerd{0}".format(
                                  ".exe" if platform.system() == "Windows"
                                  else ""))
        rec_file_path = os.path.join(self.tmp, self.__rec_filename)

        mcerd_command = "{0} {1}".format(mcerd_path, rec_file_path)

        # MCERD needs to be fixed so we can get rid of this ulimit.
        ulimit = "" if platform.system() == "Windows" else "ulimit -s 64000; "
        exec_command = "" if platform.system() == "Windows" else "exec "

        return f"{ulimit}{exec_command}{mcerd_command}"

    def run(self):
        """Starts the MCERD process. Also starts a thread that
        periodically checks if the MCERD has finished.
        """
        # Create files necessary to run MCERD
        self.__create_mcerd_files()

        cmd = self.get_command()
        self.__process = subprocess.Popen(cmd,
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
            try:
                time.sleep(10)
                if self.__process.poll() == 0:
                    self.parent.notify(self)
                    self.__process = None
                    break
            except AttributeError:
                break

    def stop_process(self):
        """Stop the MCERD process and delete the MCERD object."""
        used_os = platform.system()
        if used_os == "Windows":
            cmd = "TASKKILL /F /PID " + str(self.__process.pid) + " /T"
            subprocess.call(cmd)
        elif used_os == "Linux" or used_os == "Darwin":
            self.__process.kill()
        else:
            print("It appears we do not support your OS.")

    def __create_mcerd_files(self):
        """
        Creates the temporary files needed for running MCERD. These files
        are placed to the directory of the temporary files of the operating
        system.
        """
        # TODO individual functions for creating each file type

        target = self.__settings["target"]
        detector = self.__settings["detector"]
        recoil_element = self.__settings["recoil_element"]

        # Create the main MCERD command file
        with open(self.__command_file, "w") as file:
            file.write(self.get_command_file_contents())

        # Create the MCERD detector file
        with open(self.__detector_file, "w") as file_det:
            file_det.write(self.get_detector_file_contents())

        # Create the MCERD target file
        with open(self.__target_file, "w") as file_target:
            for layer in target.layers:
                for element in layer.elements:
                    if element.isotope:
                        # TODO find_mass_of_isotope could handle checking if the
                        #      element has an isotope
                        mass = masses.find_mass_of_isotope(element)
                    else:
                        mass = masses.get_standard_isotope(element.symbol)
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
                    if element.amount > 1:
                        amount = element.amount / 100
                    else:
                        amount = element.amount
                    file_target.write(str(count) +
                                      (" %0.3f" % amount) + "\n")
                    count += 1

        # Create the MCERD foils file
        with open(self.__foils_file, "w") as file_foils:
            for foil in detector.foils:
                for layer in foil.layers:
                    # Write only one layer since mcerd soesn't know how to
                    # handle multiple layers in a foil
                    for element in layer.elements:
                        mass = masses.find_mass_of_isotope(element)
                        file_foils.write("%0.2f %s" % (mass,
                                                       element.symbol) + "\n")
                    break

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
                        if element.amount > 1:
                            amount = element.amount / 100
                        else:
                            amount = element.amount
                        file_foils.write(str(count) +
                                         (" %0.3f" % amount) + "\n")
                        count += 1
                    break

        recoil_element.write_recoil_file(self.recoil_file)

    def get_command_file_contents(self):
        """Returns the contents of MCERD's command file as a string.
        """
        # TODO this could also be done with a template file
        beam = self.__settings["beam"]
        target = self.__settings["target"]
        recoil_element = self.__settings["recoil_element"]
        min_scat_angle = self.__settings['minimum_scattering_angle']
        min_main_scat_angle = self.__settings['minimum_main_scattering_angle']
        min_ene_ions = self.__settings['minimum_energy_of_ions']
        rec_count = self.__settings['number_of_recoils']
        sim_mode = self.__settings['simulation_mode']
        scale_ion_count = self.__settings['number_of_scaling_ions']
        ions_in_presim = self.__settings['number_of_ions_in_presimu']
        seed = self.__settings['seed_number']

        return "\n".join([
            f"Type of simulation: {self.__settings['simulation_type']}",
            *beam.get_mcerd_params(),
            f"Target description file: {self.__target_file}",
            f"Detector description file: {self.__detector_file}",
            f"Recoiling atom: {recoil_element.element.get_prefix()}",
            f"Recoiling material distribution: {self.recoil_file}",
            f"Target angle: {target.target_theta} deg",
            "Beam spot size: " + ("%0.1f %0.1f mm" % beam.spot_size) + "",
            f"Minimum angle of scattering: {min_scat_angle} deg",
            f"Minimum main scattering angle: {min_main_scat_angle} deg",
            f"Minimum energy of ions: {min_ene_ions} MeV",
            f"Average number of recoils per primary ion: {rec_count}",
            f"Recoil angle width (wide or narrow): {sim_mode}",
            f"Presimulation * result file: {self.__presimulation_file}",
            f"Number of real ions per each scaling ion: {scale_ion_count}",
            f"Number of ions: {self.__settings['number_of_ions']}",
            f"Number of ions in the presimulation: {ions_in_presim}",
            f"Seed number of the random number generator: {seed}",
        ])

    def get_detector_file_contents(self):
        """Returns the contents of the detector file as a string.
        """
        detector = self.__settings["detector"]
        foils = "\n----------\n".join("\n".join(foil.get_mcerd_params())
                                      for foil in detector.foils)

        return "\n".join([
            *detector.get_mcerd_params(),
            f"Description file for the detector foils: {self.__foils_file}",
            "==========",
            foils
        ])

    def get_target_file_contents(self):
        pass

    def get_foils_file_contents(self):
        pass

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

    def delete_unneeded_files(self):
        """
        Delete mcerd files that are not needed anymore.
        """
        try:
            os.remove(self.__command_file)
            os.remove(self.__detector_file)
            os.remove(self.__target_file)
            os.remove(self.__foils_file)
        except OSError:
            pass  # Could not delete all the files

        for file in os.listdir(self.tmp):
            if file.startswith(self.__rec_filename):
                if file.endswith(".out") or file.endswith(".dat") or \
                   file.endswith(".range"):
                    try:
                        os.remove(os.path.join(self.tmp, file))
                    except OSError:
                        continue  # Could not delete the file
            if file.startswith(self.__rec_filename) and file.endswith(".pre"):
                try:
                    os.remove(os.path.join(self.tmp, file))
                except OSError:
                    pass
