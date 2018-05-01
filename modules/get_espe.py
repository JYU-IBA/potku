# coding=utf-8
"""
Created on 27.4.2018
"""
__author__ = "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n" \
             "Sinikka Siironen"
__version__ = "2.0"

import os
import platform


class GetEspe():
    """
    Class for handling calling the external program get_espe to generate
    energy spectra coordinates.
    """
    __slots__ = "__result_files", "__recoil_file", \
                "__settings", "__beam", "__detector", "__target", \
                "__channel_width", "__reference_density", "__fluence", \
                "__params", "output_file"

    def __init__(self, settings, mcerd_objects):
        """
        Initializes the GetEspe class.
        Args:
             settings: All settings that get_espe needs in one dictionary.
        """
        # Options for get_espe, here only temporarily:
        #
        # get_espe - Calculate an energy spectrum from simulated ERD data
        #
        # Options:
        #         -real    only real events are handled
        #         -ch      channel width in the output (MeV)
        #         -depth   depth range of the events (nm, two values)
        #         -dist    file name for depth distribution
        #         -m2      average mass of the secondary particles (u)
        #         -avemass use average mass for calculating energy from TOF
        #         -scale   scale the total intensity to value
        #         -err     give statistics in the third column
        #         -detsize limit in the size of the detector foil (mm)
        #         -erange  energy range in the output spectrum (MeV)
        #         -timeres time resolution of the TOF-detector (ps, FWHM)
        #         -eres    energy resolution (keV, FWHM) of the SSD, (energy
        #                  signal used!)
        #         -toflen  time-of-flight length (m)
        #         -beam    mass number and the chemical symbol of the primary
        #                  ion
        #         -dose    dose of the beam (particle-┬╡C) = fluence
        #         -energy  beam energy (MeV)
        #         -theta   scattering angle (deg)
        #         -tangle  angle between target surface and beam (deg)
        #         -solid   solid angle of the detector (msr)
        #         -density surface atomic density of the first 10 nm layer
        #                  (at/cm^2)

        self.__result_files = ""
        for key, value in mcerd_objects.items():
            self.__result_files += value.result_file + " "
            # All the mcerd processes should have the same recoil
            # distribution, so it shouldn't matter which of the files is used.
            self.__recoil_file = value.recoil_file
            self.output_file = value.recoil_file[:len(
                value.recoil_file) - 3] + "simu"
            # output file has the same name as recoil file

        self.__beam = settings["beam"]
        self.__detector = self.__settings["detector"]
        self.__target = self.__settings["target"]
        self.__channel_width = self.__settings["ch"]
        self.__reference_density = self.__settings["reference_density"]
        self.__fluence = self.__settings["fluence"]  # from Run object

        toflen = self.__detector.foils[self.__detector.tof_foils[0]].distance
        toflen -= self.__detector.foils[self.__detector.tof_foils[1]].distance

        self.__params = "-ch " + str(self.__channel_width) + " -dist " + \
                        self.__recoil_file + " -toflen " + str(toflen) + \
                        " -beam " + str(self.__beam.ion.isotope) + \
                        self.__beam.ion.symbol + "-dose " + str(self.__fluence)\
                        + " -energy " + str(self.__beam.energy) + " -theta " + \
                        str(self.__detector.detector_theta) + " -tangle " + \
                        str(self.__target.target_theta)
        # This is missing timeres, solid and density

    def run(self):
        command = ("type " if platform.system() == "Windows" else "cat ") + \
                  self.__result_files + "| " + os.path.join(
            "external", "Potku-bin", "get_espe" +
                                     (".exe " if platform.system() == "Windows"
                                      else "_linux "
                                      if platform.system() == "Linux"
                                      else "_mac ")) + self.__params + " > " + \
                  self.output_file

        os.subprocess.call(command, shell=True)
