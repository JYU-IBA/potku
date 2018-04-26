# coding=utf-8
"""
Created on 25.4.2018
Updated on 26.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import hashlib
import os
import platform
import subprocess
import tempfile


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

        self.__create_mcerd_files()

        command = os.path.join("external", "Potku-bin", "mcerd" +
            (".exe " if platform.system() == "Windows" else " ") +
            os.path.join(self.__tmp, self.__hash, ".main"))

        # TODO: MCERD needs to be fixed so we can get rid of this ulimit.
        ulimit = "" if platform.system() == "Windows" else "ulimit -s 64000; "
        self.__process = subprocess.Popen(ulimit + command, shell=True)

        self.result_file = os.path.join(self.__tmp, self.__hash, ".erd")

    def __del__(self):
        """Stop the MCERD process and delete the MCERD object."""
        self.__process.kill()

    def __create_mcerd_files(self):

        command_file = os.path.join(self.__tmp, self.__hash + ".main")
        target_file = os.path.join(self.__tmp, self.__hash + ".target")
        detector_file = os.path.join(self.__tmp, self.__hash, ".detector")
        foils_file = os.path.join(self.__tmp, self.__hash, ".foil")
        recoil_file = os.path.join(self.__tmp, self.__hash + ".recoil")

        beam = self.__settings["beam"]
        target = self.__settings["target"]
        detector = self.__settings["detector"]
        recoil = self.__settings["recoil"]

        # Create the main MCERD command file
        with open(command_file) as file:

            file.write("Type of simulation: " +
                       self.__settings["simulation_type"])

            file.write("Beam ion: " + beam.ion)

            file.write("Beam energy: " + str(beam.energy))

            file.write("Target description file: " + target_file)

            file.write("Detector description file: " + detector_file)

            file.write("Recoiling atom: " + recoil.atom)

            file.write("Recoiling material distribution: " + recoil_file)

            file.write("Target angle: " + str(target.angle))

            file.write("Beam spot size: " + ("%0.1f %0.1f mm" % beam.spot_size))

            file.write("Minimum angle of scattering: " +
                       str(self.__settings["minimum_angle_of_scattering"]))

            file.write("Minimum energy of ions: " +
                       str(self.__settings["minimum_energy_of_ions"]))

            file.write("Number of ions: " +
                       str(self.__settings["number_of_ions"]))

            file.write("Number of ions in presimulation: " +
                       str(self.__settings["number_of_ions_in_presimu"]))

            file.write("Average number of recoils per primary ions: " +
                       str(target["number of recoils"] /
                           target["number of ions"]))

            file.write("Seed number of the random number generator: " +
                       str(target["seed_number"]))

            file.write("Recoil angle width (wide or narrow): " +
                       self.__settings["mode"])

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
            with (detector_file, "w") as file:

                file.write("Detector type: " + detector.type)

                file.write("Detector angle: " + detector.angle)

                file.write("Virtual detector size: " +
                           ("%0.1f %0.1f" % detector.virtual_detector_size))

                file.write("Timing detector numbers: " +
                           ("%0.1f %0.1f" % detector.timing_numbers))

                file.write("Description file for the detector foils: " +
                           foils_file)

                file.write("==========")

                for foil in detector.foils:

                    if type(foil) == foil.CircularFoil:
                        file.write("Foil type: circular")
                        file.write("Foil diameter: " + str(foil.diameter))
                        file.write("Foil distance: " + str(foil.distance))
                    else:
                        file.write("Foil type: rectangular")
                        file.write("Foil size: " + ("%0.1f %0.1f" % foil.size))
                        file.write("Foil distance: " + str(foil.distance))

                    file.write("==========")

            # Create the MCERD target file
            with (target_file, "w") as file:
                for layer in enumerate(target.layers):
                    for element in layer:
                        file.write("%0.2f %s" % (element.mass,
                                                 element.symbol))
                count = 0
                for layer in target.layers:
                    file.write("\n")
                    file.write(str(layer.thickness) + " nm")
                    file.write("ZBL")
                    file.write("ZBL")
                    file.write(str(layer.density) + " g/cm3")
                    for element in layer.elements:
                        file.write(str(count) + (" %0.3f" % element.amount))
                        count += 1

            # Create the MCERD foils file
            with (foils_file, "w") as file:
                for foil in detector.foils:
                    for layers in enumerate(foil.layers):
                        for element in layers:
                            file.write("%0.2f %s" % (element.mass,
                                                     element.symbol))
                    count = 0
                    for layer in target.layers:
                        file.write("\n")
                        file.write(str(layer.thickness) + " nm")
                        file.write("ZBL")
                        file.write("ZBL")
                        file.write(str(layer.density) + " g/cm3")
                        for element in layer.elements:
                            file.write(str(count) + (" %0.3f" % element.amount))
                            count += 1
