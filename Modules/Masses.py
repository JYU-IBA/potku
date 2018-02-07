# coding=utf-8
'''
Created on 20.3.2013
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

Reads data of the elements isotopes from masses.dat
'''
__author__ = "Jarkko Aalto \n Timo Konu \n Samuli Kärkkäinen \n Samuli Rahkonen \n Miika Raunio"
__versio__ = "1.0"

import csv

class Masses:
    '''Masses class handles all element isotopes' masses.
    '''
    def __init__(self, filepath):
        '''Inits Masses object
        
        Args:
            filepath: String representing filepath to masses.dat
        '''
        self.isotopes = {}   

        for data in self.__import_text(filepath, ' '):
            if data[3] not in self.isotopes:
                self.isotopes[data[3]] = []
            self.isotopes[data[3]].append((data[2], data[5]))

    
    def load_isotopes(self, element, combobox, current_isotope=None):
        '''Load isotopes into given combobox.
        
        Args:
            element: String representing selected element of which 
                        isotopes are loaded.
            combobox: QComboBox to which items are added.
            current_isotope: Current isotope to select it on combobox by default 
                             (string).
        '''
        if element == None:
            return
        combobox.clear() 
        # Sort isotopes based on their commonness
        isotopes = sorted(self.__get_isotopes(element),
                          key=lambda isotope: isotope[1],
                          reverse=True)
        dirtyinteger = 0
        for isotope, tn in isotopes:
            # We don't need rare isotopes to be shown
            if float(tn) > 0.0:
                combobox.addItem(isotope) 
                if isotope == current_isotope:
                    combobox.setCurrentIndex(dirtyinteger) 
            dirtyinteger += 1
    
    
    def get_standard_isotope(self, element):
        '''Calculate standard element weight.
        
        Args:
            element: String representing element.
            
        Return:
            Returns standard weight of given element (float).
        '''
        standard = 0.0
        for isotope in self.__get_isotopes(element):
            # Has to have float() on both, else we crash.
            standard += float(isotope[0]) * float(isotope[1])
        return standard / 100.0
     
     
    def get_most_common_isotope(self, element):
        '''Get the most common isotope for an element.
        
        Args:
            element: String representing element.
            
        Return:
            Returns the most common isotope for the element (int)
            and the propability (commonness) of the isotope (float)
            as a tuple(int, float).
        '''
        isotopes = sorted(self.__get_isotopes(element),
                          key=lambda isotope: isotope[1],
                          reverse=True)
        return int(isotopes[0][0]), float(isotopes[0][1]) 
    
    
    def __get_isotopes(self, element):
        '''Get isotopes of given element.
        
        Return:
            Returns a list of element's isotopes.
        '''
        try:
            isotopes = self.isotopes[element]
        except:
            isotopes = []
        return isotopes
    
    
    def __import_text(self, filename, separator):
        '''Import test from masses.dat
        
        Args:
            filename: String representing full filepath to file which includes 
                      masses.
            separator: String representing separator for columns in the file.
            
        Returns:
            Yields one line in the file.
        '''
        for line in csv.reader(open(filename),
                               delimiter=separator,
                               skipinitialspace=True):
            if line:  # skips empty lines
                yield line

    

    
