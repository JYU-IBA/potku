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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen " \
             "\n Samuli Rahkonen \n Miika Raunio \n Severi Jääskeläinen \n " \
             "Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging
import os
import subprocess
import platform

import numpy as np

from pathlib import Path

from . import general_functions as gf
from .parsing import ToFListParser
from .measurement import Measurement
from .element import Element


# TODO rename and refactor functions

class EnergySpectrum:
    """Class for energy spectrum.
    """
    def __init__(self, measurement: Measurement, cut_files, spectrum_width,
                 progress=None, no_foil=False):
        """Inits energy spectrum
        
        Args:
            measurement: A Measurement class object for which Energy Spectrum
                         is made.
            cut_files: String list of cut files.
            spectrum_width: Float representing energy spectrum graph width.
            progress: ProgressReporter object.
            no_foil: whether foil thickness is set to 0 when running tof_list
        """
        self.__measurement = measurement
        self.__global_settings = self.__measurement.request.global_settings
        self.__cut_files = cut_files
        self.__spectrum_width = spectrum_width
        self.__directory_es = measurement.get_energy_spectra_dir()
        # TODO ATM tof_in is generated twice when calculating espes. This
        #      should be refactored
        self.__measurement.generate_tof_in(no_foil=no_foil)
        self.__tof_listed_files = self.__load_cuts(
            no_foil=no_foil, progress=progress)

    @staticmethod
    def calculate_measured_spectra(measurement: Measurement, cut_files,
                                   spectrum_width, progress=None,
                                   no_foil=False):
        """Calculates the measured energy spectra for the given .cut files.

        Args:
            measurement: Measurement whose settings will be used when
                calculating spectra
            cut_files: collection of .cut file paths
            spectrum_width: Float representing energy spectrum graph width.
            progress: ProgressReporter object.
            no_foil: whether foil thickness is set to 0 when running tof_list

        Returns:
            energy spectra as a dictionary
        """
        es = EnergySpectrum(measurement, cut_files, spectrum_width,
                            progress=progress, no_foil=no_foil)
        return es.calculate_spectrum(no_foil=no_foil)

    def calculate_spectrum(self, no_foil=False):
        """Calculate energy spectrum data from cut files.

        Args:
            no_foil: whether foil thickness is set to 0 or original foil
                thickness is used
        
        Returns:
            energy spectra as a dictionary
        """
        # First generate tof.in file to match the measurement whose energy
        # spectra are drawn.
        self.__measurement.generate_tof_in(no_foil=no_foil)
        return EnergySpectrum._calculate_spectrum(
            self.__tof_listed_files, self.__spectrum_width, self.__measurement,
            self.__directory_es, no_foil=no_foil)

    def __load_cuts(self, no_foil=False, progress=None):
        """Loads cut files through tof_list into list.

        Args:
            no_foil: whether foil thickness is set to 0 when running tof_list
            progress: ProgressReporter object

        Return:
            Returns list of cut files' tof_list results.
        """
        cut_dict = {}
        try:
            save_output = self.__global_settings.is_es_output_saved()
            count = len(self.__cut_files)
            
            self.__directory_es.mkdir(exist_ok=True)
            
            for i, cut_file in enumerate(self.__cut_files):
                filename_split = os.path.basename(cut_file).split('.')
                element = Element.from_string(filename_split[1])

                if len(filename_split) == 5:  # Regular cut file
                    # TODO name the split parts
                    key = "{0}.{1}.{2}".format(
                        element, filename_split[2], filename_split[3])
                else:  # Elemental Losses cut file
                    key = "{0}.{1}.{2}.{3}".format(
                        element, filename_split[2], filename_split[3],
                        filename_split[4])

                cut_dict[key] = EnergySpectrum.tof_list(
                    cut_file, self.__directory_es, save_output=save_output,
                    no_foil=no_foil, logger_name=self.__measurement.name)

                if progress is not None:
                    progress.report(i / count * 90)
        except Exception as e:
            msg = f"Could not calculate Energy Spectrum: {e}."
            logging.getLogger(self.__measurement.name).error(msg)
        finally:
            if progress is not None:
                progress.report(100)
        return cut_dict

    @staticmethod
    def tof_list(cut_file: Path, directory: Path = None, save_output=False,
                 no_foil=False, logger_name=None):
        """ToF_list

        Arstila's tof_list executables interface for Python.

        Args:
            cut_file: A Path representing cut file to be ran through tof_list.
            directory: A Path representing measurement's energy spectrum
                directory.
            save_output: A boolean representing whether tof_list output is
                saved.
            no_foil: whether foil thickness was used when .cut files were
                generated. This affects the file path when saving output
            logger_name: name of a logging entity

        Returns:
            Returns cut file as list transformed through Arstila's tof_list
            program.
        """
        bin_dir = gf.get_bin_dir()

        if not cut_file:
            return []

        new_cut_file = gf.copy_file_to_temp(cut_file)
        tof_parser = ToFListParser()

        try:
            if platform.system() == 'Windows':
                executable = str(bin_dir / "tof_list.exe")
            else:
                executable = "./tof_list"

            cmd = executable, str(new_cut_file)
            p = subprocess.Popen(
                cmd, cwd=bin_dir, stdout=subprocess.PIPE,
                universal_newlines=True)

            raw_output = iter(p.stdout.readline, "")
            parsed_output = tof_parser.parse_strs(
                raw_output, method="row", ignore="w")

            if save_output:
                if directory is None:
                    directory = Path.cwd() / "energy_spectrum_output"

                directory.mkdir(exist_ok=True)

                if no_foil:
                    foil_txt = ".no_foil"
                else:
                    foil_txt = ""

                es_file = directory / f"{cut_file.stem}{foil_txt}.tof_list"
                ls = []
                with es_file.open("w") as file:
                    for row in parsed_output:
                        file.write(f"{' '.join(str(col) for col in row)}\n")
                        ls.append(row)
                return ls
            return list(parsed_output)
        except Exception as e:
            msg = f"Error in tof_list: {e}"
            if logger_name is not None:
                logging.getLogger(logger_name).error(msg)
            else:
                print(msg)
            return []
        finally:
            gf.remove_files(new_cut_file)

    @staticmethod
    def _calculate_spectrum(tof_listed_files, spectrum_width: float,
                            measurement: Measurement,
                            directory_es: Path, no_foil=False):
        """Calculate energy spectrum data from .tof_list files and writes the
        results to .hist files.

        Args:
            tof_listed_files: contents of .tof_list files belonging to the
                              measurement as a dict.
            spectrum_width: TODO
            measurement: measurement which the .tof_list files belong to
            directory_es: directory
            no_foil: whether foil thickeness was set to 0 or not. This affects
                     the file name

        Returns:
            contents of .hist files as a dict
        """
        histed_files = {}
        keys = tof_listed_files.keys()
        invalid_keys = set()

        for key in keys:
            histed_files[key] = gf.hist(
                tof_listed_files[key], spectrum_width, 3)
            if not histed_files[key]:
                invalid_keys.add(key)
                continue
            first_val = (histed_files[key][0][0] - spectrum_width, 0)
            last_val = (histed_files[key][-1][0] + spectrum_width, 0)
            histed_files[key].insert(0, first_val)
            histed_files[key].append(last_val)

        for key in keys:
            if key in invalid_keys:
                continue
            file = measurement.name
            histed = histed_files[key]

            if no_foil:
                foil_txt = ".no_foil"
            else:
                foil_txt = ""

            filename = Path(directory_es,
                            "{0}.{1}{2}.hist".format(os.path.splitext(file)[0],
                                                     key,
                                                     foil_txt))
            numpy_array = np.array(histed,
                                   dtype=[('float', float), ('int', int)])

            np.savetxt(filename, numpy_array, delimiter=" ", fmt="%5.5f %6d")

        return histed_files
