# coding=utf-8
"""
Created on 21.4.2013
Updated on 9.4.2018

Potku is a graphical user interface for analyzation and 
visualization of measurement data collected from a ToF-ERD 
telescope. For physics calculations Potku uses external 
analyzation components.  
Copyright (C) Jarkko Aalto, Timo Konu, Samuli Kärkkäinen, Samuli Rahkonen and 
Miika Raunio

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
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio \n" \
             "Severi Jääskeläinen \n Samuel Kaiponen \n Heta Rekilä \n Sinikka Siironen"
__version__ = "2.0"

import logging
import os
import sys
import numpy
from PyQt5 import QtCore

from modules.element import Element
from modules.general_functions import hist, tof_list
from modules.null import Null


class EnergySpectrum:
    """ Class for energy spectrum.
    """
    def __init__(self, measurement, cut_files, spectrum_width, progress_bar=Null()):
        """Inits energy spectrum
        
        Args:
            measurement: A Measurement class object for which Energy Spectrum
                         is made.
            cut_files: String list of cut files.
            spectrum_width: Float representing energy spectrum graph width.
            progress_bar: QtWidgets.QProgressBar for GUI (Null class object otherwise).
        """
        self.__measurement = measurement
        self.__global_settings = self.__measurement.request.global_settings
        self.__cut_files = cut_files
        self.__spectrum_width = spectrum_width
        self.__progress_bar = progress_bar
        self.__directory_es = measurement.directory_energy_spectra
        # tof_list files here just in case progress bar might happen to 'disappear'.
        self.__tof_listed_files = self.__load_cuts()

    def calculate_spectrum(self):
        """Calculate energy spectrum data from cut files.
        
        Returns list of cut files 
        """
        histed_files = {}
        keys = self.__tof_listed_files.keys()
        for key in keys:
            histed_files[key] = hist(self.__tof_listed_files[key],
                                     self.__spectrum_width, 3)
            if not histed_files[key]:
                return {}
            first_val = (histed_files[key][0][0] - self.__spectrum_width, 0)
            last_val = (histed_files[key][-1][0] + self.__spectrum_width, 0)
            histed_files[key].insert(0, first_val)
            histed_files[key].append(last_val)
        if self.__global_settings.is_es_output_saved():
            for key in keys:
                file = self.__measurement.measurement_file
                histed = histed_files[key]
                filename = os.path.join(self.__directory_es, "{0}.{1}.hist".format(os.path.splitext(file)[0], key))
                numpy_array = numpy.array(histed,
                                          dtype=[('float', float), ('int', int)])
                numpy.savetxt(filename, numpy_array, delimiter=" ", fmt="%5.5f %6d")
        return histed_files

    def __load_cuts(self):
        """Loads cut files through tof_list into list.
        
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
                if len(filename_split) == 4:  # Regular cut file
                    key = "{0}.{1}".format(element, filename_split[2])
                else:  # Elemental Losses cut file
                    key = "{0}.{1}.{2}".format(element, filename_split[2],
                                               filename_split[3])
                cut_dict[key] = tof_list(cut_file, self.__directory_es, save_output)
    
                dirtyinteger += 1
                self.__progress_bar.setValue((dirtyinteger / count) * 100)
                QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents)
                # Mac requires event processing to show progress bar and its
                # process.
        except:
            import traceback
            msg = "Could not calculate Energy Spectrum. "
            err_file = sys.exc_info()[2].tb_frame.f_code.co_filename
            str_err = ", ".join([sys.exc_info()[0].__name__ + ": " + traceback._some_str(sys.exc_info()[1]), err_file,
                                str(sys.exc_info()[2].tb_lineno)])
            msg += str_err
            logging.getLogger(self.__measurement.measurement_name).error(msg)
        return cut_dict
