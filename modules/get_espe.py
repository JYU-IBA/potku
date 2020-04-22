# coding=utf-8
"""
Created on 27.4.2018
Updated on 3.8.2018

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

import os
import platform
import subprocess

import modules.general_functions as gf


class GetEspe:
    """
    Class for handling calling the external program get_espe to generate
    energy spectra coordinates.
    """
    __slots__ = "__recoil_file", "__settings", "__beam", "__detector", \
                "__target", "__channel_width", "__reference_density", \
                "__fluence", "__params", "output_file", "__timeres", \
                "__density", "__solid", "__erd_file", "__output_file"

    def __init__(self, settings):
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
        self.__beam = settings["beam"]
        self.__detector = settings["detector"]
        self.__target = settings["target"]
        self.__channel_width = settings["ch"]
        self.__fluence = settings["fluence"]  # from Run object
        self.__timeres = settings["timeres"]
        self.__density = settings["reference_density"] * settings["multiplier"]
        self.__solid = settings["solid"]
        self.__recoil_file = settings["recoil_file"]
        self.__erd_file = settings["erd_file"]
        self.__output_file = settings["spectrum_file"]

        toflen = self.__detector.foils[self.__detector.tof_foils[1]].distance
        toflen -= self.__detector.foils[self.__detector.tof_foils[0]].distance
        toflen_in_meters = toflen / 1000

        self.__params = "-beam " + str(self.__beam.ion.isotope) + \
                        self.__beam.ion.symbol \
                        + " -energy " + str(self.__beam.energy) \
                        + " -theta " + str(self.__detector.detector_theta) \
                        + " -tangle " + str(self.__target.target_theta) \
                        + " -timeres " + str(self.__timeres) \
                        + " -toflen " + str(toflen_in_meters) \
                        + " -solid " + str(self.__solid) \
                        + " -dose " + str(self.__fluence) \
                        + " -avemass" \
                        + " -density " + str(self.__density) \
                        + " -dist " + str(self.__recoil_file) \
                        + " -ch " + str(self.__channel_width)

    def run_get_espe(self):
        """Run get_espe binary with given parameters.
        """
        command = self.get_command()
        subprocess.call(command, shell=True)

    def get_command(self):
        """Returns the command to run get_espe executable"""
        if platform.system() == "Windows":
            first_cmd = "type"
            executable = "get_espe.exe"
        else:
            first_cmd = "cat"
            executable = "get_espe"

        bin_dir = gf.get_bin_dir()
        espe_path = bin_dir / executable
        # TODO refactor the command into tuples
        return "{0} {1} | {2} {3} > {4}".format(first_cmd,
                                                self.__erd_file,
                                                espe_path,
                                                self.__params,
                                                self.__output_file)
