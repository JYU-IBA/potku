# coding=utf-8
"""
Created on 27.4.2018
Updated on 3.8.2018
Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2018 Severi Jääskeläinen, Samuel Kaiponen, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell, 2021 Joonas Koponen and Tuomas Pitkänen
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
             "Sinikka Siironen \n Juhani Sundell \n Joonas Koponen \n Tuomas " \
             "Pitkänen "
__version__ = "2.0"

import glob
import platform
import subprocess
from pathlib import Path
from typing import Iterable
from typing import Optional
from typing import Tuple

from . import general_functions as gf
from . import subprocess_utils as sutils
from .base import Espe
from .beam import Beam
from .detector import Detector
from .parsing import CSVParser
from .target import Target

from modules.global_settings import GlobalSettings


class GetEspe:
    """Class for handling calling the external program get_espe to generate
    energy spectra coordinates.
    """
    __slots__ = "recoil_file", "beam_ion", "energy", "theta", \
                "channel_width", "fluence", "timeres", "density", \
                "solid", "erd_file", "tangle", "toflen", "_output_parser"

    def __init__(self, beam_ion: str, energy: float, theta: float,
                 tangle: float, toflen: float, solid: float,
                 recoil_file: Path, erd_file: Path,
                 reference_density: float = None,
                 ch: float = 0.025, fluence: float = 5.00e+11,
                 timeres: float = 250.0):
        """Initializes the GetEspe class.
        Args:
            beam_ion: mass number and the chemical symbol of the primary ion
            energy: beam energy (MeV)
            theta: scattering angle (deg)
            tangle: angle between target surface and beam (deg)
            toflen: time-of-flight length (m)
            solid: solid angle of the detector (msr)
            recoil_file: file name for depth distribution
            erd_file: file name for simulated data. Glob patterns allowed.
            reference_density: average atomic density of the first 10 nm layer
                (at./cm^3)
            ch: channel width in the output (MeV)
            fluence: dose of the beam in particles (6.24e12 == 1 p-uC)
            timeres: time resolution of the TOF-detector (ps, FWHM)
        """
        self.beam_ion = beam_ion
        self.energy = energy
        self.theta = theta
        self.tangle = tangle
        self.toflen = toflen
        self.channel_width = ch
        self.fluence = fluence
        self.timeres = timeres

        if reference_density is None:
            self.density = GlobalSettings().get_default_reference_density()
        else:
            self.density = reference_density
        
        self.solid = solid
        self.recoil_file = recoil_file
        self.erd_file = erd_file
        self._output_parser = CSVParser((0, float), (1, float))

    @staticmethod
    def calculate_simulated_spectrum(
            beam: Beam, detector: Detector, target: Target,
            output_file: Optional[Path] = None, verbose: bool = None,
            **kwargs) -> Espe:
        """Calculates simulated spectrum. Calling this is the same as creating
        a new GetEspe object and calling its run method.
        Args:
            beam: provides ion and energy data
            detector: provides tof-length, solid angle, scattering angle
                and time resolution data
            target: provides target theta data
            output_file: path to file where output will be written. If None,
                output is not written to a file.
            verbose: whether get_espe's stderr is printed to console
            kwargs: keyword arguments passed down to GetEspe
        Return:
            spectrum data as a list of parsed tuples
        """
        get_espe = GetEspe(
            beam_ion=beam.ion.get_prefix(),
            energy=beam.energy,
            theta=detector.detector_theta,
            timeres=detector.timeres,
            toflen=detector.calculate_tof_length(),
            solid=detector.calculate_solid(),
            tangle=target.target_theta,
            **kwargs)
        return get_espe.run(output_file=output_file, verbose=verbose)

    @staticmethod
    def read_espe_file(espe_file: Path) -> Espe:
        """Reads a file generated by get_espe.
        Args:
            espe_file: A string representing path of energy spectrum data file
                (.simu) to be read.
        Return:
            Returns energy spectrum data as a list.
        """
        parser = CSVParser((0, float), (1, float))
        try:
            return list(parser.parse_file(espe_file, method=CSVParser.ROW))
        except (OSError, UnicodeDecodeError, IndexError):
            # File was not found, or it could not be decoded (for example, it
            # could have been .png)
            return []

    def run(self, output_file: Optional[Path] = None, verbose: bool = True) \
            -> Espe:
        """Run get_espe binary with given parameters.
        Args:
            output_file: if given, get_espe output will be written to this file
            verbose: whether get_espe's stderr is printed to console
        Return:
            parsed get_espe output
        """
        espe_cmd = self.get_command()
        bin_dir = gf.get_bin_dir()

        stderr = None if verbose else subprocess.DEVNULL

        with subprocess.Popen(
                espe_cmd, cwd=bin_dir, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, universal_newlines=True,
                stderr=stderr) as espe_process:

            with espe_process.stdin as stdin:
                for line in self.read_erd_files():
                    stdin.write(line)

            espe = sutils.process_output(
                espe_process,
                parse_func=self._output_parser.parse_str,
                file=output_file,
                text_func=lambda x: f"{x[0]} {x[1]}\n")

        return espe

    def read_erd_files(self) -> Iterable[str]:
        """Yields lines from ERD files.
        Yield:
            each line as a string
        """
        # TODO this could be a function in some utility module
        for f in glob.glob(str(self.erd_file)):
            with open(f, "r") as file:
                for line in file:
                    yield line

    def get_command(self) -> Tuple[str, ...]:
        """Returns the command to run get_espe executable.
        Return: command as a tuple of strings
        """
        # Options for get_espe
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
        #         -dose    dose of the beam = fluence, in particles (6.24e12 ==
        #                  1 p-uC)
        #         -energy  beam energy (MeV)
        #         -theta   scattering angle (deg)
        #         -tangle  angle between target surface and beam (deg)
        #         -solid   solid angle of the detector (msr)
        #         -density average atomic density of the first 10 nm layer
        #                  (at./cm^3)
        if platform.system() == "Windows":
            executable = str(gf.get_bin_dir() / "get_espe.exe")
        else:
            executable = "./get_espe"

        return (
            executable,
            "-beam", self.beam_ion,
            "-energy", str(self.energy),
            "-theta", str(self.theta),
            "-tangle", str(self.tangle),
            "-timeres", str(self.timeres),
            "-toflen", str(self.toflen),
            "-solid", str(self.solid),
            "-dose", str(self.fluence),
            "-avemass",
            "-density", str(self.density),
            "-ch", str(self.channel_width),
            "-dist", str(self.recoil_file),
        )