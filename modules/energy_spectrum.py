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
import sys

import modules.general_functions as gf

from modules.element import Element


class EnergySpectrum:
    """ Class for energy spectrum.
    """
    def __init__(self, measurement, cut_files, spectrum_width,
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
        self.__directory_es = measurement.directory_energy_spectra
        # tof_list files here just in case progress bar might happen to
        # 'disappear'.
        # TODO ATM tof_in is generated twice when calculating espes. This
        #      should be refactored
        self.__measurement.generate_tof_in(no_foil=no_foil)
        self.__tof_listed_files = self.__load_cuts(no_foil=no_foil,
                                                   progress=progress)

    def calculate_spectrum(self, no_foil=False):
        """Calculate energy spectrum data from cut files.

        Args:
            no_foil: whether foil thickness is set to 0 or original foil
                     thickness is used
        
        Returns list of cut files 
        """
        # First generate tof.in file to match the measurement whose energy
        # spectra are drawn.
        self.__measurement.generate_tof_in(no_foil=no_foil)
        return gf.calculate_spectrum(self.__tof_listed_files,
                                     self.__spectrum_width,
                                     self.__measurement,
                                     self.__directory_es,
                                     no_foil=no_foil)

    def __load_cuts(self, no_foil=False, progress=None):
        """Loads cut files through tof_list into list.

        Args:
            no_foil: whether foil thickness is set to 0 when running tof_list
            progress: ProgressReporter object

        Return:
            Returns list of cut files' tof_list results.
        """
        try:
            cut_dict = {}
            save_output = self.__global_settings.is_es_output_saved()
            count = len(self.__cut_files)
            dirtyinteger = 0
            
            if not os.path.exists(self.__directory_es):
                os.makedirs(self.__directory_es)
            
            for cut_file in self.__cut_files:
                filename_split = os.path.basename(cut_file).split('.')
                element = Element.from_string(filename_split[1])
                if len(filename_split) == 5:  # Regular cut file
                    key = "{0}.{1}.{2}".format(element,
                                               filename_split[2],
                                               filename_split[3])
                else:  # Elemental Losses cut file
                    key = "{0}.{1}.{2}.{3}".format(element,
                                                   filename_split[2],
                                                   filename_split[3],
                                                   filename_split[4])
                cut_dict[key] = gf.tof_list(cut_file,
                                            self.__directory_es,
                                            save_output=save_output,
                                            no_foil=no_foil)
    
                dirtyinteger += 1
                if progress is not None:
                    progress.report((dirtyinteger / count) * 100)
        except:
            import traceback
            msg = "Could not calculate Energy Spectrum. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[0].__name__ + ": " +
                                 traceback._some_str(sys.exc_info()[1]),
                                 err_file,
                                str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.__measurement.name).error(msg)
        return cut_dict
