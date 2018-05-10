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
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import platform
import subprocess

import hashlib
import os
import tempfile

import modules.masses as masses
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
        self.__hash = hashlib.sha1(str(settings).encode("utf-8")).hexdigest()

        # The recoil file and erd file are later passed to get_espe.
        self.recoil_file = self.__create_mcerd_files()
        self.erd_file = os.path.join(self.__tmp, self.__hash + "." +
                                     str(self.__settings["seed_number"]) +
                                     ".erd")

        # The command that is used to start the MCERD process.
        command = os.path.join("external", "Potku-bin", "mcerd" +
                               (".exe " if platform.system() == "Windows"
                                else " ") +
                               os.path.join(self.__tmp, self.__hash))

        # TODO: MCERD needs to be fixed so we can get rid of this ulimit.
        ulimit = "" if platform.system() == "Windows" else "ulimit -s 64000; "

        # Start the MCERD process.
        self.__process = subprocess.Popen(ulimit + command, shell=True)

    def __del__(self):
        """Stop the MCERD process and delete the MCERD object."""
        self.__process.kill()

    def __create_mcerd_files(self):
        """
        Creates the temporary files needed for running MCERD. These files
        are placed to the directory of the temporary files of the operating
        system.

        Return: Path of the recoil file.
        """
        command_file = os.path.join(self.__tmp, self.__hash)
        target_file = os.path.join(self.__tmp, self.__hash + ".target")
        detector_file = os.path.join(self.__tmp, self.__hash, ".detector")
        foils_file = os.path.join(self.__tmp, self.__hash, ".foil")
        recoil_file = os.path.join(self.__tmp, self.__hash + ".recoil")

        beam = self.__settings["beam"]
        target = self.__settings["target"]
        detector = self.__settings["detector"]
        recoil_element = self.__settings["recoil_element"].element

        # Create the main MCERD command file
        with open(command_file) as file:

            file.write("Type of simulation: " +
                       self.__settings["simulation_type"])

            file.write("Beam ion: " + str(beam.ion.isotope) + beam.ion.symbol)

            file.write("Beam energy: " + str(beam.energy))

            file.write("Target description file: " + target_file)

            file.write("Detector description file: " + detector_file)

            file.write("Recoiling atom: " + str(recoil_element.isotope) +
                       recoil_element.symbol)

            file.write("Recoiling material distribution: " + recoil_file)

            file.write("Target angle: " + str(target.target_theta))

            file.write("Beam spot size: " + ("%0.1f %0.1f mm" % beam.spot_size))

            file.write("Minimum angle of scattering: " +
                       str(self.__settings["minimum_scattering_angle"]))

            file.write("Minimum energy of ions: " +
                       str(self.__settings["minimum_energy_of_ions"]))

            file.write("Number of ions: " +
                       str(self.__settings["number_of_ions"]))

            file.write("Number of ions in presimulation: " +
                       str(self.__settings["number_of_ions_in_presimu"]))

            file.write("Average number of recoils per primary ion: " +
                       str(self.__settings["number_of_recoils"] /
                           self.__settings["number_of_ions"]))

            file.write("Seed number of the random number generator: " +
                       str(self.__settings["seed_number"]))

            file.write("Recoil angle width (wide or narrow): " +
                       self.__settings["simulation_mode"])

            file.write("Minimum main scattering angle: " +
                       str(self.__settings["minimum_main_scattering_angle"]))

            file.write("Beam divergence: " + str(beam.divergence))

            file.write("Beam profile: " + str(beam.profile))

            file.write("Surface topography file: " + target.image_file)

            file.write("Side length of the surface topography image: " +
                       ("%0.1f %0.1f" % target.image_size))

            file.write("Number of real ions per each scaling ion:" +
                       str(self.__settings["number_of_ions"] /
                           self.__settings["number_of_scaling_ions"]))

        # Create the MCERD detector file
        with (detector_file, "w") as file_det:

            file_det.write("Detector type: " + detector.type)

            file_det.write("Detector angle: " + detector.angle)

            file_det.write("Virtual detector size: " +
                           ("%0.1f %0.1f" % detector.virtual_size))

            file_det.write("Timing detector numbers: " +
                           str(detector.tof_foils[0]) + " " +
                           str(detector.tof_foils[1]))

            file_det.write("Description file for the detector foils: " +
                           foils_file)

            file_det.write("==========")

            for foil in detector.foils:

                if type(foil) == CircularFoil:
                    file_det.write("Foil type: circular")
                    file_det.write("Foil diameter: " + str(foil.diameter))
                    file_det.write("Foil distance: " + str(foil.distance))
                else:
                    file_det.write("Foil type: rectangular")
                    file_det.write("Foil size: " +
                                   ("%0.1f %0.1f" % foil.size))
                    file_det.write("Foil distance: " + str(foil.distance))

                file_det.write("----------")

        # There will be a list of all used elements at the top of the file,
        # also duplicates (the count can be running)
        # Create the MCERD target file
        with (target_file, "w") as file_target:
            for layer in target.layers:
                for element in layer:
                    mass = masses.find_mass_of_isotope(element)
                    file_target.write("%0.2f %s" % (mass,
                                                    element.symbol))
            count = 0
            for layer in target.layers:
                file_target.write("\n")
                file_target.write(str(layer.thickness) + " nm")
                file_target.write("ZBL")
                file_target.write("ZBL")
                file_target.write(str(layer.density) + " g/cm3")
                for element in layer.elements:
                    file_target.write(str(count) +
                                      (" %0.3f" % element.amount))
                    count += 1

        # Create the MCERD foils file
        with (foils_file, "w") as file_foils:
            for foil in detector.foils:
                for layers in foil.layers:
                    for element in layers:
                        file_foils.write("%0.2f %s" % (element.mass,
                                                       element.symbol))
                count = 0
                for layer in target.layers:
                    file_foils.write("\n")
                    file_foils.write(str(layer.thickness) + " nm")
                    file_foils.write("ZBL")
                    file_foils.write("ZBL")
                    file_foils.write(str(layer.density) + " g/cm3")
                    for element in layer.elements:
                        file_foils.write(str(count) +
                                         (" %0.3f" % element.amount))
                        count += 1

        with (recoil_file, "w") as file_rec:
            for point in recoil_element.points:
                file_rec.write(str(point.get_x()) + " " + str(point.get_y()))

        return recoil_file
