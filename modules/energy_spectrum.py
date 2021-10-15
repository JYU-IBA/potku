# coding=utf-8
"""
Created on 21.4.2013
Updated on 18.12.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) 2013-2018 Jarkko Aalto, Severi Jääskeläinen, Samuel Kaiponen,
Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen, Miika Raunio, Heta Rekilä and
Sinikka Siironen, 2020 Juhani Sundell

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen \n " \
             "Juhani Sundell"
__version__ = "2.0"

import os
import pathlib
import platform
import re
import subprocess

from pathlib import Path
from typing import Dict, Union, List, Optional, Sequence, Tuple

from . import general_functions as gf
from . import subprocess_utils as sutils
from .base import Espe
from .element import Element
from .measurement import Measurement
from .observing import ProgressReporter
from .parsing import ToFListParser
from .ui_log_handlers import Logger

import numpy as np

TofListData = List[Tuple[float, float, float, int, float, str, float, int]]


# TODO rename and refactor functions

class EnergySpectrum:
    """Class for energy spectrum.
    """

    def __init__(
            self,
            measurement: Measurement,
            cut_files: Sequence[Path],
            spectrum_width: float,
            progress: Optional[ProgressReporter] = None,
            no_foil: bool = False,
            verbose: bool = True):
        """Inits energy spectrum
        
        Args:
            measurement: A Measurement class object for which Energy Spectrum
                         is made.
            cut_files: String list of cut files.
            spectrum_width: Float representing energy spectrum graph width.
            progress: ProgressReporter object.
            no_foil: whether foil thickness is set to 0 when running tof_list
            verbose: whether tof_list's stderr is printed to console
        """
        self._measurement = measurement
        self._global_settings = self._measurement.request.global_settings
        self._cut_files = cut_files
        self._spectrum_width = spectrum_width
        self._directory_es = measurement.get_energy_spectra_dir()
        self._tof_listed_files = self._load_cuts(
            no_foil=no_foil, progress=progress, verbose=verbose)

    @staticmethod
    def calculate_measured_spectra(
            measurement: Measurement,
            cut_files: Sequence[Path],
            spectrum_width: float,
            progress: Optional[ProgressReporter] = None,
            use_efficiency: bool = False,
            sum_spectrum: bool = False,
            no_foil: bool = False,
            verbose: bool = True) -> Dict[str, Espe]:
        """Calculates the measured energy spectra for the given .cut files.

        Args:
            measurement: Measurement whose settings will be used when
                calculating spectra
            cut_files: collection of .cut file paths
            spectrum_width: Float representing energy spectrum graph width.
            progress: ProgressReporter object.
            use_efficiency: whether efficiency is taken into account when
                spectra is calculated
            sum_spectrum: whether sum spectrum is taken into account when
                spectra is calculated
            no_foil: whether foil thickness is set to 0 when running tof_list
            verbose: whether tof_list's stderr is printed to console

        Returns:
            energy spectra as a dictionary
        """
        es = EnergySpectrum(
            measurement, cut_files, spectrum_width, progress=progress,
            no_foil=no_foil, verbose=verbose)
        return es.calculate_spectrum(
            use_efficiency=use_efficiency, no_foil=no_foil)

    def calculate_spectrum(
            self,
            use_efficiency: bool = False,
            no_foil: bool = False) -> Dict[str, Espe]:
        """Calculate energy spectrum data from cut files.

        Args:
            use_efficiency: whether efficiency is taken into account when
                spectra is calculated
            sum_spectrum: whether efficiency is taken into account when
                spectra is calculated
            no_foil: whether foil thickness is set to 0 or original foil
                thickness is used

        Returns:
            energy spectra as a dictionary
        """
        return EnergySpectrum._calculate_spectrum(
            self._tof_listed_files, self._spectrum_width, self._measurement,
            self._directory_es, use_efficiency=use_efficiency, no_foil=no_foil)

    def _load_cuts(
            self,
            no_foil: bool = False,
            progress: Optional[ProgressReporter] = None,
            verbose: bool = True) -> Dict[str, TofListData]:
        """Loads cut files through tof_list into list.

        Args:
            no_foil: whether foil thickness is set to 0 when running tof_list
            progress: ProgressReporter object

        Return:
            Returns list of cut files' tof_list results.
        """
        tof_in = self._measurement.generate_tof_in(no_foil=no_foil)
        cut_dict = {}
        try:
            if self._global_settings.is_es_output_saved():
                directory = self._directory_es
            else:
                directory = None

            count = len(self._cut_files)

            self._directory_es.mkdir(exist_ok=True)

            for i, cut_file in enumerate(self._cut_files):
                # TODO move cut file handling to cut_file module
                filename_split = cut_file.name.split('.')
                element = Element.from_string(filename_split[1])

                if not (5 <= len(filename_split) <= 6):
                    raise ValueError(
                        f"Could not parse cut file name: {cut_file}")

                key = ".".join([str(element), *filename_split[2:-1]])

                cut_dict[key] = EnergySpectrum.tof_list(
                    cut_file, directory, no_foil=no_foil,
                    logger=self._measurement,
                    tof_in=tof_in, verbose=verbose)

                if progress is not None:
                    progress.report(i / count * 90)
        except Exception as e:
            msg = f"Could not calculate Energy Spectrum: {e}."
            self._measurement.log_error(msg)
        finally:
            if progress is not None:
                progress.report(100)
        return cut_dict

    @staticmethod
    def tof_list(
            cut_file: Path,
            directory: Optional[Path] = None,
            no_foil: bool = False,
            logger: Optional[Logger] = None,
            tof_in: Path = Path("tof.in"),
            verbose: bool = True) -> TofListData:
        """ToF_list

        Arstila's tof_list executables interface for Python.

        Args:
            cut_file: A Path representing cut file to be ran through tof_list.
            directory: A Path representing measurement's energy spectrum
                directory.
            no_foil: whether foil thickness was used when .cut files were
                generated. This affects the file path when saving output
            logger: optional Logger entity used for logging
            tof_in: path to tof_in_file
            verbose: whether tof_list's stderr is printed to console

        Returns:
            Returns cut file as list transformed through Arstila's tof_list
            program.
        """
        if not cut_file:
            return []

        tof_parser = ToFListParser()
        cmd = EnergySpectrum.get_command(tof_in, cut_file)
        stderr = None if verbose else subprocess.DEVNULL

        try:
            with subprocess.Popen(
                    cmd, cwd=gf.get_bin_dir(), stdout=subprocess.PIPE,
                    universal_newlines=True, stderr=stderr) as tof_list:

                if directory is not None:
                    directory.mkdir(exist_ok=True)
                    tof_list_file = EnergySpectrum.get_tof_list_file_name(
                        directory, cut_file, no_foil=no_foil)
                else:
                    tof_list_file = None

                tof_list_data = sutils.process_output(
                    tof_list,
                    tof_parser.parse_str,
                    file=tof_list_file,
                    text_func=lambda x: f"{' '.join(str(col) for col in x)}\n"
                )
                return tof_list_data
        except Exception as e:
            msg = f"Error in tof_list: {e}"
            if logger is not None:
                logger.log_error(msg)
            else:
                print(msg)
            return []

    @staticmethod
    def get_command(tof_in: Path, cut_file: Path) -> Tuple[str, str, str]:
        """Returns the command for running tof_list.
        """
        if platform.system() == 'Windows':
            executable = str(gf.get_bin_dir() / "tof_list.exe")
        else:
            executable = "./tof_list"
        return executable, str(tof_in), str(cut_file)

    @staticmethod
    def get_tof_list_file_name(
            directory: Path, cut_file: Path, no_foil: bool = False) -> Path:
        foil_txt = ".no_foil" if no_foil else ""
        return directory / f"{cut_file.stem}{foil_txt}.tof_list"

    @staticmethod
    def get_hist_file_name(
            directory: Path, measurement_name: str, key: str,
            no_foil: bool = False) -> Path:
        foil_txt = ".no_foil" if no_foil else ""
        measurement_name = Path(measurement_name)

        return Path(
            directory,
            f"{measurement_name.name}.{key}{foil_txt}.hist")

    @staticmethod
    def pad_with_zeroes(espe: Espe, spectrum_width: float) -> Espe:
        """Returns energy spectrum data that has been padded with zeroes at
        both ends.
        """
        first_val = espe[0][0] - spectrum_width, 0
        last_val = espe[-1][0] + spectrum_width, 0
        return [first_val, *espe, last_val]

    @staticmethod
    def _calculate_spectrum(
            tof_listed_files,
            spectrum_width: float,
            measurement: Measurement,
            directory_es: Path,
            use_efficiency: bool = False,
            no_foil: bool = False) -> Dict[str, Espe]:
        """Calculate energy spectrum data from .tof_list files and writes the
        results to .hist files.

        Args:
            tof_listed_files: contents of .tof_list files belonging to the
                measurement as a dict.
            spectrum_width: width of bins in the histogrammed spectra
            measurement: measurement which the .tof_list files belong to
            directory_es: directory
            use_efficiency: whether efficiency is taken into account when
                spectra is calculated
            no_foil: whether foil thickness was set to 0 or not. This also
                affects the file name

        Returns:
            contents of .hist files as a dict
        """
        espes = {}
        if use_efficiency:
            y_col = 6
        else:
            y_col = None

        keys = []
        for key, tof_list_data in tof_listed_files.items():
            espe = gf.hist(
                tof_list_data, col=2, weight_col=y_col,
                width=spectrum_width)

            if not espe:
                espes[key] = espe
                continue

            keys.append(key)
            espes[key] = EnergySpectrum.pad_with_zeroes(espe, spectrum_width)

            filename = EnergySpectrum.get_hist_file_name(
                directory_es, measurement.name, key, no_foil=no_foil)

            numpy_array = np.array(
                espe, dtype=[("float", float), ("int", int)])
            np.savetxt(filename, numpy_array, delimiter=" ", fmt="%5.5f %6d")
        return espes


# TODO: Inherit from dict and add _calculate_sum_spectrum to modification
#       operations?
class SumEnergySpectrum:
    """Container class for a sum of energy spectra."""
    def __init__(self, spectra: Dict[str, Espe] = None, directory_es: Optional[Path] = "",
                 spectrum_type: Dict[str, bool] = None) -> None:
        self.sum_spectrums: Dict[str, List] = {"simulation": Optional[List], "measurement": Optional[List]}
        self.sum_spectrum_path: Optional[Path] = None
        self.sum_spectrum_paths: Dict[str, Path] = {"simulation": Optional[Path], "measurement": Optional[Path]}
        self._detailed_sum_spectrum_key: Optional[bool] = None
        self._directory_es: Optional[Path] = directory_es
        self._spectrum_type: Dict[str, bool] = spectrum_type
        self._spectra: Dict[str, Espe] = {}
        self._simulation_spectra: Dict[str, Espe] = {}
        self._measurement_spectra: Dict[str, Espe] = {}
        self._sum_key = "SUM"
        if spectra:
            self.add_or_update_spectra(spectra)

    @property
    def spectra(self) -> Dict[str, Espe]:
        """Get tracked spectra."""
        # Read-only, use other methods to edit spectra
        return self._spectra

    @property
    def directory_es(self) -> Optional[Path]:
        """Get energy spectrum path."""
        # Read-only, use other methods to edit the path
        return self._directory_es

    @property
    def spectrum_type(self) ->Dict[str, bool]:
        """Get energy spectrum type."""
        # Read-only, use other methods to edit the type
        return self._spectrum_type

    @property
    def detailed_sum_spectrum_key(self) -> Optional[bool]:
        """Get detailed sum spectrum key"""
        # Read-only, use other methods to edit the boolean value
        return True

    def _calculate_sum_spectrum(self) -> None:
        spectras = [self._simulation_spectra, self._measurement_spectra]
        spectrum_index = 0
        for s in spectras:
            if not s:
                spectrum_index += 1
            else:
                amount_of_elements = len(s)
                xs = []
                ys = []
                y_sum = []
                for i, spectrum in enumerate(s.values()):
                    xs.append([0.0] * len(spectrum))
                    ys.append([0.0] * len(spectrum))
                    for j, pair in enumerate(spectrum):
                        xs[i][j] += pair[0]
                        ys[i][j] += pair[1]
                xs_flat = [item for sublist in xs for item in sublist]
                xs_flat = np.unique(xs_flat)
                for i in range(amount_of_elements):
                    y_sum.append(np.interp(xs_flat, xs[i], ys[i]))
                y_sum = np.sum(y_sum, axis=0)
                self.sum_spectrum = [tuple(pair) for pair in zip(xs_flat, y_sum)]
                if spectrum_index is 0:
                    self.sum_spectrums["simulation"] = self.sum_spectrum
                else:
                    self.sum_spectrums["measurement"] = self.sum_spectrum
                self.sum_spectrum_to_file(s, spectrum_index)
                spectrum_index += 1
                self._sum_key = 'SUM'

    def sum_spectrum_to_file(self, spectra_type: Dict[str, List[Tuple]] = None, spectrum_index: Optional[int] = None) -> None:
        # raise NotImplementedError  # TODO: remove when done
        # TODO: Build the path (add self.directory_es to __init__?),
        #       differentiate between "simulation" and "measured" in file name.
        spectra_keys = list(spectra_type.keys())
        if self.detailed_sum_spectrum_key:
            if spectrum_index is not 0:
                for key in spectra_keys:
                    if type(key) is str:
                        self._sum_key += "." + re.match(r"^\w*(?=\.|\-)", key)[0]
                    else:
                        self._sum_key += key.suffixes[0]
            else:
                for key in spectra_keys:
                    self._sum_key += "." + re.match(r"^\w*(?=\.|\-)", key.stem)[0]
        # TODO: This is copied from EnergySpectrum._calculate_spectrum,
        #       turn it into a separate function like this:
        #       def espe_to_file(filename, espe_array): ...
        sum_spectrum_np_array = np.array(self.sum_spectrum, dtype=[("float", float), ("int", int)])
        self.get_spectrum_path(spectrum_index)
        np.savetxt(self.sum_spectrum_path, sum_spectrum_np_array, delimiter=" ", fmt="%5.5f %6d")

    def get_spectrum_path(self, spectrum_index: Optional[int] = None):
        sum_prefix = {0: "simulation", 1: "measurement"}
        self.sum_spectrum_path = pathlib.Path(
            self.directory_es) / f"{sum_prefix[spectrum_index].upper()}_{self._sum_key}.hist"
        self.sum_spectrum_paths[sum_prefix[spectrum_index]] = self.sum_spectrum_path

    def add_or_update_spectra(self, spectra: Dict[str, Espe]) -> None:
        """Add or update specified spectra in the sum spectrum."""
        for directory, points in spectra.items():
            # FIXME: If there is a better way to separate simulation and measurement files
            if "simulation" in str(directory).lower() and self._spectrum_type["simulation"]:
                self._simulation_spectra[directory] = points
            elif "measurement" in str(directory).lower() and self._spectrum_type["measurement"]:
                self._measurement_spectra[directory] = points
            else:
                self._measurement_spectra[directory] = points
        self._calculate_sum_spectrum()

    def delete_spectra(self, spectra: Union[Sequence[str], Dict[str, Espe]]) \
            -> None:
        """Delete specified spectra from the sum spectrum."""
        for name in spectra:
            del self._spectra[name]
        self._calculate_sum_spectrum()
