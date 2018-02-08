# coding=utf-8
'''
Created on 21.4.2013
Updated on 23.5.2013

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
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import os

from Modules.Element import Element
from Modules.Functions import hist
from Modules.Functions import tof_list
from Modules.Null import Null


class EnergySpectrum:
    '''
    '''
    def __init__(self, cut_files, spectrum_width, progress_bar=Null()):
        '''Inits energy spectrum
        
        Args:
            cut_files: String list of cut files.
            spectrum_width: Float representing energy spectrum graph width.
            progress_bar: QtGui.QProgressBar for GUI (Null class object otherwise).
        '''
        self.cut_files = cut_files
        self.spectrum_width = spectrum_width
        self.progress_bar = progress_bar
        # tof_list files here just in case progress bar might happen to 'disappear'.
        self.tof_listed_files = self.__load_cuts()
        
    
    def calculate_spectrum(self):
        '''Calculate energy spectrum data from cut files.
        
        Returns list of cut files 
        '''
        histed_files = {}
        keys = self.tof_listed_files.keys()
        for key in keys:
            histed_files[key] = hist(self.tof_listed_files[key],
                                     self.spectrum_width, 3)
        return histed_files
        
        
    def __load_cuts(self):
        '''Loads cut files through tof_list into list.
        
        Return:
            Returns list of cut files' tof_list results.
        '''
        cut_dict = {}

        count = len(self.cut_files)
        dirtyinteger = 0
        for cut_file in self.cut_files:
            filename_split = os.path.basename(cut_file).split('.')
            element = Element(filename_split[1])
            if len(filename_split) == 4:  # Regular cut file
                key = "{0}.{1}".format(element, filename_split[2])
            else:  # Elemental Losses cut file
                key = "{0}.{1}.{2}".format(element, filename_split[2],
                                           filename_split[3])
            cut_dict[key] = tof_list(cut_file)

            dirtyinteger += 1
            self.progress_bar.setValue((dirtyinteger / count) * 100)
        return cut_dict
    
    
    
    
